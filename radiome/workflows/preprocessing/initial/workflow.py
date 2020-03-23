from nipype.interfaces import afni
from nipype.interfaces import ants
from radiome.core import workflow, AttrDict, Context, ResourceKey as R, ResourcePool
from radiome.core.jobs import NipypeJob


@workflow()
def create_workflow(config: AttrDict, resource_pool: ResourcePool, context: Context):
    for _, rp in resource_pool[['T1w']]:
        anatomical_image = rp[R('T1w')]
        anat_deoblique = NipypeJob(
            interface=afni.Refit(deoblique=True),
            reference='deoblique'
        )
        anat_deoblique.in_file = anatomical_image
        output_node = anat_deoblique.out_file

        if config.non_local_means_filtering:
            denoise = NipypeJob(interface=ants.DenoiseImage(), reference='denoise')
            denoise.input_image = output_node
            output_node = denoise.output_image

        if config.n4_bias_field_correction:
            n4 = NipypeJob(interface=ants.N4BiasFieldCorrection(dimension=3, shrink_factor=2, copy_header=True),
                           reference='correction')
            n4.input_image = output_node
            output_node = n4.output_image

        anat_reorient = NipypeJob(
            interface=afni.Resample(orientation='RPI', outputtype='NIFTI_GZ'),
            reference='reorient'
        )
        anat_reorient.in_file = output_node
        rp[R('T1w', label='initial')] = anat_reorient.out_file
