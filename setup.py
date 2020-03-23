import os

from setuptools import setup, find_namespace_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

requirements = []
if os.path.exists('requirements.txt'):
    with open('requirements.txt') as req:
        requirements = list(filter(None, req.read().splitlines()))

setup(
    name="preprocessing",
    version="0.0.1",
    author="Pu Zhao",
    author_email="puzhao@utexas.edu",
    description="Radiome Preprocessing Workflows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=find_namespace_packages(include=['radiome.workflows.*']),
    package_data={
        'radiome.workflows.preprocessing.skullstrip.afni': ['spec.yml'],
        'radiome.workflows.preprocessing.skullstrip.fsl': ['spec.yml'],
        'radiome.workflows.preprocessing.skullstrip.unet': ['spec.yml'],
        'radiome.workflows.preprocessing.initial': ['spec.yml']
    },
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    include_package_data=True,
    zip_safe=False,
)
