#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    This module contains the shared API for parsing ASN.1
"""
from . import configMT
from . import asnParser
from . import asnAST
from . import aadlAST
from . import utility
from . import createInternalTypes
from . import verify
from . import recursiveMapper
from . import cleanupNodes

__version__ = "2.0.0"

def print_version():
    print("TASTE Data Modelling Tools version {}\n\n"
          "The following tools are available:\n"
          "   asn2aadlPlus    - Convert ASN.1 models to AADL\n"
          "   asn2dataModel   - TASTE A Mappers (fron ASN.1 to C, Python, etc.)\n"
          "   aadl2glueC      - TASTE B Mappers\n"
          "   msgPrinter      - (See documentation)\n"
          "   msgPrinterASN1  - (See documentation)\n"
          "   smp2asn         - SMP2 to ASN.1 converter\n".format(__version__))
