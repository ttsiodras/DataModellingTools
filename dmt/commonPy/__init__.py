#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module contains the shared API for parsing ASN.1 and AADL
and performing code generation via AST traversals.
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

import pkg_resources  # pragma: no cover
__version__ = pkg_resources.require("dmt")[0].version  # pragma: no cover


def print_version() -> None:
    print("TASTE Data Modelling Tools version {}\n\n"
          "The following tools are available:\n"
          "   asn2aadlPlus    - Convert ASN.1 models to AADL\n"
          "   asn2dataModel   - TASTE A Mappers (from ASN.1 to C, Python, etc.)\n"
          "   aadl2glueC      - TASTE B Mappers (from ASN.1+AADL to glue code)\n"
          "   msgPrinter      - Generate serializers of ASN.1 instances\n"
          "   msgPrinterASN1  - Generate serializers of ASN.1 instances (other encodings)\n"
          "   smp2asn         - SMP2 to ASN.1 converter\n".format(__version__))
