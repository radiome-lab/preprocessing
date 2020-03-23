import tempfile

import torch
from nipype.interfaces import fsl, ants
from radiome.core import workflow, ResourcePool, Context, AttrDict
from radiome.core.jobs import PythonJob, NipypeJob
from radiome.core.resource_pool import R, Resource
from radiome.core.utils.s3 import S3Resource
from torch import nn

from .unet.function import predict_volumes
from .unet.model import UNet2d


# TODO don't work in Dask
@workflow()
def create_workflow(config: AttrDict, resource_pool: ResourcePool, context: Context):
    for _, rp in resource_pool[['label-initial_T1w']]:
        anat = rp[R('T1w', label='initial')]
        train_model = UNet2d(dim_in=config.dim_in, num_conv_block=config.num_conv_block, kernel_root=config.kernel_root)
        if config.unet_model.lower().startswith('s3://'):
            unet_path = S3Resource(config.unet_model, working_dir=tempfile.mkdtemp())()
        else:
            unet_path = config.unet_model
        checkpoint = torch.load(unet_path, map_location={'cuda:0': 'cpu'})
        train_model.load_state_dict(checkpoint['state_dict'])
        model = nn.Sequential(train_model, nn.Softmax2d())

        # create a node called unet_mask
        unet_mask = PythonJob(function=predict_volumes, reference='unet_mask')
        unet_mask.model = Resource(model)
        unet_mask.cimg_in = anat

        """
        Revised mask with ANTs
        """
        # fslmaths <whole head> -mul <mask> brain.nii.gz
        unet_masked_brain = NipypeJob(interface=fsl.MultiImageMaths(op_string="-mul %s"), reference='unet_masked_brain')
        unet_masked_brain.in_file = anat
        unet_masked_brain.operand_files = unet_mask.output_path

        # flirt -v -dof 6 -in brain.nii.gz -ref NMT_SS_0.5mm.nii.gz -o brain_rot2atl -omat brain_rot2atl.mat -interp sinc
        # TODO change it to ANTs linear transform
        native_brain_to_template_brain = NipypeJob(
            interface=fsl.FLIRT(reference=config.template_brain_only_for_anat, dof=6, interp='sinc'),
            reference='native_brain_to_template_brain')
        native_brain_to_template_brain.in_file = unet_masked_brain.out_file

        # flirt -in head.nii.gz -ref NMT_0.5mm.nii.gz -o head_rot2atl -applyxfm -init brain_rot2atl.mat
        # TODO change it to ANTs linear transform
        native_head_to_template_head = NipypeJob(
            interface=fsl.FLIRT(reference=config.template_skull_for_anat, apply_xfm=True),
            reference='native_head_to_template_head')
        native_head_to_template_head.in_file = anat
        native_head_to_template_head.in_matrix_file = native_brain_to_template_brain.out_matrix_file

        # fslmaths NMT_SS_0.5mm.nii.gz -bin templateMask.nii.gz
        template_brain_mask = NipypeJob(interface=fsl.maths.MathsCommand(args='-bin'), reference='template_brain_mask')
        template_brain_mask.in_file = config.template_brain_only_for_anat

        # ANTS 3 -m  CC[head_rot2atl.nii.gz,NMT_0.5mm.nii.gz,1,5] -t SyN[0.25] -r Gauss[3,0] -o atl2T1rot -i 60x50x20 --use-Histogram-Matching  --number-of-affine-iterations 10000x10000x10000x10000x10000 --MI-option 32x16000
        ants_template_head_to_template = NipypeJob(interface=ants.Registration(), reference='template_head_to_template')
        ants_template_head_to_template.metric = ['CC']
        ants_template_head_to_template.metric_weight = [1, 5]
        ants_template_head_to_template.moving_image = config.template_skull_for_anat
        ants_template_head_to_template.transforms = ['SyN']
        ants_template_head_to_template.transform_parameters = [(0.25,)]
        ants_template_head_to_template.interpolation = 'NearestNeighbor'
        ants_template_head_to_template.number_of_iterations = [[60, 50, 20]]
        ants_template_head_to_template.smoothing_sigmas = [[0.6, 0.2, 0.0]]
        ants_template_head_to_template.shrink_factors = [[4, 2, 1]]
        ants_template_head_to_template.convergence_threshold = [1.e-8]

        ants_template_head_to_template.fixed_image = native_head_to_template_head.out_file

        # antsApplyTransforms -d 3 -i templateMask.nii.gz -t atl2T1rotWarp.nii.gz atl2T1rotAffine.txt -r brain_rot2atl.nii.gz -o brain_rot2atl_mask.nii.gz
        template_head_transform_to_template = NipypeJob(interface=ants.ApplyTransforms(dimension=3),
                                                        reference='template_head_transform_to_template')
        template_head_transform_to_template.input_image = template_brain_mask.out_file
        template_head_transform_to_template.reference_image = native_brain_to_template_brain.out_file
        template_head_transform_to_template.transforms = ants_template_head_to_template.forward_transforms

        # convert_xfm -omat brain_rot2native.mat -inverse brain_rot2atl.mat 
        invt = NipypeJob(interface=fsl.ConvertXFM(invert_xfm=True), reference='convert_xfm')
        invt.in_file = native_brain_to_template_brain.out_matrix_file

        # flirt -in brain_rot2atl_mask.nii.gz -ref brain.nii.gz -o brain_mask.nii.gz -applyxfm -init brain_rot2native.mat
        template_brain_to_native_brain = NipypeJob(interface=fsl.FLIRT(apply_xfm=True),
                                                   reference='template_brain_to_native_brain')
        template_brain_to_native_brain.in_file = template_head_transform_to_template.output_image
        template_brain_to_native_brain.reference = unet_masked_brain.out_file
        template_brain_to_native_brain.in_matrix_file = invt.out_file

        # fslmaths brain_mask.nii.gz -thr .5 -bin brain_mask_thr.nii.gz
        refined_mask = NipypeJob(interface=fsl.Threshold(thresh=0.5, args='-bin'), reference='refined_mask')
        refined_mask.in_file = template_brain_to_native_brain.out_file

        # get a new brain with mask
        refined_brain = NipypeJob(interface=fsl.MultiImageMaths(op_string="-mul %s"), reference='refined_brain')
        refined_brain.in_file = anat
        refined_brain.operand_files = refined_mask.out_file

        rp[R('T1w', label='skullstrip', suffix='mask')] = refined_mask.out_file
        rp[R('T1w', label='skullstrip', suffix='brain')] = refined_brain.out_file
