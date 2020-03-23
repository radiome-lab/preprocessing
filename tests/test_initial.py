import os
import unittest
import nibabel as nib
from radiome.core.resource_pool import R
from radiome.core.utils.mocks import WorkflowDriver
from .utils import test_data_dir, entry_dir


class TestCase(unittest.TestCase):
    def setUp(self):
        self._wf = WorkflowDriver(entry_dir('initial'),
                                  test_data_dir('images/initial'))

    def test_result(self):
        res_rp = self._wf.run(config={'non_local_means_filtering': False,
                                      'n4_bias_field_correction': False})
        for _, rp in res_rp[['label-initial_T1w']]:
            anat_image = rp[R('T1w', label='initial')]()
            anat_reorient_sform = nib.load(anat_image).get_sform()

            for i in range(0, 4):
                for j in range(0, 4):
                    if i == j:
                        if i == 0:
                            self.assertLess(anat_reorient_sform[i][i], 0)
                        else:
                            self.assertGreater(anat_reorient_sform[i][i], 0)
                    else:
                        if not (j == 3):
                            self.assertEqual(anat_reorient_sform[i][j], 0)


if __name__ == '__main__':
    unittest.main()
