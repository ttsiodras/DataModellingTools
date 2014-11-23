#!/usr/bin/env python
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
import os
import sys
import copy

import commonPy.configMT
import commonPy.asnParser
import commonPy.aadlAST
from commonPy.utility import inform, panic
import commonPy.cleanupNodes

import commonPy.verify

__doc__ = '''\
Model Translator

This is one of the code generators that Semantix developed for
the European research project ASSERT. It is now enhanced in the
context of Data Modelling and Data Modelling Tuning projects.

It reads the ASN.1 specification of the exchanged messages, and
generates the semantically equivalent ModelingTool/ModelingLanguage
declarations (e.g. SCADE/Lustre, Matlab/Simulink statements, etc).
'''


def usage(argsToTools):
    '''Print usage instructions.'''
    msg = 'Usage: %s <options> input1.asn1 [input2.asn1]...\nWhere options are:\n'
    msg += '\t-verbose\t\tDisplay more debug output\n'
#    msg += '\t-lexonly\t\tPerform only lexical analysis\n'
#    msg += '\t-ignoreINTEGERranges\tDon\'t check INTEGERs for mandatory constraints\n'
#    msg += '\t-ignoreREALranges\tDon\'t check REALs for mandatory constraints\n'
    msg += '\t-o dirname\t\tDirectory to place generated files\nAnd one of:\n'
    for opt in sorted(argsToTools.iterkeys()):
        msg += '\t-' + opt + ' (for ' + argsToTools[opt][0].upper() + argsToTools[opt][1:] + ')\n'
    panic(msg % sys.argv[0])


def main():
    sys.path.append(os.path.abspath(os.path.dirname(sys.argv[0])))
    sys.path.append('commonPy')

    argsToTools = {
        'toOG': 'OG',
        'toSCADE5': 'SCADE5',
        'toSCADE6': 'SCADE6',
        'toSIMULINK': 'Simulink',
        'toC': 'C',
        'toRTDS': 'RTDS',
        'toAda': 'ada',
        'toPython': 'python',
        'toSMP2': 'smp2',
        'toSQL': 'sql'
    }
    for i in os.listdir(os.path.abspath(os.path.dirname(sys.argv[0]))):
        if '_A_mapper' in i and i.endswith('.py'):
            target = i.split('_')[0]
            if target.lower() not in [x.lower() for x in argsToTools.itervalues()]:
                argsToTools['to' + target.capitalize()] = target

    for i in argsToTools:
        locals()[i] = False

    if sys.argv.count("-o") != 0:
        idx = sys.argv.index("-o")
        try:
            commonPy.configMT.outputDir = os.path.normpath(sys.argv[idx+1]) + os.sep
        except:   # pragma: no cover
            usage(argsToTools)  # pragma: no cover
        del sys.argv[idx]
        del sys.argv[idx]
        if not os.path.isdir(commonPy.configMT.outputDir):
            panic("'%s' is not a directory!\n" % commonPy.configMT.outputDir)  # pragma: no cover
    if "-verbose" in sys.argv:
        commonPy.configMT.verbose = True
        sys.argv.remove("-verbose")
