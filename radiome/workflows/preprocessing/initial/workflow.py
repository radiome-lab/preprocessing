from nipype.interfaces import afni
from nipype.interfaces import ants

from radiome.core.execution.nipype import NipypeJob
from radiome.core.pipeline import Context
from radiome.core.resource_pool import ResourcePool, ResourceKey as R
from radiome.core.schema import validate_inputs


def create_workflow(configuration: dict, resource_pool: ResourcePool, context: Context):
    validate_inputs(__file__, configuration)
    for _, rp in resource_pool[['T1w']]:
        anatomical_image = rp[R('T1w')]

        anat_deoblique = NipypeJob(
            interface=afni.Refit(deoblique=True),
            reference='deoblique'
        )
        anat_deoblique.in_file = anatomical_image
        output_node = anat_deoblique.out_file

        if configuration['non_local_means_filtering']:
            denoise = NipypeJob(interface=ants.DenoiseImage(), reference='denoise')
            denoise.input_image = output_node
            output_node = denoise.output_image

        if configuration['n4_bias_field_correction']:
            n4 = NipypeJob(interface=ants.N4BiasFieldCorrection(dimension=3, shrink_factor=2, copy_header=True),
                           reference='correction')
            n4.input_image = output_node
            output_node = n4.output_image

        anat_reorient = NipypeJob(
            interface=afni.Resample(orientation='RPI', outputtype='NIFTI_GZ'),
            reference='reorient'
        )
        anat_reorient.in_file = output_node
        rp[R('T1w', label='initial')] = anat_reorient.out_file % 'initial'
