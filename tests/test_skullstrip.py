import unittest

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
        # TODO set unet to linear execution
        self._wfs[2][0].linear = True

    def test_result(self):
        for wf, config in self._wfs[2:3]:
            self.assertTrue(wf.run(config))


if __name__ == '__main__':
    unittest.main()
