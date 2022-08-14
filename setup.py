#!/usr/bin/env python3

from pathlib import Path
from typing import Dict
from setuptools import setup

readme = Path("README.md").read_text()
reqs = Path("requirements.txt").read_text()
package_name = "vsstats"

meta: Dict[str, str] = dict()
exec(Path(f'{package_name}/_metadata.py').read_text(), meta)

setup(
    name=package_name,
    version=meta['__version__'],
    author=meta['__author_name__'],
    author_email=meta['__author_email__'],
    maintainer=meta['__maintainer_name__'],
    maintainer_email=meta['__maintainer_email__'],
    description=meta['__doc__'],
    long_description=readme,
    long_description_content_type='text/markdown',
    project_urls={
        'Source Code': 'https://github.com/Irrational-Encoding-Wizardry/vs-scale',
        'Documentation': 'https://vsscale.encode.moe/en/latest/',
        'Contact': 'https://discord.gg/qxTxVJGtst',
    },
    install_requires=reqs,
    python_requires='>=3.10',
    packages=[
        package_name
    ],
    package_data={
        package_name: ['py.typed']
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ]
)
