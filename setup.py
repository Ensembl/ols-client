from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    README = f.read()

with open('VERSION', 'r', encoding='utf-8') as f:
    VERSION = f.read()


def import_requirements():
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        content = f.readlines()
        # you may also want to remove whitespace characters like `\n` at the end of each line
        content = [x.strip() for x in content]
        return content


setup(
    name='ebi-ols-client',
    version=VERSION,
    description='OLS - REST Api Client - python library',
    long_description=README,
    long_description_content_type='text/markdown',
    author='Marc Chakiachvili',
    author_email='mchakiachvili@ebi.ac.uk',
    url='https://github.com/Ensembl/ols-client',
    license='Apache 2.0',
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=import_requirements(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]
)
