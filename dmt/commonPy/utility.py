# (C) Semantix Information Technologies.
#
# Semantix Information Technologies is licensing the code of the
# Data Modelling Tools (DMT) in the following dual-license mode:
#
# Commercial Developer License:
#       The DMT Commercial Developer License is the appropriate version
# to use for the development of proprietary and/or commercial software.
# This version is for developers/companies who do not want to share
# the source code they develop with others or otherwise comply with the
# terms of the GNU Lesser General Public License version 3.
#
# GNU LGPL v. 2.1:
#       This version of DMT is the one to use for the development of
# non-commercial applications, when you are willing to comply
# with the terms of the GNU Lesser General Public License version 3.
#
# The features of the two licenses are summarized below:
#
#                       Commercial
#                       Developer               LGPL
#                       License
#
# License cost          License fee charged     No license fee
#
# Must provide source
# code changes to DMT   No, modifications can   Yes, all source code
#                       be closed               must be provided back
#
# Can create            Yes, that is,           No, applications are subject
# proprietary           no source code needs    to the LGPL and all source code
# applications          to be disclosed         must be made available
#
# Support               Yes, 12 months of       No, but available separately
#                       premium technical       for purchase
#                       support
#
# Charge for Runtimes   None                    None
#
import sys
import os
import re
import platform
import traceback

from typing import Dict, Union, Match, Any  # NOQA pylint: disable=unused-import
from mypy_extensions import NoReturn  # NOQA pylint: disable=unused-import

from . import configMT


def inform(fmt: str, *args: Any) -> None:
    if configMT.verbose:
        print(fmt % args)


def warn(fmt: str, *args: Any) -> None:
    sys.stderr.write(("WARNING: " + fmt) % args)
    sys.stderr.write("\n")


def panic(x: str) -> NoReturn:
    if not x.endswith("\n"):
        x += "\n"
    sys.stderr.write("\n" + chr(27) + "[32m" + x + chr(27) + "[0m\n")
    sys.exit(1)


def panicWithCallStack(msg: str) -> NoReturn:
    if configMT.verbose:
        sys.stderr.write("\n" + chr(27) + "[32m" + msg + chr(27) + "[0m\n")
        sys.stderr.write(
            "\nCall stack was:\n%s\n" % "".join(traceback.format_stack()))
        sys.exit(1)
    else:
        panic(msg)


def lcfirst(word: str) -> str:
    if word:
        return word[:1].lower() + word[1:]
    else:
        return word


def ucfirst(word: str) -> str:
    if word:
        return word[:1].upper() + word[1:]
    else:
        return word


def collapseCAPSgroups(word: str) -> str:
    while 1:
        m = re.match('^(.*?)([A-Z][A-Z]+)(.*?)$', word)
        if m:
            word = m.group(1) + lcfirst(m.group(2)) + m.group(3)
        else:
            break
    return word


def readContexts(tapNumbers: str) -> Dict[str, str]:
    data = {}
    for line in open(tapNumbers, "r").readlines():
        line = line.rstrip(os.linesep)
        lista = line.split(":")
        data[lista[0]] = lista[1]
    return data


def mysystem(cmd: str) -> int:
    p = platform.system()
    if p == "Windows" or p.startswith("CYGWIN"):
        return os.system('"' + cmd + '"')
    else:
        return os.system(cmd)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
