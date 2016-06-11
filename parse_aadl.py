#!/usr/bin/env python2
# vim: set expandtab ts=8 sts=4 shiftwidth=4
#
# (C) Semantix Information Technologies.
#
# Semantix Information Technologies is licensing the code of the
# Data Modelling Tools (DMT) in the following dual-license mode:
#
# Commercial Developer License:
#       The DMT Commercial Developer License is the suggested version
# to use for the development of proprietary and/or commercial software.
# This version is for developers/companies who do not want to comply
# with the terms of the GNU Lesser General Public License version 2.1.
#
# GNU LGPL v. 2.1:
#       This version of DMT is the one to use for the development of
# applications, when you are willing to comply with the terms of the
# GNU Lesser General Public License version 2.1.
#
# Note that in both cases, there are no charges (royalties) for the
# generated code.
#
'''
AADLv2 parser
'''

import os
import sys

import commonPy2.aadlAST

#import aadlParser
from commonPy2 import AadlLexer
from commonPy2 import AadlParser

import antlr

from commonPy2.utility import panic, inform


def ParseAADLfilesAndResolveSignals():
    '''Invokes the ANTLR generated AADL parser, and resolves
all references to AAADL Data types into the param._signal member
of each SUBPROGRAM param.'''
    for aadlFilename in sys.argv[1:]:
        # Parse AADL system description files
        inform("Parsing %s...", aadlFilename)
        #aadlParser.ParseInput("\n".join(open(aadlFilename,'r').readlines()))

        L = AadlLexer.Lexer(aadlFilename)
        P = AadlParser.Parser(L)
        L.setFilename(aadlFilename)
        P.setFilename(L.getFilename())
        try:
            P.aadl_specification()
        except antlr.ANTLRException as e:  # pragma: no cover
            panic("Error in file '%s': %s\n" % (e.fileName, str(e)))

    # Resolve signal definitions over all input AADL files
    for subProgramName, subProgram in \
            commonPy2.aadlAST.g_apLevelContainers.items():
        inform(
            "Resolving data definitions in subprogram %s..." % subProgramName)
        for param in subProgram._params:
            if not isinstance(param._signal, commonPy2.aadlAST.Signal):
                if param._signal not in commonPy2.aadlAST.g_signals:
                    panic("Unknown data type %s in the definition of %s!\n" % (
                        param._signal, subProgramName))  # pragma: no cover
                param._signal = commonPy2.aadlAST.g_signals[param._signal]


def main():
    sys.path.append(os.path.abspath(os.path.dirname(sys.argv[0])))
    astFile = None
    if sys.argv.count("-o") != 0:
        idx = sys.argv.index("-o")
        try:
            astFile = os.path.abspath(sys.argv[idx + 1])
        except:  # pragma: no cover
            panic('Usage: %s -o astFile input1.aadl [input2.aadl] ...\n' % sys.argv[0])  # pragma: no cover
        del sys.argv[idx]
        del sys.argv[idx]
    if "-onlySP" in sys.argv:  # pragma: no cover
        commonPy2.configMT.g_bOnlySubprograms = True  # pragma: no cover
        sys.argv.remove("-onlySP")  # pragma: no cover
    if "-verbose" in sys.argv:
        commonPy2.configMT.verbose = True
        sys.argv.remove("-verbose")

    # No other options must remain in the cmd line...
    if astFile is None or len(sys.argv) < 2:
        panic('Usage: %s [-verbose] [-useOSS] [-o dirname] input1.aadl [input2.aadl] ...\n' % sys.argv[0])  # pragma: no cover
    commonPy2.configMT.showCode = True
    for f in sys.argv[1:]:
        if not os.path.isfile(f):
            panic("'%s' is not a file!\n" % f)  # pragma: no cover

    ParseAADLfilesAndResolveSignals()
    serialize_package = {
        'g_signals': commonPy2.aadlAST.g_signals,
        'g_apLevelContainers': commonPy2.aadlAST.g_apLevelContainers,
        'g_subProgramImplementations': commonPy2.aadlAST.g_subProgramImplementations,
        'g_processImplementations': commonPy2.aadlAST.g_processImplementations,
        'g_threadImplementations': commonPy2.aadlAST.g_threadImplementations,
        'g_systems': commonPy2.aadlAST.g_systems
    }
    import cPickle
    cPickle.dump(serialize_package, open(astFile, 'w'))

if __name__ == "__main__":
    if "-pdb" in sys.argv:
        sys.argv.remove("-pdb")  # pragma: no cover
        import pdb  # pragma: no cover
        pdb.run('main()')  # pragma: no cover
    else:
        main()
