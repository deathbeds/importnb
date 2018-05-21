import json
from pathlib import Path
import setuptools

name = "importnb"

__version__ = None

here = Path(__file__).parent

# This should be replaced with proper pathlib business

with (here/ 'src' / 'importnb'/ '_version.py').open('r') as file:
    exec(file.read())

with open(str(here/'readme.md'),'r') as f:
    description = f.read()
    
with open(str(here/'changelog.ipynb'), 'r') as f:
    description += '\n'+ '\n'.join(
        ''.join(cell['source']) for cell in json.load(f)['cells'] if cell['cell_type'] == 'markdown'
    )

import sys

setup_args = dict(
    name=name,
    version=__version__,
    author="deathbeds",
    author_email="tony.fast@gmail.com",
    description="Import .ipynb files as modules in the system path.",
    long_description=description,
    long_description_content_type='text/markdown',
    url="https://github.com/deathbeds/importnb",
    python_requires=">=3.4",
    license="BSD-3-Clause",
    setup_requires=[
        'pytest-runner',
        'twine>=1.11.0',
        'setuptools>=38.6.',
    ] + ([] if sys.version_info.minor == 4 else ['wheel>=0.31.0']),
    tests_require=['pytest', 'nbformat'],
    install_requires=[],
    include_package_data=True,
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=(
        "Development Status :: 4 - Beta",
        "Framework :: IPython",
        "Framework :: Jupyter",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: BSD License",
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',),
    zip_safe=False,
    extras_require={
        'watch': ['watchdog']
    },
    entry_points = {
        'pytest11': ['pytest-importnb = importnb.utils.pytest_plugin',],
        'console_scripts': [
            'importnb-install = importnb.utils.ipython:install',
            'importnb-uninstall = importnb.utils.ipython:uninstall',
            'nbdoctest = importnb.utils.nbdoctest:_test',
        ]
    },
)

if __name__ == "__main__":
    setuptools.setup(**setup_args)
