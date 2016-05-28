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
import re
import os
import commonPy
import commonPy.asnParser
from commonPy.utility import panic, inform
from commonPy.asnAST import (
    AsnBool, AsnInt, AsnReal, AsnString, isSequenceVariable, AsnEnumerated,
    AsnSequence, AsnSet, AsnChoice, AsnMetaMember, AsnSequenceOf, AsnSetOf,
    AsnBasicNode)
import commonPy.cleanupNodes

# The Python file written to
g_outputFile = None

# The SETers and GETers files
g_outputGetSetH = None
g_outputGetSetC = None

g_bHasStartupRunOnce = False


def Version():
    print "Code generator: " + \
        "$Id: python_A_mapper.py 2400 2012-09-04 10:40:19Z ttsiodras $"  # pragma: no cover


def CleanNameAsPythonWants(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


def OnStartup(unused_modelingLanguage, asnFile, outputDir):
    os.system("bash -c '[ ! -f \"" + outputDir + "/" + asnFile + "\" ] && cp \"" + asnFile + "\" \"" + outputDir + "\"'")
    this_path = os.path.dirname(__file__)
    stubs = this_path + os.sep + 'Stubs.py'
    os.system('cp "{}" "{}"'.format(stubs, outputDir))
    enum_learner = this_path + os.sep + 'learn_CHOICE_enums.py'
    os.system('cp "{}" "{}"'.format(enum_learner, outputDir))
    global g_bHasStartupRunOnce
    if g_bHasStartupRunOnce:
        # Don't rerun, it has already done all the work
        # for all the ASN.1 files used
        return  # pragma: no cover
    else:
        g_bHasStartupRunOnce = True
    if not asnFile.endswith(".asn"):
        panic("The ASN.1 grammar file (%s) doesn't end in .asn" %
              asnFile)  # pragma: no cover
    outputFilename = os.path.basename(asnFile)
    outputFilename = re.sub(r'[^a-zA-Z0-9_]', '_', outputFilename) + ".py"
    origGrammarBase = os.path.basename(asnFile.replace(".asn", ""))
    base = re.sub(r'[^a-zA-Z0-9_]', '_', origGrammarBase)
    inform("Python_A_mapper: Creating file '%s'...", outputFilename)
    global g_outputFile
    g_outputFile = open(outputDir + outputFilename, 'w')
    g_outputFile.write("import DV\n\n")
    g_outputFile.write("from Stubs import (\n")
    g_outputFile.write(
        "    myassert, panicWithCallStack, Clean, DataStream, COMMON)\n\n")
    global g_outputGetSetH
    g_outputGetSetH = open(outputDir + base + "_getset.h", "w")
    g_outputGetSetH.write('#ifndef __GETSET_H__\n#define __GETSET_H__\n\n')
    g_outputGetSetH.write('#include "%s.h"\n\n' % origGrammarBase)
    g_outputGetSetH.write('size_t GetStreamCurrentLength(BitStream *pBitStrm);\n')
    g_outputGetSetH.write('byte *GetBitstreamBuffer(BitStream *pBitStrm);\n')
    g_outputGetSetH.write('byte GetBufferByte(byte *p, size_t off);\n')
    g_outputGetSetH.write('void SetBufferByte(byte *p, size_t off, byte b);\n')
    g_outputGetSetH.write('void ResetStream(BitStream *pStrm);\n')
    g_outputGetSetH.write('BitStream *CreateStream(size_t bufferSize);\n')
    g_outputGetSetH.write('void DestroyStream(BitStream *pBitStrm);\n\n')
    global g_outputGetSetC
    g_outputGetSetC = open(outputDir + "%s_getset.c" % base, "w")
    g_outputGetSetC.write('#include <stdio.h>\n')
    g_outputGetSetC.write('#include <stdlib.h>\n')
    g_outputGetSetC.write('#include <assert.h>\n')
    g_outputGetSetC.write('#include <string.h>\n')
    g_outputGetSetC.write('#include "%s_getset.h"\n\n' % base)
    g_outputGetSetC.write('size_t GetStreamCurrentLength(BitStream *pBitStrm) {\n')
    g_outputGetSetC.write('    return pBitStrm->currentByte + ((pBitStrm->currentBit+7)/8);\n')
    g_outputGetSetC.write('}\n\n')
    g_outputGetSetC.write('byte *GetBitstreamBuffer(BitStream *pBitStrm) {\n')
    g_outputGetSetC.write('    return pBitStrm->buf;\n')
    g_outputGetSetC.write('}\n\n')
    g_outputGetSetC.write('byte GetBufferByte(byte *p, size_t off) {\n')
    g_outputGetSetC.write('    assert(p);\n')
    g_outputGetSetC.write('    return p[off];\n')
    g_outputGetSetC.write('}\n\n')
    g_outputGetSetC.write('void SetBufferByte(byte *p, size_t off, byte b) {\n')
    g_outputGetSetC.write('    assert(p);\n')
    g_outputGetSetC.write('    p[off] = b;\n')
    g_outputGetSetC.write('}\n\n')
    g_outputGetSetC.write('void ResetStream(BitStream *pStrm) {\n')
    g_outputGetSetC.write('    assert(pStrm);\n')
    g_outputGetSetC.write('    assert(pStrm->count > 0);\n')
    g_outputGetSetC.write('    pStrm->currentByte = 0;\n')
    g_outputGetSetC.write('    pStrm->currentBit = 0;\n')
    g_outputGetSetC.write('}\n\n')
    g_outputGetSetC.write('BitStream *CreateStream(size_t bufferSize) {\n')
    g_outputGetSetC.write('    BitStream *pBitStrm = malloc(sizeof(BitStream));\n')
    g_outputGetSetC.write('    assert(pBitStrm);\n')
    g_outputGetSetC.write('    pBitStrm->buf = malloc(bufferSize);\n')
    g_outputGetSetC.write('    assert(pBitStrm->buf);\n')
    g_outputGetSetC.write('    pBitStrm->count = bufferSize;\n')
    g_outputGetSetC.write('    memset(pBitStrm->buf, 0x0, bufferSize);\n')
    g_outputGetSetC.write('    ResetStream(pBitStrm);\n')
    g_outputGetSetC.write('}\n\n')
    g_outputGetSetC.write('void DestroyStream(BitStream *pBitStrm) {\n')
    g_outputGetSetC.write('    assert(pBitStrm);\n')
    g_outputGetSetC.write('    assert(pBitStrm->buf);\n')
    g_outputGetSetC.write('    free(pBitStrm->buf);\n')
    g_outputGetSetC.write('    free(pBitStrm);\n')
    g_outputGetSetC.write('}\n\n')
    Makefile = open(outputDir + "Makefile.python", 'w')

    # Note that this Makefile will use a custom ASN1SCC invocation
    # where "-equal" is passed - the _Equal functions will be generated
    # and used during comparisons of incoming TMs (For MSCs)

    # mono_exe = "mono " if sys.argv[0].endswith('.py') and sys.platform.startswith('linux') else ""
    mono_exe = ""
    Makefile.write('''
ASN1SCC:=asn1.exe
ASN2DATAMODEL:=asn2dataModel
GRAMMAR := %(origGrammarBase)s
BASEGRAMMAR := %(base)s
BDIR:= .
OBJ     := $(BDIR)/$(GRAMMAR).o $(BDIR)/asn1crt.o $(BDIR)/real.o $(BDIR)/acn.o $(BDIR)/ber.o $(BDIR)/xer.o $(BDIR)/$(BASEGRAMMAR)_getset.o

all:    $(BDIR)/$(BASEGRAMMAR)_getset.so $(BDIR)/DV.py

$(BDIR)/$(GRAMMAR)_getset.c:       $(GRAMMAR).asn
%(tab)smkdir -p $(BDIR)
%(tab)s$(ASN2DATAMODEL) -toPython -o $(BDIR) $<

$(BDIR)/asn1crt.c $(BDIR)/$(GRAMMAR).c $(BDIR)/real.c $(BDIR)/acn.c $(BDIR)/ber.c $(BDIR)/xer.c $(BDIR)/$(GRAMMAR).h $(BDIR)/asn1crt.h:       $(GRAMMAR).asn
%(tab)sif [ ! -f "$(GRAMMAR).acn" ] ; then %(mono)s$(ASN1SCC) -ACND -o $(BDIR) $< ; fi
%(tab)s%(mono)s$(ASN1SCC) -ACN -c -uPER -equal -wordSize 8 -o $(BDIR) $< $(GRAMMAR).acn

$(BDIR)/DV.py:       $(GRAMMAR).asn
%(tab)sgrep 'REQUIRED_BYTES_FOR_ENCODING' $(BDIR)/$(GRAMMAR).h | awk '{print $$2 " = " $$3}' > $@
%(tab)slearn_CHOICE_enums.py %(base)s >> $@

$(BDIR)/%%.o:       $(BDIR)/%%.c
%(tab)sgcc -g -fPIC -c `python-config --includes` -o $@ $<

$(BDIR)/$(BASEGRAMMAR)_getset.so:	${OBJ}
%(tab)sgcc -g -fPIC -shared `python-config --ldflags` -o $@ $^

clean:
%(tab)srm -f $(BDIR)/asn1crt.?  $(BDIR)/real.?  $(BDIR)/$(GRAMMAR).?  $(BDIR)/acn.?  $(BDIR)/ber.? $(BDIR)/xer.?
%(tab)srm -f $(BDIR)/DV.py $(BDIR)/*.pyc $(BDIR)/$(BASEGRAMMAR)_getset.? $(BDIR)/$(BASEGRAMMAR)_getset.so
%(tab)srm -f $(BDIR)/$(GRAMMAR)_asn.py
''' % {'tab': '\t', 'base': base, 'origGrammarBase': origGrammarBase, 'mono': mono_exe})
    Makefile.close()
    CreateDeclarationsForAllTypes(commonPy.asnParser.g_names, commonPy.asnParser.g_leafTypeDict)
    g_outputGetSetH.write('\n/* Helper functions for NATIVE encodings */\n\n')
    g_outputGetSetC.write('\n/* Helper functions for NATIVE encodings */\n\n')

    def WorkOnType(nodeTypename):
        typ = CleanNameAsPythonWants(nodeTypename)
        g_outputGetSetH.write('void SetDataFor_%s(void *dest, void *src);\n' % typ)
        g_outputGetSetH.write("byte* MovePtrBySizeOf_%s(byte *pData);\n" % typ)
        g_outputGetSetH.write("byte* CreateInstanceOf_%s(void);\n" % typ)
        g_outputGetSetH.write("void DestroyInstanceOf_%s(byte *pData);\n\n" % typ)
        g_outputGetSetC.write('void SetDataFor_%s(void *dest, void *src)\n' % typ)
        g_outputGetSetC.write('{\n')
        g_outputGetSetC.write('    memcpy(dest, src, sizeof(%s));\n' % typ)
        g_outputGetSetC.write('}\n\n')
        g_outputGetSetC.write("byte* MovePtrBySizeOf_%s(byte *pData)\n" % typ)
        g_outputGetSetC.write('{\n')
        g_outputGetSetC.write('    return pData + sizeof(%s);\n' % typ)
        g_outputGetSetC.write('}\n\n')
        g_outputGetSetC.write("byte* CreateInstanceOf_%s() {\n" % typ)
        g_outputGetSetC.write('    %s *p = (%s*)malloc(sizeof(%s));\n' % (typ, typ, typ))
        if typ != 'int':
            g_outputGetSetC.write('    %s_Initialize(p);\n' % typ)
        else:
            g_outputGetSetC.write('    *p = 0;\n')
        g_outputGetSetC.write('    return (byte*)p;\n')
        g_outputGetSetC.write('}\n\n')
        g_outputGetSetC.write("void DestroyInstanceOf_%s(byte *pData) {\n" % typ)
        g_outputGetSetC.write('    free(pData);\n')
        g_outputGetSetC.write('}\n\n')
    for nodeTypename, node in commonPy.asnParser.g_names.iteritems():
        if node._isArtificial:
            continue
        WorkOnType(nodeTypename)
    WorkOnType("int")
    g_outputGetSetH.write('\n#endif\n')
    g_outputGetSetH.close()
    g_outputGetSetC.close()

    retTypes = {}
    for line in open(outputDir + "%s_getset.c" % base):
        if any(x in line for x in ['_Get(', '_GetLength']):
            retType, funcName = line.split()[0:2]
            funcName = funcName.split('(')[0]
            retTypes[funcName] = retType
    g_outputGetSetC = open(outputDir + "DV_Types.py", 'w')
    g_outputGetSetC.write('funcTypeLookup = ' + repr(retTypes))
    g_outputGetSetC.close()


def OnBasic(unused_nodeTypename, unused_node, unused_leafTypeDict):
    pass


def OnSequence(unused_nodeTypename, unused_node, unused_leafTypeDict):
    pass


def OnSet(unused_nodeTypename, unused_node, unused_leafTypeDict):
    pass  # pragma: nocover


def OnEnumerated(unused_nodeTypename, unused_node, unused_leafTypeDict):
    pass


def OnSequenceOf(unused_nodeTypename, unused_node, unused_leafTypeDict):
    pass


def OnSetOf(unused_nodeTypename, unused_node, unused_leafTypeDict):
    pass  # pragma: nocover


def OnChoice(unused_nodeTypename, unused_node, unused_leafTypeDict):
    pass


def OnShutdown():
    pass


class Params(object):
    cTypes = {
        "BOOLEAN": "flag",
        "INTEGER": "asn1SccSint",
        "REAL": "double",
        "ENUMERATED": "int",
        "OCTET STRING": "byte*",
    }

    def __init__(self, nodeTypename):
        self._vars = []
        self._types = []
        self._nodeTypeName = nodeTypename

    def AddParam(self, node, varName, unused_leafTypeDict):
        # Handle variable name
        while varName in self._vars:
            varName += "_"
        # Handle type
        # special case:int is used for SEQUENCE_OF (iDx)
        assert node == "int"
        self._vars.append(varName)
        self._types.append("int")
        return True
        # For others, lookup the C type
        # try:
        #     realLeafType = leafTypeDict[node._leafType]
        # except:
        #     #panic("Python_A_mapper: Only primitive types can be C params, not %s" % node.Location())
        #     # the lookup will fail for non-primitives, which we ignore
        #     return False

        # self._vars.append(varName)
        # try:
        #     self._types.append(self.cTypes[realLeafType])
        # except:
        #     panic("Python_A_mapper: Can't map (%s,%s) to C type\n" % (varName, realLeafType))
        # return True

    def Pop(self):
        self._vars.pop()
        self._types.pop()

    def GetDecl(self):
        params = CleanNameAsPythonWants(self._nodeTypeName) + "* root"
        for v, t in zip(self._vars, self._types):
            params += ", "+t+" "+v
        return params


def CommonBaseImpl(comment, ctype, path, params, accessPathInC, postfix="", returnPointer=False):
    takeAddr = '&' if returnPointer else ''
    g_outputGetSetH.write("\n/* %s */\n%s %s_Get%s(%s);\n" % (comment, ctype, path, postfix, params.GetDecl()))
    g_outputGetSetC.write("\n/* %s */\n%s %s_Get%s(%s)\n" % (comment, ctype, path, postfix, params.GetDecl()))
    g_outputGetSetC.write("{\n")
    g_outputGetSetC.write("    return " + takeAddr + "(*root)" + accessPathInC + ";\n")
    g_outputGetSetC.write("}\n")
    if not returnPointer:
        g_outputGetSetH.write("\n/* %s */\nvoid %s_Set%s(%s, %s value);\n" % (comment, path, postfix, params.GetDecl(), ctype))
        g_outputGetSetC.write("\n/* %s */\nvoid %s_Set%s(%s, %s value)\n" % (comment, path, postfix, params.GetDecl(), ctype))
        g_outputGetSetC.write("{\n")
        g_outputGetSetC.write("    (*root)" + accessPathInC + " = value;\n")
        g_outputGetSetC.write("}\n")


# def CommonBaseImplSequenceFixed(comment, ctype, path, params, accessPathInC, node, postfix = ""):
def CommonBaseImplSequenceFixed(comment, ctype, path, params, _, node, postfix=""):
    g_outputGetSetH.write("\n/* %s */\n%s %s_Get%s(%s);\n" % (comment, ctype, path, postfix, params.GetDecl()))
    g_outputGetSetC.write("\n/* %s */\n%s %s_Get%s(%s)\n" % (comment, ctype, path, postfix, params.GetDecl()))
    g_outputGetSetC.write("{\n")
    g_outputGetSetC.write("    return " + str(node._range[-1]) + ";\n")
    g_outputGetSetC.write("}\n")
    g_outputGetSetH.write("\n/* %s */\nvoid %s_Set%s(%s, %s value);\n" % (comment, path, postfix, params.GetDecl(), ctype))
    g_outputGetSetC.write("\n/* %s */\nvoid %s_Set%s(%s, %s value)\n" % (comment, path, postfix, params.GetDecl(), ctype))
    g_outputGetSetC.write("{\n")
    g_outputGetSetC.write("    fprintf(stderr, \"WARNING: setting length of fixed-length sequence\\n\");\n")
    g_outputGetSetC.write("}\n")


def CreateGettersAndSetters(path, params, accessPathInC, node, names, leafTypeDict):
    if isinstance(node, str):
        node = names[node]
    if isinstance(node, AsnMetaMember):
        node = names[node._containedType]

    if isinstance(node, AsnBool):
        CommonBaseImpl("BOOLEAN", "flag", path, params, accessPathInC)
    elif isinstance(node, AsnInt):
        CommonBaseImpl("INTEGER", "asn1SccSint", path, params, accessPathInC)
    elif isinstance(node, AsnReal):
        CommonBaseImpl("REAL", "double", path, params, accessPathInC)
    elif isinstance(node, AsnString):
        if node._range == []:
            panic("Python_A_mapper: string (in %s) must have a SIZE constraint!\n" % node.Location())  # pragma: no cover
        if isSequenceVariable(node):
            CommonBaseImpl("OCTETSTRING", "long", path, params, accessPathInC+".nCount", "Length")
        else:
            CommonBaseImplSequenceFixed("OCTETSTRING", "long", path, params, accessPathInC+".nCount", node, "Length")
        params.AddParam('int', "iDx", leafTypeDict)
        CommonBaseImpl("OCTETSTRING_bytes", "byte", path+"_iDx", params, accessPathInC + (".arr["+params._vars[-1]+"]"), "")
        params.Pop()
    elif isinstance(node, AsnEnumerated):
        CommonBaseImpl("ENUMERATED", "int", path, params, accessPathInC)
    elif isinstance(node, AsnSequence) or isinstance(node, AsnSet) or isinstance(node, AsnChoice):
        if isinstance(node, AsnChoice):
            CommonBaseImpl("CHOICE selector", "int", path+"_kind", params, accessPathInC+".kind")
        union = ""
        if isinstance(node, AsnChoice):
            union = ".u"
        for child in node._members:
            childNode = child[1]
            childVarname = CleanNameAsPythonWants(child[0])
            if isinstance(childNode, AsnMetaMember):
                baseTypeOfChild = names[childNode._containedType]._leafType
                baseTypeOfChild = leafTypeDict.get(baseTypeOfChild, baseTypeOfChild)
                if baseTypeOfChild not in ['INTEGER', 'REAL', 'BOOLEAN', 'OCTET STRING', 'ENUMERATED']:
                    useStar = '' if baseTypeOfChild.endswith('OF') else '*'
                    CommonBaseImpl("Field " + childVarname + " selector", CleanNameAsPythonWants(childNode._containedType)+useStar, path+"_"+childVarname, params, accessPathInC+union+"."+childVarname, returnPointer=not baseTypeOfChild.endswith('OF'))
            CreateGettersAndSetters(path+"_"+childVarname, params, accessPathInC+union+"."+childVarname, child[1], names, leafTypeDict)
    elif isinstance(node, AsnSequenceOf) or isinstance(node, AsnSetOf):
        containedNode = node._containedType
        if isinstance(containedNode, str):
            containedNode = names[containedNode]
        if isSequenceVariable(node):
            CommonBaseImpl("SEQUENCEOF/SETOF", "long", path, params, accessPathInC+".nCount", "Length")
        else:
            CommonBaseImplSequenceFixed("SEQUENCEOF/SETOF", "long", path, params, accessPathInC+".nCount", node, "Length")
        params.AddParam('int', "iDx", leafTypeDict)
        CreateGettersAndSetters(path+"_iDx", params, accessPathInC + (".arr["+params._vars[-1]+"]"), node._containedType, names, leafTypeDict)
        params.Pop()


def DumpTypeDumper(codeIndent, outputIndent, lines, variableName, node, names):
    ''' Return the lines of code needed to display the value of a variable
        of a given type, in the ASN.1 Value Notation format (aka GSER) '''
    if isinstance(node, AsnBool):
        lines.append(
            codeIndent +
            'lines.append("%s"+str(%s.Get()!=0).upper())' % (outputIndent, variableName))
    elif isinstance(node, AsnInt):
        lines.append(
            codeIndent + 'lines.append("%s"+str(%s.Get()))' % (outputIndent, variableName))
    elif isinstance(node, AsnReal):
        lines.append(
            codeIndent + 'lines.append("%s"+str(%s.Get()))' % (outputIndent, variableName))
    elif isinstance(node, AsnString):
        lines.append(
            codeIndent +
            'lines.append("%s\\\""+str(%s.GetPyString()) + "\\\"")' % (outputIndent, variableName))
    elif isinstance(node, AsnEnumerated):
        mapping = str({val: name for name, val in node._members})
        lines.append(
            codeIndent +
            'lines.append("%s"+%s[str(%s.Get())])' % (outputIndent, mapping, variableName))
    elif isinstance(node, (AsnChoice, AsnSet, AsnSequence)):
        if not isinstance(node, AsnChoice):
            lines.append(codeIndent + 'lines.append("{")')
        extraIndent = ""
        sep = " "
        if isinstance(node, AsnChoice):
            extraIndent = " "
        for idx, child in enumerate(node._members):
            if isinstance(node, AsnChoice):
                lines.append(
                    codeIndent + 'if %s.kind.Get() == DV.%s:' % (
                        variableName,
                        CleanNameAsPythonWants(child[2])))
                sep = ": "
            elif idx > 0:
                # Separate fields with comas:
                #
                # - only when we are past the 1st field
                # - and when we are NOT a CHOICE
                lines.append(codeIndent + extraIndent + "lines.append(', ')")
            lines.append(
                codeIndent + extraIndent +
                'lines.append("%s%s%s")' % (outputIndent, child[0], sep))
            childNode = child[1]
            if isinstance(childNode, AsnMetaMember):
                childNode = names[childNode._containedType]
            DumpTypeDumper(
                codeIndent + extraIndent, outputIndent + " ", lines,
                variableName + "." + CleanNameAsPythonWants(child[0]), childNode, names)
        if not isinstance(node, AsnChoice):
            lines.append(codeIndent + 'lines.append("}")')
    elif isinstance(node, AsnSetOf) or isinstance(node, AsnSequenceOf):
        lines.append(codeIndent + 'lines.append("{")')
        containedNode = node._containedType
        if isinstance(containedNode, str):
            containedNode = names[containedNode]
        lines.append(codeIndent + 'def emitElem(i):')
        lines.append(codeIndent + '    if i>0:')
        lines.append(codeIndent + '        lines.append(",")')
        DumpTypeDumper(codeIndent+"    ", outputIndent+" ", lines,
                       variableName+'[i]', containedNode, names)
        lines.append(codeIndent + "map(emitElem, xrange(%s.GetLength()))" % variableName)
        lines.append(codeIndent + 'lines.append("}")')


def CreateDeclarationForType(nodeTypename, names, leafTypeDict):
    node = names[nodeTypename]
    name = CleanNameAsPythonWants(nodeTypename)
    if isinstance(node, AsnBasicNode) or isinstance(node, AsnEnumerated) or \
            isinstance(node, AsnSequence) or isinstance(node, AsnSet) or \
            isinstance(node, AsnChoice) or isinstance(node, AsnSequenceOf) or \
            isinstance(node, AsnSetOf):

        g_outputFile.write("class " + name + "(COMMON):\n")
        if isinstance(node, AsnEnumerated):
            g_outputFile.write("    # Allowed enumerants:\n")
            allowed = "    allowed = ["
            for member in node._members:
                # member[0] enumerant name, member[1] integer value (or None)
                if member[1] is not None:
                    g_outputFile.write("    %s = %s\n" % (CleanNameAsPythonWants(member[0]), member[1]))
                    allowed += ("%s, " % (CleanNameAsPythonWants(member[0])))
                else:  # pragma: no cover
                    panic("Python_A_mapper: must have values for enumerants (%s)" % node.Location())  # pragma: no cover
            g_outputFile.write(allowed + "]\n")
        if isinstance(node, (AsnSequence, AsnSet)):
            g_outputFile.write("    # Ordered list of fields:\n")
            children = [child[0] for child in node._members]
            g_outputFile.write("    children_ordered = ['{}']\n\n"
                               .format("', '".join(children)))
        g_outputFile.write("    def __init__(self):\n")
        g_outputFile.write("        COMMON.__init__(self, \"" + name + "\")\n")
        if isinstance(node, AsnString):
            g_outputFile.write('''#\n''')
        CreateGettersAndSetters(name+"_", Params(nodeTypename), "", node, names, leafTypeDict)
        g_outputFile.write("\n    def GSER(self):\n")
        g_outputFile.write("        ''' Return the GSER representation of the value '''\n")
        g_outputFile.write("        lines = []\n")
        lines = []
        DumpTypeDumper("        ", "", lines, "self", names[nodeTypename], names)
        g_outputFile.write("\n".join(lines) + "\n\n")
        g_outputFile.write("        return ' '.join(lines)")
        g_outputFile.write("\n\n    def PrintAll(self):\n")
        g_outputFile.write("        ''' Display a variable of this type '''\n")
        g_outputFile.write("        print(self.GSER() + '\\n')\n\n\n")

    else:  # pragma: no cover
        panic("Unexpected ASN.1 type... Send this grammar to Semantix")  # pragma: no cover


def CreateDeclarationsForAllTypes(names, leafTypeDict):
    for nodeTypename in names:
        if not names[nodeTypename]._isArtificial and not commonPy.cleanupNodes.IsBadType(nodeTypename):
            CreateDeclarationForType(nodeTypename, names, leafTypeDict)
