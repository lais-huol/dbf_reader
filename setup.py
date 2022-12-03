import sys
from setuptools import setup


version = '0.1.7'

config = {
    "name": 'dbf_reader',
    "description": 'Utils classes to read DBF files, specially DATASUS compressed DBF files',
    "long_description": 'Utils classes to read DBF files, specially DATASUS compressed DBF files, that a distributed without compliance with the specification',
    "license": 'MIT',
    "author": 'Kelson da Costa Medeiros',
    "author_email": 'kelson.medeiros@lais.huol.ufrn.br',
    "packages": ['dbf_reader'],
    "include_package_data": True,
    "version": version,
    "download_url": f"https://github.com/lais-huol/dbf_reader/releases/tag/{version}",
    "url": 'https://github.com/lais-huol/dbf_reader',
    "keywords": ['DBF', 'DBC', 'reader', 'datasus', ],
    "classifiers": [
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ]
}

if len(sys.argv) >= 3 and sys.argv[1] == 'validate_tag':
    if sys.argv[2] != version:
        raise Exception(f"A versão TAG [{sys.argv[2]}] é diferente da versão no arquivo setup.py [{version}].")
    exit()

setup(**config)
