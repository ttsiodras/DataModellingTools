#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Setup file for Linux distribution of the Data Modelling Toolchain (DMT).

Usage:  python setup.py sdist   --> to create a tarball
        python setup.py install --> to install in python directory
'''

from setuptools import setup, find_packages

from dmt import (
    commonPy, asn2dataModel, A_mappers, B_mappers,
    aadl2glueC, msgPrinter, msgPrinterASN1)

setup(
    name='dmt',
    version=commonPy.__version__,
    packages=find_packages(),
    data_files=[
        ('dmt-utils', [
            'dmt/utils/learn_CHOICE_enums.py',
            'dmt/utils/parse_aadl.py',
            'dmt/utils/asn2aadlPlus.py']),
    ],
    author='Thanassis Tsiodras',
    author_email='Thanassis.Tsiodras@esa.int',
    description='TASTE Data Modelling Technologies based on ASN.1',
    long_description=open('README.md').read(),
    install_requires=[],
    include_package_data=True,
    url='http://taste.tuxfamily.org',
    classifiers=[
        'Programming Language :: Python',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5'
    ],
    entry_points={
        'console_scripts': [
            # 'asn2aadlPlus = asn2aadlPlus:main',
            'asn2dataModel = dmt.asn2dataModel:main',
            'aadl2glueC = dmt.aadl2glueC:main',
            'msgPrinter = dmt.msgPrinter:main',
            'msgPrinterASN1 = dmt.msgPrinterASN1:main',
            'dmt = dmt.commonPy:print_version'
        ]
    }
)
