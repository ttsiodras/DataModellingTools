#!/usr/bin/env python3
# vim: set expandtab ts=8 sts=4 shiftwidth=4
#
# (C) Semantix Information Technologies, Neuropublic, and European Space Agency
#
# Copyright 2014-2015 IB Krates <info@krates.ee>
#       QGenc code generator integration
#
# License is GPL with runtime exception
'''
Model Translator

This is one of the code generators that Semantix developed for
the European research project ASSERT. It is now enhanced in the
context of Data Modelling and Data Modelling Tuning projects.

It reads the ASN.1 specification of the exchanged messages, and
generates the semantically equivalent ModelingTool/ModelingLanguage
declarations (e.g. SCADE/Lustre, Matlab/Simulink statements, etc).
'''
import os
import sys
import copy

from typing import cast, Dict, Tuple, Any, List  # NOQA pylint: disable=unused-import

from .commonPy import configMT, asnParser, cleanupNodes, verify
from .commonPy.utility import inform, panic
from .commonPy.asnParser import Filename, Typename, AST_Lookup, AST_TypesOfFile, AST_Leaftypes  # NOQA pylint: disable=unused-import
from .commonPy.asnAST import AsnNode  # NOQA pylint: disable=unused-import

from . import A_mappers  # NOQA pylint:disable=unused-import

from .A_mappers import ada_A_mapper
from .A_mappers import c_A_mapper
from .A_mappers import og_A_mapper
from .A_mappers import python_A_mapper
from .A_mappers import qgenada_A_mapper
from .A_mappers import qgenc_A_mapper
from .A_mappers import rtds_A_mapper
from .A_mappers import scade6_A_mapper
from .A_mappers import simulink_A_mapper
from .A_mappers import smp2_A_mapper
from .A_mappers import sqlalchemy_A_mapper
from .A_mappers import sql_A_mapper
from .A_mappers import vdm_A_mapper

from .A_mappers.module_protos import A_Mapper


def usage(argsToTools: Dict[str, str]) -> None:
    '''Print usage instructions.'''
    msg = 'Usage: %s <options> input1.asn1 [input2.asn1]...\nWhere options are:\n'
    msg += '\t-verbose\t\tDisplay more debug output\n'
    msg += '\t-o dirname\t\tDirectory to place generated files\nAnd one of:\n'
    for opt in sorted(argsToTools.keys()):
        msg += '\t-' + opt + ' (for ' + argsToTools[opt][0].upper() + argsToTools[opt][1:] + ')\n'
    panic(msg % sys.argv[0])


def getBackend(modelingLanguage: str) -> A_Mapper:
    backends = {
        'OG': og_A_mapper,
        'SCADE5': scade6_A_mapper,
        'SCADE6': scade6_A_mapper,
        'Simulink': simulink_A_mapper,
        'C': c_A_mapper,
        'RTDS': rtds_A_mapper,
        'ada': ada_A_mapper,
        'python': python_A_mapper,
        'smp2': smp2_A_mapper,
        'qgenada': qgenada_A_mapper,
        'qgenc': qgenc_A_mapper,
        'sql': sql_A_mapper,
        'sqlalchemy': sqlalchemy_A_mapper,
        'vdm': vdm_A_mapper,
    }
    if modelingLanguage not in backends:
        panic("Modeling language '%s' not supported" % modelingLanguage)  # pragma: no cover
    return cast(A_Mapper, backends[modelingLanguage])


