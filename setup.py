import re

from setuptools import setup


def get_install_requires():
    """
    parse requirements.txt, ignore links, exclude comments
    """
    requirements = []
    for line in open('requirements.txt').readlines():
        # skip to next iteration if comment or empty line
        if line.startswith('#') or line == '' or line.startswith('http') or line.startswith('git'):
            continue
        # add line to requirements
        requirements.append(line.replace('\n', ''))
    return requirements


with open("sentinel2_downloader/__init__.py", encoding="utf-8") as f:
    version = re.search(r'__version__\s*=\s*"(\S+)"', f.read()).group(1)

with open('README.rst', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='sentinel2_downloader',
    packages=['sentinel2_downloader'],
    version=version,
    description='Utility for searching and downloading satellite images Dataspace Copernicus',
    long_description=long_description,
    include_package_data=True,
    author='Azimkozho Kenzhebek uulu',
    author_email='azimkozho.inventor@gmail.com',
    url='https://github.com/Azim-Kenzh/sentinel2_downloader',
    zip_safe=False,
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Utilities",
    ],
    keywords="copernicus, sentinel, satellite, download, GIS",
    install_requires=get_install_requires(),
)
