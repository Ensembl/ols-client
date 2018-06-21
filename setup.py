# -*- coding: utf-8 -*-

# Learn more: https://github.com/Ensembl/ols-client
import os

from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

def import_requirements():
    with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as f:
        content = f.readlines()
        # you may also want to remove whitespace characters like `\n` at the end of each line
        content = [x.strip() for x in content]
        return content

setup(
    name='ontology-client',
    version='0.0.1',
    description='OLS - REST Api Client - python library',
    long_description=readme,
    author='Marc Chakiachvili',
    author_email='mchakiachvili@ebi.ac.uk',
    url='https://github.com/Ensembl/ontology-client',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=import_requirements(),
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]
)