def main() -> None:
    if "-pdb" in sys.argv:
        sys.argv.remove("-pdb")  # pragma: no cover
        import pdb  # pragma: no cover pylint: disable=wrong-import-position,wrong-import-order
        pdb.set_trace()  # pragma: no cover

    use_ASN1SCC_allboards_support = "-allboards" in sys.argv
    if use_ASN1SCC_allboards_support:
        sys.argv.remove("-allboards")  # pragma: no cover
        extraFlags = os.getenv("ASN1SCC_FLAGS") or ""
        extraFlags += " --target allboards "
        os.putenv("ASN1SCC_FLAGS", extraFlags)


    if "-v" in sys.argv:
        import pkg_resources  # pragma: no cover
        version = pkg_resources.require("dmt")[0].version  # pragma: no cover
        print("asn2dataModel v" + str(version))  # pragma: no cover
        sys.exit(1)  # pragma: no cover

    argsToTools = {
        'toOG': 'OG',
        'toSCADE5': 'SCADE5',
        'toSCADE6': 'SCADE6',
        'toSIMULINK': 'Simulink',
        'toC': 'C',
        'toCPP': 'C',
        'toRTDS': 'RTDS',
        'toAda': 'ada',
        'toPython': 'python',
        'toSMP2': 'smp2',
        'toQGenAda': 'qgenada',
        'toQGenC': 'qgenc',
        'toSQL': 'sql',
        'toSqlalchemy': 'sqlalchemy'
    }
    for i in os.listdir(os.path.dirname(os.path.abspath(A_mappers.__file__))):
        if '_A_mapper' in i and i.endswith('.py'):
            target = i.split('_')[0]
            if target.lower() not in [x.lower() for x in argsToTools.values()]:
                argsToTools['to' + target.capitalize()] = target  # pragma: no cover

    toolSelected = {}
    for i in argsToTools:
        toolSelected[i] = False

    if sys.argv.count("-o") != 0:
        idx = sys.argv.index("-o")
        try:
            configMT.outputDir = os.path.normpath(sys.argv[idx + 1]) + os.sep
        except:   # pragma: no cover
            usage(argsToTools)  # pragma: no cover
        del sys.argv[idx]
        del sys.argv[idx]
        if not os.path.isdir(configMT.outputDir):
            panic("'%s' is not a directory!\n" % configMT.outputDir)  # pragma: no cover
    if "-verbose" in sys.argv:
        configMT.verbose = True
        sys.argv.remove("-verbose")
    for i in argsToTools:
        if "-" + i in sys.argv:
            toolSelected[i] = True
            sys.argv.remove("-" + i)

    if len(sys.argv) < 2:
        usage(argsToTools)

    # One of the tools must be selected!
    if not any(toolSelected[i] for i in argsToTools):
        usage(argsToTools)  # pragma: no cover

    for f in sys.argv[1:]:
        if not os.path.isfile(f):
            panic("'%s' is not a file!\n" % f)  # pragma: no cover

    uniqueFilenames = list(set(sys.argv[1:]))
    asnParser.ParseAsnFileList(uniqueFilenames)

    uniqueASNfiles = {}  # type: Dict[Filename, Tuple[AST_Lookup, List[AsnNode], AST_Leaftypes]]
    for asnFile in uniqueFilenames:
        tmpNames = {}  # type: AST_Lookup
        for name in asnParser.g_typesOfFile[asnFile]:
            tmpNames[name] = asnParser.g_names[name]

        uniqueASNfiles[asnFile] = (
            copy.copy(tmpNames),                            # map Typename to type definition class from asnAST
            copy.copy(asnParser.g_astOfFile[asnFile]),    # list of nameless type definitions
            copy.copy(asnParser.g_leafTypeDict))   # map from Typename to leafType

        inform("Checking that all base nodes have mandatory ranges set in %s..." % asnFile)
        for node in list(tmpNames.values()):
            verify.VerifyRanges(node, asnParser.g_names)

    if configMT.debugParser:
        sys.exit(0)  # pragma: no cover

    # If some AST nodes must be skipped (for any reason), go learn about them
    badTypes = cleanupNodes.DiscoverBadTypes()

    # For each ASN.1 grammar file referenced in the system level description
    for arg, modelingLanguage in argsToTools.items():
        if not toolSelected[arg]:
            continue
        backend = getBackend(modelingLanguage)

        # For some languages we want to pass the complete list of ASN.1 files to ASN1SCC,
        # instead of working per type:
        if modelingLanguage.lower() in ["c", "ada", "smp2", "qgenc", "qgenada"]:
            backend.OnStartup(modelingLanguage, list(uniqueASNfiles.keys()), configMT.outputDir, badTypes)
            backend.OnShutdown(badTypes)
            continue  # bug in coverage.py...  # pragma: no cover

        # Work on each ASN.1 file's types
        for asnFile in uniqueASNfiles:
            if 'OnStartup' in dir(backend):
                backend.OnStartup(modelingLanguage, asnFile, configMT.outputDir, badTypes)

            leafTypeDict = uniqueASNfiles[asnFile][2]

            inform("Executing mappings for types inside %s...", asnFile)
            names = uniqueASNfiles[asnFile][0]
            for nodeTypename in sorted(names):
                # Check if this type must be skipped
                if nodeTypename in badTypes and modelingLanguage.lower() != 'python':
                    # all languages but python discard IA5Strings
                    continue
                node = names[nodeTypename]
                inform("Processing %s (%s)...", nodeTypename, modelingLanguage)

                # First, make sure we know what leaf type this node is
                assert nodeTypename in leafTypeDict

                leafType = leafTypeDict[nodeTypename]
                if leafType in ['BOOLEAN', 'INTEGER', 'REAL', 'OCTET STRING', 'AsciiString']:
                    processor = backend.OnBasic
                elif leafType == 'SEQUENCE':
                    processor = backend.OnSequence
                elif leafType == 'SET':
                    processor = backend.OnSet  # pragma: no cover
                elif leafType == 'CHOICE':
                    processor = backend.OnChoice
                elif leafType == 'SEQUENCEOF':
                    processor = backend.OnSequenceOf
                elif leafType == 'SETOF':
                    processor = backend.OnSetOf  # pragma: no cover
                elif leafType == 'ENUMERATED':
                    processor = backend.OnEnumerated
                else:  # pragma: no cover
                    panic("Unexpected type of element: %s" % leafType)  # pragma: no cover
                processor(nodeTypename, node, leafTypeDict)

            if 'OnShutdown' in dir(backend):
                backend.OnShutdown(badTypes)


if __name__ == "__main__":
    main()
