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

from typing import Dict

from . import configMT


def inform(fmt: str, *args) -> None:
    if configMT.verbose:
        print(fmt % args)


def warn(fmt: str, *args) -> None:
    sys.stderr.write(("WARNING: " + fmt) % args)
    sys.stderr.write("\n")


def panic(x: str) -> None:
    if not x.endswith("\n"):
        x += "\n"
    sys.stderr.write("\n" + chr(27) + "[32m" + x + chr(27) + "[0m\n")
    sys.exit(1)


def panicWithCallStack(msg: str) -> None:
    if configMT.verbose:
        sys.stderr.write("\n" + chr(27) + "[32m" + msg + chr(27) + "[0m\n")
        sys.stderr.write(
            "\nCall stack was:\n%s\n" % "".join(traceback.format_stack()))
    else:
        panic(msg)


def lcfirst(word: str) -> str:
    if len(word):
        return word[:1].lower() + word[1:]
    else:
        return word


def ucfirst(word: str) -> str:
    if len(word):
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


class Matcher:
    def __init__(self, pattern, flags=0):
        self._pattern = re.compile(pattern, flags)
        self._lastOne = None
        self._match = None
        self._search = None

    def match(self, line):
        self._match = re.match(self._pattern, line)
        self._lastOne = 'Match'
        return self._match

    def search(self, line):
        self._search = re.search(self._pattern, line)
        self._lastOne = 'Search'
        return self._search

    def group(self, idx):
        if self._lastOne == 'Match':
            return self._match.group(idx)
        elif self._lastOne == 'Search':
            return self._search.group(idx)
        else:
            return panic(
                "Matcher group called with index "
                "%d before match/search!\n" % idx)

    def groups(self):
        if self._lastOne == 'Match':
            return self._match.groups()
        elif self._lastOne == 'Search':
            return self._search.groups()
        else:
            return panic("Matcher groups called with match/search!\n")


def mysystem(cmd):
    p = platform.system()
    if p == "Windows" or p.startswith("CYGWIN"):
        return os.system('"' + cmd + '"')
    else:
        return os.system(cmd)
