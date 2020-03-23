from nipype.interfaces import fsl, afni
from radiome.core import Context, AttrDict, workflow
from radiome.core import ResourcePool, ResourceKey as R
from radiome.core.jobs import NipypeJob


@workflow()
def create_workflow(config: AttrDict, resource_pool: ResourcePool, context: Context):
    for _, rp in resource_pool[['label-initial_T1w']]:
        anat = rp[R('T1w', label='initial')]
        anat_skullstrip = NipypeJob(
            interface=fsl.BET(output_type='NIFTI_GZ', **config),
            reference='anat_skullstrip'
        )
        anat_skullstrip.in_file = anat
        anat_skullstrip_orig_vol = NipypeJob(interface=afni.Calc(expr='a*step(b)', outputtype='NIFTI_GZ'),
                                             reference='anat_skullstrip_orig_vol')
        anat_skullstrip_orig_vol.in_file_a = anat
        anat_skullstrip_orig_vol.in_file_b = anat_skullstrip.out_file

        rp[R('T1w', label='skullstrip', suffix='mask')] = anat_skullstrip.mask_file
        rp[R('T1w', label='skullstrip', suffix='brain')] = anat_skullstrip_orig_vol.out_file
