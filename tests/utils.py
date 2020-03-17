import os


def test_data_dir(destination):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', destination)


def entry_dir(destination):
    return os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, 'radiome', 'workflows', 'preprocessing',
                     destination))