#    if "-lexonly" in sys.argv:
#       commonPy.configMT.debugParser = True
#       sys.argv.remove("-lexonly")
#    if "-ignoreINTEGERranges" in sys.argv:
#       commonPy.configMT.args.append("-ignoreINTEGERranges")
#       sys.argv.remove("-ignoreINTEGERranges")
#    if "-ignoreREALranges" in sys.argv:
#       commonPy.configMT.args.append("-ignoreREALranges")
#       sys.argv.remove("-ignoreREALranges")
    for i in argsToTools:
        if "-"+i in sys.argv:
            locals()[i] = True
            sys.argv.remove("-"+i)

    if len(sys.argv) < 2:
        usage(argsToTools)

    # One of the tools must be selected!
    if not reduce(lambda x, y: x or y, [locals()[i] for i in argsToTools]):
        usage(argsToTools)  # pragma: no cover

    for f in sys.argv[1:]:
        if not os.path.isfile(f):
            panic("'%s' is not a file!\n" % f)  # pragma: no cover

    uniqueASNfiles = {}
    for grammar in sys.argv[1:]:
        uniqueASNfiles[grammar]=1
    commonPy.asnParser.ParseAsnFileList(uniqueASNfiles.keys())

    for asnFile in uniqueASNfiles:
        tmpNames = {}
        for name in commonPy.asnParser.g_typesOfFile[asnFile]:
            tmpNames[name] = commonPy.asnParser.g_names[name]

        uniqueASNfiles[asnFile] = [
            copy.copy(tmpNames),                            # map Typename to type definition class from asnAST
            copy.copy(commonPy.asnParser.g_astOfFile[asnFile]),    # list of nameless type definitions
            copy.copy(commonPy.asnParser.g_leafTypeDict)]   # map from Typename to leafType

        inform("Checking that all base nodes have mandatory ranges set in %s..." % asnFile)
        for node in tmpNames.values():
            verify.VerifyRanges(node, commonPy.asnParser.g_names)

    if commonPy.configMT.debugParser:
        sys.exit(0)  # pragma: no cover

    loadedBackends = {}

    # If some AST nodes must be skipped (for any reason), go learn about them
    commonPy.cleanupNodes.DiscoverBadTypes()

    # For each ASN.1 grammar file referenced in the system level description
    for arg, modelingLanguage in argsToTools.iteritems():
        if locals()[arg]:
            backendFilename = modelingLanguage.lower() + "_A_mapper.py"
            inform("Parsing %s...", backendFilename)
            try:
                backend = __import__(backendFilename[:-3])
                if backendFilename[:-3] not in loadedBackends:
                    loadedBackends[backendFilename[:-3]] = 1
                    if commonPy.configMT.verbose:
                        backend.Version()
            except:  # pragma: no cover
                panic("Failed to load backend (%s)" % backendFilename)  # pragma: no cover

            # Esp. for C, we want to pass the complete list of ASN.1 files to ASN1SCC,
            # instead of working per type:
            if modelingLanguage.lower() in ["c", "ada", "smp2"]:
                if 'OnStartup' in dir(backend):
                    backend.OnStartup(modelingLanguage, uniqueASNfiles.keys(), commonPy.configMT.outputDir)
                if 'OnShutdown' in dir(backend):
                    backend.OnShutdown()
            else:
                # Work on each ASN.1 file's types
                for asnFile in uniqueASNfiles:
                    if 'OnStartup' in dir(backend):
                        backend.OnStartup(modelingLanguage, asnFile, commonPy.configMT.outputDir)

                    leafTypeDict = uniqueASNfiles[asnFile][2]

                    inform("Executing mappings for types inside %s...", asnFile)
                    names = uniqueASNfiles[asnFile][0]
                    for nodeTypename in names:
                        # Check if this type must be skipped
                        if commonPy.cleanupNodes.IsBadType(nodeTypename):
                            continue
                        node = names[nodeTypename]
                        inform("Processing %s (%s)...", nodeTypename, modelingLanguage)

                        # First, make sure we know what leaf type this node is
                        assert(nodeTypename in leafTypeDict)

                        leafType = leafTypeDict[nodeTypename]
                        # If it is a base type,
                        if leafType in ['BOOLEAN', 'INTEGER', 'REAL', 'OCTET STRING']:
                            # make sure we have mapping instructions for BASE elements
                            if 'OnBasic' not in dir(backend):
                                panic("ASN.1 grammar contains literal(%s) but no BASE section found in the mapping grammar (%s)" % (nodeTypename, sys.argv[2]))  # pragma: no cover
                            backend.OnBasic(nodeTypename, node, leafTypeDict)
                        # if it is a complex type
                        elif leafType in ['SEQUENCE', 'SET', 'CHOICE', 'SEQUENCEOF', 'SETOF', 'ENUMERATED']:
                            # make sure we have mapping instructions for the element
                            mappedName = {
                                'SEQUENCE': 'OnSequence',
                                'SET': 'OnSet',
                                'CHOICE': 'OnChoice',
                                'SEQUENCEOF': 'OnSequenceOf',
                                'SETOF': 'OnSetOf',
                                'ENUMERATED': 'OnEnumerated'
                            }
                            if mappedName[leafType] not in dir(backend):
                                panic("ASN.1 grammar contains %s but no %s section found in the mapping grammar (%s)" % (nodeTypename, mappedName[leafType], backendFilename))  # pragma: no cover
                            processor = backend.__dict__[mappedName[leafType]]
                            processor(nodeTypename, node, leafTypeDict)
                        # what type is it?
                        else:  # pragma: no cover
                            panic("Unexpected type of element: %s" % leafTypeDict[nodeTypename])  # pragma: no cover

                    if 'OnShutdown' in dir(backend):
                        backend.OnShutdown()

if __name__ == "__main__":
    if "-pdb" in sys.argv:
        sys.argv.remove("-pdb")  # pragma: no cover
        import pdb  # pragma: no cover
        pdb.run('main()')  # pragma: no cover
    else:
        main()
