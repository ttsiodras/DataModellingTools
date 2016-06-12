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
#from commonPy.asnAST import AsnBool,AsnMetaMember,AsnInt,AsnReal,AsnOctetString,AsnEnumerated,AsnSequence,AsnSet,AsnChoice,sourceSequenceLimit
from commonPy.asnAST import sourceSequenceLimit
from commonPy.utility import inform, panic
import commonPy.cleanupNodes
from commonPy.recursiveMapper import RecursiveMapper

import commonPy.verify

__doc__ = '''\
This is one of the code generators that Semantix developed for
the European research project ASSERT. It is now enhanced in the
context of Data Modelling and Data Modelling Tuning projects.

It reads the ASN.1 specification of the exchanged messages, and
generates "printer" functions for their content.
'''


def usage():
    '''Print usage instructions.'''
    msg = 'Usage: %s <options> input1.asn1 [input2.asn1]...\nWhere options are:\n'
    msg += '\t-o dirname\t\tDirectory to place generated files\nAnd one of:\n'
    msg += '\t-verbose\t\tDisplay more debug output\n'


class Printer(RecursiveMapper):
    def __init__(self):
        self.uniqueID = 0

    def UniqueID(self):
        self.uniqueID += 1 if self.uniqueID != 385 else 2
        return self.uniqueID

    def MapInteger(self, srcCVariable, prefix, _, __, ___):
        lines = []
        lines.append('#if WORD_SIZE==8')
        lines.append('printf("%%s%s %%lld\\n", paramName, %s);' % (prefix, srcCVariable))
        lines.append('#else')
        lines.append('printf("%%s%s %%d\\n", paramName, %s);' % (prefix, srcCVariable))
        lines.append('#endif')
        return lines

    def MapReal(self, srcCVariable, prefix, _, __, ___):
        return ['printf("%%s%s %%f\\n", paramName, %s);' % (prefix, srcCVariable)]

    def MapBoolean(self, srcCVariable, prefix, _, __, ___):
        return ['printf("%%s%s %%d\\n", paramName, (int)%s);' % (prefix, srcCVariable)]

    def MapOctetString(self, srcCVariable, prefix, node, __, ___):
        lines = []
        lines.append("{")
        lines.append("    int i;")
        limit = sourceSequenceLimit(node, srcCVariable)
        lines.append('    printf("%%s%s ", paramName);' % prefix)
        lines.append("    for(i=0; i<%s; i++)" % limit)
        lines.append('        printf("%%c", %s.arr[i]);' % srcCVariable)
        lines.append('    printf("\\n");')
        lines.append("}\n")
        return lines

    def MapEnumerated(self, srcCVariable, prefix, _, __, ___):
        return ['printf("%%s%s %%d\\n", paramName, (int)%s);' % (prefix, srcCVariable)]

    def MapSequence(self, srcCVariable, prefix, node, leafTypeDict, names):
        lines = []
        for child in node._members:
            lines.extend(
                self.Map(
                    "%s.%s" % (srcCVariable, self.CleanName(child[0])),
                    prefix + "::" + self.CleanName(child[0]),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcCVariable, prefix, node, leafTypeDict, names):
        return self.MapSequence(srcCVariable, prefix, node, leafTypeDict, names)

    def MapChoice(self, srcCVariable, prefix, node, leafTypeDict, names):
        lines = []
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append(
                "%sif (%s.kind == %s) {" %
                (self.maybeElse(childNo), srcCVariable, self.CleanName(child[2])))
            lines.extend(['    '+x for x in self.Map(
                          "%s.u.%s" % (srcCVariable, self.CleanName(child[0])),
                          prefix + "::" + self.CleanName(child[0]),
                          child[1],
                          leafTypeDict,
                          names)])
            lines.append("}")
        return lines

    def MapSequenceOf(self, srcCVariable, prefix, node, leafTypeDict, names):
        lines = []
        lines.append("{")
        uniqueId = self.UniqueID()
        lines.append("    int i%s;" % uniqueId)
        limit = sourceSequenceLimit(node, srcCVariable)
        lines.append("    for(i%s=0; i%s<%s; i%s++) {" % (uniqueId, uniqueId, limit, uniqueId))
        lines.extend(["        " + x for x in self.Map(
                     "%s.arr[i%s]" % (srcCVariable, uniqueId),
                     prefix + "::Elem",
                     node._containedType,
                     leafTypeDict,
                     names)])
        lines.append("    }")
        lines.append("}")
        return lines

    def MapSetOf(self, srcCVariable, prefix, node, leafTypeDict, names):
        return self.MapSequenceOf(srcCVariable, prefix, node, leafTypeDict, names)


def main():
    sys.path.append(os.path.abspath(os.path.dirname(sys.argv[0])))
    sys.path.append('commonPy')

    if sys.argv.count("-o") != 0:
        idx = sys.argv.index("-o")
        try:
            commonPy.configMT.outputDir = os.path.normpath(sys.argv[idx+1]) + os.sep
        except:  # pragma: no cover
            usage()  # pragma: no cover
        del sys.argv[idx]
        del sys.argv[idx]
        if not os.path.isdir(commonPy.configMT.outputDir):
            panic("'%s' is not a directory!\n" % commonPy.configMT.outputDir)  # pragma: no cover

    if "-verbose" in sys.argv:
        commonPy.configMT.verbose = True
        sys.argv.remove("-verbose")

    if len(sys.argv) < 2:
        usage()

    for f in sys.argv[1:]:
        if not os.path.isfile(f):
            panic("'%s' is not a file!\n" % f)  # pragma: no cover

    uniqueASNfiles = {}
    for grammar in sys.argv[1:]:
        uniqueASNfiles[grammar]=1
    commonPy.asnParser.ParseAsnFileList(list(uniqueASNfiles.keys()))

    for asnFile in uniqueASNfiles:
        tmpNames = {}
        for name in commonPy.asnParser.g_typesOfFile[asnFile]:
            tmpNames[name] = commonPy.asnParser.g_names[name]

        uniqueASNfiles[asnFile] = [
            copy.copy(tmpNames),                            # map Typename to type definition class from asnAST
            copy.copy(commonPy.asnParser.g_astOfFile[asnFile]),    # list of nameless type definitions
            copy.copy(commonPy.asnParser.g_leafTypeDict)]   # map from Typename to leafType

        inform("Checking that all base nodes have mandatory ranges set in %s..." % asnFile)
        for node in list(tmpNames.values()):
            verify.VerifyRanges(node, commonPy.asnParser.g_names)

    # If some AST nodes must be skipped (for any reason), go learn about them
    badTypes = commonPy.cleanupNodes.DiscoverBadTypes()

    C_HeaderFile = open(commonPy.configMT.outputDir + os.sep + "PrintTypes.h", "w")
    C_HeaderFile.write('#ifndef __PRINTTYPES_H__\n')
    C_HeaderFile.write('#define __PRINTTYPES_H__\n\n')
    C_HeaderFile.write('#ifdef __cplusplus\n')
    C_HeaderFile.write('extern "C" {\n')
    C_HeaderFile.write('#endif\n\n')

    C_SourceFile = open(commonPy.configMT.outputDir + os.sep + "PrintTypes.c", "w")
    C_SourceFile.write('#include <stdio.h>\n\n')
    C_SourceFile.write('#include "PrintTypes.h"\n\n')
    C_SourceFile.write('#ifdef __linux__\n')
    C_SourceFile.write('#include <pthread.h>\n\n')
    C_SourceFile.write('static pthread_mutex_t g_printing_mutex = PTHREAD_MUTEX_INITIALIZER;\n\n')
    C_SourceFile.write('#endif\n\n')

    # Work on each ASN.1 file's types
    for asnFile in uniqueASNfiles:
        asn_name = os.path.basename(os.path.splitext(asnFile)[0])
        C_HeaderFile.write("#include \"%s.h\" // Generated by ASN1SCC\n\n" % asn_name)

        leafTypeDict = uniqueASNfiles[asnFile][2]
        inform("Executing mappings for types inside %s...", asnFile)
        names = uniqueASNfiles[asnFile][0]

        printer = Printer()

        for nodeTypename in names:
            # Check if this type must be skipped
            if nodeTypename in badTypes:
                continue
            node = names[nodeTypename]
            if node._isArtificial:
                continue
            cleanNodeTypename = printer.CleanName(nodeTypename)
            inform("Processing %s...", nodeTypename)

            # First, make sure we know what leaf type this node is
            assert(nodeTypename in leafTypeDict)

            C_HeaderFile.write('void Print%s(const char *paramName, const asn1Scc%s *pData);\n' % (cleanNodeTypename, cleanNodeTypename))
            C_SourceFile.write('void Print%s(const char *paramName, const asn1Scc%s *pData)\n{\n' % (cleanNodeTypename, cleanNodeTypename))
            C_SourceFile.write('#ifdef __linux__\n')
            C_SourceFile.write('    pthread_mutex_lock(&g_printing_mutex);\n')
            C_SourceFile.write('#endif\n')
            #C_SourceFile.write('\n'.join(printer.Map('(*pData)', '', node, leafTypeDict, commonPy.asnParser.g_names)))
            lines = ["    "+x for x in printer.Map('(*pData)', '', node, leafTypeDict, commonPy.asnParser.g_names)]
            C_SourceFile.write("\n".join(lines))
            C_SourceFile.write('\n#ifdef __linux__\n')
            C_SourceFile.write('    pthread_mutex_unlock(&g_printing_mutex);\n')
            C_SourceFile.write('#endif\n')
            C_SourceFile.write('}\n\n')

    C_HeaderFile.write('\n#ifdef __cplusplus\n')
    C_HeaderFile.write('}\n')
    C_HeaderFile.write('#endif\n')
    C_HeaderFile.write('\n#endif\n')

if __name__ == "__main__":
    if "-pdb" in sys.argv:
        sys.argv.remove("-pdb")  # pragma: no cover
        import pdb  # pragma: no cover
        pdb.run('main()')  # pragma: no cover
    else:
        main()
