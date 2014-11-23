#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Setup file for Linux distribution
Usage:  python setup.py sdist   --> to create a tarball
        python setup.py install --> to install in python directory
'''

from setuptools import setup, find_packages

import commonPy
import asn2aadlPlus
import asn2dataModel
import aadl2glueC

setup(
    name='dmt',
    version=commonPy.__version__,
    packages=find_packages(),
    author='Thanassis Tsiodras',
    author_email='ttsiodras@semantix.grt',
    description='TASTE Data Modelling Technologies based on ASN.1',
    long_description=open('README').read(),
    install_requires=[],
    include_package_data=True,
    url='http://taste.tuxfamily.org',
    classifiers=[
        'Programming Language :: Python',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7'
    ],
    entry_points={
        'console_scripts': [
            'asn2aadlPlus = asn2aadlPlus:main',
            'asn2dataModel = asn2dataModel:main',
            'aadl2glueC = aadl2glueC:main',
        ]
    }
)
