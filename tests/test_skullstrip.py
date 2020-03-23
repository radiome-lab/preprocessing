import unittest

import nibabel as nib
from radiome.core.resource_pool import R
from radiome.core.utils.mocks import WorkflowDriver

from .utils import test_data_dir, entry_dir


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self._wfs = [
            (WorkflowDriver(entry_dir('skullstrip/afni'), test_data_dir('images/skullstrip')), {
                'var_shrink_fac': True,
                'shrink_fac_bot_lim': 0.4,
                'avoid_vent': True,
                'pushout': True,
                'touchup': True,
                'fill_hole': 10,
                'avoid_eyes': True,
                'push_to_edge': False,
                'use_skull': False,
                'use_edge': True,
                'max_inter_iter': 4,
                'blur_fwhm': 0,
            }),
            (WorkflowDriver(entry_dir('skullstrip/fsl'), test_data_dir('images/skullstrip')), {}),
            (WorkflowDriver(entry_dir('skullstrip/unet'), test_data_dir('images/skullstrip')), {})
        ]

    def test_result(self):
        for wf, config in self._wfs:
            res_rp = wf.run(config)
            for _, rp in res_rp[['label-skullstrip_T1w']]:
                anat_image = rp[R('T1w', label='skullstrip')]()
                skullstrip_data = nib.load(anat_image).get_data()
                # known_brain_data = nib.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'template',
                #                                          'MNI152_T1_2mm_brain.nii.gz')).get_data()
                # bin_skullstrip = skullstrip_data.flatten()
                # bin_brain = known_brain_data.flatten()

                # correlation = np.corrcoef(bin_skullstrip, bin_brain)
                # self.assertGreaterEqual(correlation[0, 1], 0.95)


if __name__ == '__main__':
    unittest.main()
