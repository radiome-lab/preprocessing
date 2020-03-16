import os
import unittest
import numpy as np
import nibabel as nib
from radiome.core.resource_pool import R
from radiome.core.utils.mocks import WorkflowDriver


class MyTestCase(unittest.TestCase):
    def setUp(self):
        config = {
            'mask_vol': False,

            'shrink_factor': 0.6,

            'var_shrink_fac': True,

            'shrink_fac_bot_lim': 0.4,

            'avoid_vent': True,

            'niter': 250,

            'pushout': True,

            'touchup': True,

            'fill_hole': 10,

            'smooth_final': 20,

            'avoid_eyes': True,

            'use_edge': True,

            'exp_frac': 0.1,

            'push_to_edge': False,

            'use_skull': False,

            'perc_int': 0,

            'max_inter_iter': 4,

            'fac': 1,

            'blur_fwhm': 0,

            'monkey': False

        }
        self._wf = WorkflowDriver('radiome.workflows.preprocessing.afni.skullstrip',
                                  os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/images/skullstrip'),
                                  config=config)

    def test_result(self):
        res_rp = self._wf.run()

        for _, rp in res_rp[['label-skullstrip_T1w']]:
            anat_image = rp[R('T1w', label='skullstrip')]()
            skullstrip_data = nib.load(anat_image).get_data()
            known_brain_data = nib.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'template',
                                                     'MNI152_T1_2mm_brain.nii.gz')).get_data()
            bin_skullstrip = skullstrip_data.flatten()
            bin_brain = known_brain_data.flatten()

            # correlation = np.corrcoef(bin_skullstrip, bin_brain)
            # self.assertGreaterEqual(correlation[0, 1], 0.95)


if __name__ == '__main__':
    unittest.main()
