#!/usr/bin/env python3

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
SMP2 Catalogues datatypes importer

This tool parses SMP2 Catalogues, extracts the data types described in them,
and maps them to the corresponding ASN.1 data type declarations. It also
includes logic to merge these types to pre-existing data type declarations
of an ASN.1 file - thus allowing merging of SMP2 designs into TASTE designs
(datatype-wise).
'''
import os
import sys
import getopt

from .commonPy import asnParser
from .commonPy.createInternalTypes import ScanChildren
from .commonPy.asnAST import AsnMetaType
from .commonPy.commonSMP2 import (
    info, panic, green, white, red, setVerbosity,
    DashUnderscoreAgnosticDict, ConvertCatalogueToASN_AST)


def usage(coloredMsg=""):
    '''Prints help message and aborts. '''
    usageMsg = 'Usage: smp2asn <options> <smp2Catalogues...>\n\n' \
        'Where options must include:\n' \
        '  -o, --outAsn1=newAsnGrammar.asn  the output ASN.1 grammar, containing\n'\
        '                                   all the SMP2 types (if -a was used,\n'\
        '                                   the existing ASN.1 types, too)\n'\
        'Options may also include:\n'\
        '  -a, --asn1=asnGrammar.asn        an input ASN.1 grammar to merge with\n'\
        '  -p, --prune                      prune unnamed (inner) SMP2-translation types\n'\
        '  -v, --verbose                    Be more verbose (debugging)\n' \
        '  -h, --help                       Show this help message\n'
    panic(usageMsg, coloredMsg)


def MergeASN1_AST(smp2AsnAST):
    '''Merges the ASN.1 AST generated from SMP2 files (smp2AsnAST param)
    into the ASN.1 AST stored in asnParser.g_names. Uses smart
    merging, i.e. diff-like semantics.'''
    typesToAddVerbatim = []
    identicals = {}
    d = asnParser.g_names
    for k, v in smp2AsnAST.items():
        if k in d:
            # Type name exists in both trees - is it the same?
            if not v.IdenticalPerSMP2(d[k], smp2AsnAST, d):  # pragma: no cover
                panic(green + k + white + " exists, but is different:\n" +
                      "it is...\n" + d[k].AsASN1(d) + "\n" +
                      "but in SMP2 it is...\n" + v.AsASN1(smp2AsnAST))  # pragma: no cover
            else:  # pragma: no cover
                info(1, green, k, white, "exists and is semantically equivalent.")  # pragma: no cover
        else:
            # Find an identical type if possible
            for k2, v2 in d.items():
                if v2._isArtificial:
                    # Avoid mapping to artificially generated inner types
                    # (see last part of VerifyAndFixAST in asnParser)
                    continue
                if v2.IdenticalPerSMP2(v, d, smp2AsnAST):
                    info(1, green, k, white, "is identical to", red, k2, white)
                    identicals[k] = k2
                    break
            else:
                info(1, green, k, white, "must be copied (no equivalent type found)...")
                typesToAddVerbatim.append(k)
    # Merge missing types in asnParser.g_names
    for nodeTypename in typesToAddVerbatim:
        results = []
        node = smp2AsnAST[nodeTypename]
        # Take care to add dependencies first
        ScanChildren(nodeTypename, node, smp2AsnAST, results, isRoot=True, createInnerNodesInNames=False)
        info(1, "Will copy", nodeTypename, "(" + str(node.__class__) + ")", ("and " + str(results) if results else ''))
        results.append(nodeTypename)
        for r in results:
            node = smp2AsnAST[r]
            d[r] = node
            if isinstance(node, AsnMetaType):
                asnParser.g_metatypes[r] = r._containedType  # pragma: no cover
                d[r] = smp2AsnAST[r._containedType]  # pragma: no cover
            asnParser.g_typesOfFile.setdefault(node._asnFilename, []).append(r)
    return identicals


def SaveASN_AST(bPruneUnnamedInnerTASTEtypes, outputAsn1Grammar, identicals):
    d = DashUnderscoreAgnosticDict()
    for k, v in asnParser.g_names.items():
        d[k] = v
    with open(outputAsn1Grammar, 'w') as f:
        f.write('DATAVIEW DEFINITIONS AUTOMATIC TAGS ::= BEGIN\n\n')
        for k, v in d.items():
            if v._isArtificial:
                # Don't emit artificially generated inner types
                # (see last part of VerifyAndFixAST in asnParser)
                continue
            if bPruneUnnamedInnerTASTEtypes and 'TaStE' in k:
                # Don't emit artificially generated SMP2 types
                # (see smp2_A_mapper)

                # Update 2013-Jul-8: after having ASN1SCC handle unnamed inner types,
                # this is now impossible.
                continue  # pragma: no cover
            f.write('-- From ' + v._asnFilename + ' line ' + str(v._lineno) + '\n')
            f.write(k + ' ::= ')
            f.write(v.AsASN1(d) + "\n\n")
        for k, v in identicals.items():
            f.write(k + ' ::= ' + v + '\n\n')
        f.write('END\n')


def main(args):
    try:
        optlist, args = getopt.gnu_getopt(
            args,
            "hvpi:a:o:", ['help', 'verbose', 'prune', 'smp2=', 'asn1=', 'outAsn1='])
    except:
        usage("Invalid parameters passed...")
    inputSmp2Files = args
    inputAsn1Grammar = ""
    outputAsn1Grammar = ""
    verboseLevel = 0
    bPrune = False
    for opt, arg in optlist:
        if opt in ("-h", "--help"):
            usage()
        elif opt in ("-a", "--asn1"):
            inputAsn1Grammar = arg
        elif opt in ("-o", "--outAsn1"):
            outputAsn1Grammar = arg
        elif opt in ("-p", "--prune"):
            bPrune = True
        elif opt in ("-v", "--verbose"):
            verboseLevel += 1
    setVerbosity(verboseLevel)

    if not inputSmp2Files:
        usage("SMP2 catalogues were not provided")
    if not outputAsn1Grammar:
        usage("Mandatory option (-o newAsnGrammar.asn) missing")  # pragma: no cover

    def CheckFileExists(x):
        if not os.path.isfile(os.path.realpath(x)):
            usage("Input (%s) is not a file" % x)
    for f in inputSmp2Files:
        CheckFileExists(f)
    if inputAsn1Grammar:
        CheckFileExists(inputAsn1Grammar)

    smp2AsnAST, unused_idToTypeDict = ConvertCatalogueToASN_AST(inputSmp2Files)
    if inputAsn1Grammar:
        asnParser.ParseAsnFileList([inputAsn1Grammar])
    identicals = MergeASN1_AST(smp2AsnAST)
    SaveASN_AST(bPrune, outputAsn1Grammar, identicals)
    return 0


if __name__ == '__main__':
    for dbg in ["-d", "--debug"]:
        if dbg in sys.argv:
            sys.argv.remove(dbg)   # pragma: no cover
            import pdb             # pragma: no cover pylint: disable=wrong-import-position,wrong-import-order
            pdb.run('main(sys.argv[1:])')      # pragma: no cover
            break  # pragma: no cover
    else:
        sys.exit(main(sys.argv[1:]))

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
