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
__doc__ = '''
This is the code generator for the PragmaDev RTDS code mappers.
This backend is called by aadl2glueC, when an RTDS subprogram
is identified in the input concurrency view.

Implementation notes: Like OG, RTDS is a complex case;
It is used to model asynchronous processes (SDL)...

'''

from commonPy.utility import panic
from commonPy.asnAST import isSequenceVariable, sourceSequenceLimit, AsnBasicNode, AsnEnumerated

from recursiveMapper import RecursiveMapper
from asynchronousTool import ASynchronousToolGlueGenerator

import c_B_mapper

isAsynchronous = True
rtdsBackend = None
cBackend = None


def Version():
    print "Code generator: " + "$Id: rtds_B_mapper.py 2390 2012-07-19 12:39:17Z ttsiodras $"


class FromRTDSToASN1SCC(RecursiveMapper):
    def __init__(self):
        self.uniqueID = 0

    def UniqueID(self):
        self.uniqueID += 1
        return self.uniqueID

    def DecreaseUniqueID(self):
        self.uniqueID -= 1

    def MapInteger(self, srcSDLVariable, destVar, _, __, ___):
        return ["%s = (asn1SccSint) %s;\n" % (destVar, srcSDLVariable)]

    def MapReal(self, srcSDLVariable, destVar, _, __, ___):
        return ["%s = (double)%s;\n" % (destVar, srcSDLVariable)]

    def MapBoolean(self, srcSDLVariable, destVar, _, __, ___):
        return ["%s = (%s==TRUE)?0xff:0;\n" % (destVar, srcSDLVariable)]

    def MapOctetString(self, srcSDLVariable, destVar, node, __, ___):
        lines = []
        lines.append("{\n")
        lines.append("    int i;\n")
        lines.append("    for(i=0; i<%s.__length; i++) {\n" % srcSDLVariable)
        lines.append("        %s.arr[i] = %s.__string[i];\n" % (destVar, srcSDLVariable))
        lines.append("    }\n")
        #for i in xrange(0, node._range[-1]):
        #       lines.append("    placeHolder[%d] = %s[%d];\n" % (i, srcSDLVariable, i))
        if isSequenceVariable(node):
            lines.append("    %s.nCount = %s.__length;\n" % (destVar, srcSDLVariable))
        lines.append("}\n")
        return lines

    def MapEnumerated(self, srcSDLVariable, destVar, _, __, ___):
        return ["%s = %s;\n" % (destVar, srcSDLVariable)]

    def MapSequence(self, srcSDLVariable, destVar, node, leafTypeDict, names):
        lines = []
        for child in node._members:
            lines.extend(
                self.Map(
                    "%s.%s" % (srcSDLVariable, self.CleanName(child[0])),
                    destVar + "." + self.CleanName(child[0]),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcSDLVariable, destVar, node, leafTypeDict, names):
        return self.MapSequence(srcSDLVariable, destVar, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcSDLVariable, destVar, node, leafTypeDict, names):
        lines = []
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.present == %d) {\n" % (self.maybeElse(childNo), srcSDLVariable, childNo))
            lines.extend(["    "+x for x in self.Map(
                         "%s.__value.%s" % (srcSDLVariable, self.CleanName(child[0])),
                         destVar + (".u.%s" % self.CleanName(child[0])),
                         child[1],
                         leafTypeDict,
                         names)])
            lines.append("    %s.kind = %s;\n" % (destVar, self.CleanName(child[2])))
            lines.append("}\n")
        return lines

    def MapSequenceOf(self, srcSDLVariable, destVar, node, leafTypeDict, names):
        lines = []
        lines.append("{\n")
        uniqueId = self.UniqueID()
        lines.append("    int i%s;\n" % uniqueId)
        lines.append("    for(i%s=0; i%s<%s.length; i%s++) {\n" % (uniqueId, uniqueId, srcSDLVariable, uniqueId))
        lines.extend(["        " + x for x in self.Map(
                     "%s.elements[i%s]" % (srcSDLVariable, uniqueId),
                     "%s.arr[i%s]" % (destVar, uniqueId),
                     node._containedType,
                     leafTypeDict,
                     names)])
        lines.append("    }\n")
        if isSequenceVariable(node):
            lines.append("    %s.nCount = %s.length;\n" % (destVar, srcSDLVariable))
        lines.append("}\n")
        self.DecreaseUniqueID()
        return lines

    def MapSetOf(self, unused_srcSDLVariable, unused_destVar, node, unused_leafTypeDict, unused_names):
        panic("The PragmaDev mapper does not support SETOF. Please use SEQUENCEOF instead (%s)" % node.Location())  # pragma: nocover


class FromRTDSToOSS(RecursiveMapper):
    def __init__(self):
        self.uniqueID = 0

    def UniqueID(self):
        self.uniqueID += 1
        return self.uniqueID

    def DecreaseUniqueID(self):
        self.uniqueID -= 1

    def MapInteger(self, srcSDLVariable, destVar, _, __, ___):
        return ["%s = %s;\n" % (destVar, srcSDLVariable)]

    def MapReal(self, srcSDLVariable, destVar, _, __, ___):
        return ["%s = %s;\n" % (destVar, srcSDLVariable)]

    def MapBoolean(self, srcSDLVariable, destVar, _, __, ___):
        return ["%s = (%s==SDL_TRUE)?0xff:0;\n" % (destVar, srcSDLVariable)]

    def MapOctetString(self, srcSDLVariable, destVar, _, __, ___):
        lines = []
        lines.append("{\n")
        lines.append("    int i;\n")
        lines.append("    for(i=0; i<%s.length; i++) {\n" % srcSDLVariable)
        lines.append("        unsigned char value;\n")
        lines.append("        if(%s.cont[i].cont[0]) value |= 128;\n" % srcSDLVariable)
        lines.append("        if(%s.cont[i].cont[1]) value |= 64;\n" % srcSDLVariable)
        lines.append("        if(%s.cont[i].cont[2]) value |= 32;\n" % srcSDLVariable)
        lines.append("        if(%s.cont[i].cont[3]) value |= 16;\n" % srcSDLVariable)
        lines.append("        if(%s.cont[i].cont[4]) value |= 8;\n" % srcSDLVariable)
        lines.append("        if(%s.cont[i].cont[5]) value |= 4;\n" % srcSDLVariable)
        lines.append("        if(%s.cont[i].cont[6]) value |= 2;\n" % srcSDLVariable)
        lines.append("        if(%s.cont[i].cont[7]) value |= 1;\n" % srcSDLVariable)
        lines.append("        %s.value[i] = value;\n" % destVar)
        lines.append("    }\n")
        #for i in xrange(0, node._range[-1]):
        #       lines.append("    placeHolder[%d] = %s[%d];\n" % (i, srcSDLVariable, i))
        lines.append("    %s.length = %s.length;\n" % (destVar, srcSDLVariable))
        lines.append("}\n")
        return lines

    def MapEnumerated(self, srcSDLVariable, destVar, _, __, ___):
        return ["%s = %s;\n" % (destVar, srcSDLVariable)]

    def MapSequence(self, srcSDLVariable, destVar, node, leafTypeDict, names):
        lines = []
        for child in node._members:
            lines.extend(
                self.Map(
                    "%s.%s" % (srcSDLVariable, self.CleanName(child[0])),
                    destVar + "." + self.CleanName(child[0]),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcSDLVariable, destVar, node, leafTypeDict, names):
        return self.MapSequence(srcSDLVariable, destVar, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcSDLVariable, destVar, node, leafTypeDict, names):
        lines = []
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.present == %d) {\n" % (self.maybeElse(childNo), srcSDLVariable, childNo))
            lines.extend(["    "+x for x in self.Map(
                         "%s.u.u%d.%s" % (srcSDLVariable, childNo, self.CleanName(child[0])),
                         destVar + (".u.%s" % self.CleanName(child[0])),
                         child[1],
                         leafTypeDict,
                         names)])
            lines.append("    %s.choice = OSS_%s_chosen;\n" % (destVar, self.CleanName(child[0])))
            lines.append("}\n")
        return lines

    def MapSequenceOf(self, srcSDLVariable, destVar, node, leafTypeDict, names):
        lines = []
        lines.append("{\n")
        uniqueId = self.UniqueID()
        lines.append("    int i%s;\n" % uniqueId)
        lines.append("    for(i%s=0; i%s<%s.length; i%s++) {\n" % (uniqueId, uniqueId, srcSDLVariable, uniqueId))
        lines.extend(["        " + x for x in self.Map(
                     "%s.cont[i%s]" % (srcSDLVariable, uniqueId),
                     "%s.value[i%s]" % (destVar, uniqueId),
                     node._containedType,
                     leafTypeDict,
                     names)])
        lines.append("    }\n")
        lines.append("    %s.count = %s.length;\n" % (destVar, srcSDLVariable))
        lines.append("}\n")
        self.DecreaseUniqueID()
        return lines

    def MapSetOf(self, unused_srcSDLVariable, unused_destVar, node, unused_leafTypeDict, unused_names):
        panic("The PragmaDev mapper does not support SETOF. Please use SEQUENCEOF instead (%s)" % node.Location())  # pragma: nocover


class FromASN1SCCtoRTDS(RecursiveMapper):
    def __init__(self):
        self.uniqueID = 0

    def UniqueID(self):
        self.uniqueID += 1
        return self.uniqueID

    def DecreaseUniqueID(self):
        self.uniqueID -= 1

    def MapInteger(self, srcVar, dstSDLVariable, _, __, ___):
        return ["%s = %s;\n" % (dstSDLVariable, srcVar)]

    def MapReal(self, srcVar, dstSDLVariable, _, __, ___):
        return ["%s = %s;\n" % (dstSDLVariable, srcVar)]

    def MapBoolean(self, srcVar, dstSDLVariable, _, __, ___):
        return ["%s = (%s)?TRUE:FALSE;\n" % (dstSDLVariable, srcVar)]

    def MapOctetString(self, srcVar, dstSDLVariable, node, _, __):
        #for i in xrange(0, node._range[-1]):
        #       lines.append("%s[%d] = %s->buf[%d];\n" % (dstSDLVariable, i, srcVar, i))
        lines = []
        limit = sourceSequenceLimit(node, srcVar)
        lines.append("{\n")
        lines.append("    int i;\n")
        lines.append("    for(i=0; i<%s; i++) {\n" % limit)
        lines.append("        %s.__string[i] = %s.arr[i];\n" % (dstSDLVariable, srcVar))
        lines.append("    }\n")
        lines.append("    while(i<%d) {\n" % node._range[-1])
        lines.append("        %s.__string[i]=0;\n" % dstSDLVariable)
        lines.append("        i++;\n")
        lines.append("    };\n")
        lines.append("    %s.__length = %s;\n" % (dstSDLVariable, limit))
        lines.append("}\n")
        return lines

    def MapEnumerated(self, srcVar, dstSDLVariable, _, __, ___):
        return ["%s = %s;\n" % (dstSDLVariable, srcVar)]

    def MapSequence(self, srcVar, dstSDLVariable, node, leafTypeDict, names):
        lines = []
        for child in node._members:
            lines.extend(
                self.Map(
                    srcVar + "." + self.CleanName(child[0]),
                    "%s.%s" % (dstSDLVariable, self.CleanName(child[0])),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcVar, dstSDLVariable, node, leafTypeDict, names):
        return self.MapSequence(srcVar, dstSDLVariable, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcVar, dstSDLVariable, node, leafTypeDict, names):
        lines = []
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.kind == %s) {\n" %
                         (self.maybeElse(childNo), srcVar, self.CleanName(child[2])))
            lines.extend(['    '+x for x in self.Map(
                         srcVar + ".u." + self.CleanName(child[0]),
                         "%s.__value.%s" % (dstSDLVariable, self.CleanName(child[0])),
                         child[1],
                         leafTypeDict,
                         names)])
            lines.append("    %s.present = %d;\n" % (dstSDLVariable, childNo))
            lines.append("}\n")
        return lines

    def MapSequenceOf(self, srcVar, dstSDLVariable, node, leafTypeDict, names):
        lines = []
        lines.append("{\n")
        uniqueId = self.UniqueID()
        limit = sourceSequenceLimit(node, srcVar)
        lines.append("    int i%s;\n" % uniqueId)
        lines.append("    %s.length = %s;\n" % (dstSDLVariable, limit))
        lines.append("    for(i%s=0; i%s<%s; i%s++) {\n" % (uniqueId, uniqueId, limit, uniqueId))
        lines.extend(["        " + x for x in self.Map(
                     srcVar + ".arr[i%s]" % uniqueId,
                     "%s.elements[i%s]" % (dstSDLVariable, uniqueId),
                     node._containedType,
                     leafTypeDict,
                     names)])
        lines.append("    }\n")
        lines.append("}\n")
        self.DecreaseUniqueID()
        return lines

    def MapSetOf(self, unused_srcVar, unused_dstSDLVariable, node, unused_leafTypeDict, unused_names):
        panic("The PragmaDev mapper does not support SETOF. Please use SEQUENCEOF instead (%s)" % node.Location())  # pragma: nocover


class FromOSStoRTDS(RecursiveMapper):
    def __init__(self):
        self.uniqueID = 0

    def UniqueID(self):
        self.uniqueID += 1
        return self.uniqueID

    def DecreaseUniqueID(self):
        self.uniqueID -= 1

    def MapInteger(self, srcVar, dstSDLVariable, _, __, ___):
        return ["%s = %s;\n" % (dstSDLVariable, srcVar)]

    def MapReal(self, srcVar, dstSDLVariable, _, __, ___):
        return ["%s = %s;\n" % (dstSDLVariable, srcVar)]

    def MapBoolean(self, srcVar, dstSDLVariable, _, __, ___):
        return ["%s = (%s)?SDL_TRUE:SDL_FALSE;\n" % (dstSDLVariable, srcVar)]

    def MapOctetString(self, srcVar, dstSDLVariable, node, _, __):
        lines = []
        #for i in xrange(0, node._range[-1]):
        #       lines.append("%s[%d] = %s->buf[%d];\n" % (dstSDLVariable, i, srcVar, i))
        lines.append("{\n")
        lines.append("    int i;\n")
        lines.append("    for(i=0; i<%s.length; i++) {\n" % srcVar)
        lines.append("        unsigned char value = %s.value[i];\n" % srcVar)
        lines.append("        %s.cont[i].cont[0] = value & 128;\n" % (dstSDLVariable))
        lines.append("        %s.cont[i].cont[1] = value & 64;\n" % (dstSDLVariable))
        lines.append("        %s.cont[i].cont[2] = value & 32;\n" % (dstSDLVariable))
        lines.append("        %s.cont[i].cont[3] = value & 16;\n" % (dstSDLVariable))
        lines.append("        %s.cont[i].cont[4] = value & 8;\n" % (dstSDLVariable))
        lines.append("        %s.cont[i].cont[5] = value & 4;\n" % (dstSDLVariable))
        lines.append("        %s.cont[i].cont[6] = value & 2;\n" % (dstSDLVariable))
        lines.append("        %s.cont[i].cont[7] = value & 1;\n" % (dstSDLVariable))
        lines.append("        %s.cont[i].length = 8;\n" % (dstSDLVariable))
        lines.append("    }\n")
        lines.append("    while(i<%d) {\n" % node._range[-1])
        lines.append("        %s.cont[i].cont[0]=0;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].cont[1]=0;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].cont[2]=0;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].cont[3]=0;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].cont[4]=0;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].cont[5]=0;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].cont[6]=0;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].cont[7]=0;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].length=0;\n" % dstSDLVariable)
        lines.append("        i++;\n")
        lines.append("    };\n")
        lines.append("    %s.length = %s.length;\n" % (dstSDLVariable, srcVar))
        lines.append("}\n")
        return lines

    def MapEnumerated(self, srcVar, dstSDLVariable, _, __, ___):
        return ["%s = %s;\n" % (dstSDLVariable, srcVar)]

    def MapSequence(self, srcVar, dstSDLVariable, node, leafTypeDict, names):
        lines = []
        for child in node._members:
            lines.extend(
                self.Map(
                    srcVar + "." + self.CleanName(child[0]),
                    "%s.%s" % (dstSDLVariable, self.CleanName(child[0])),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcVar, dstSDLVariable, node, leafTypeDict, names):
        return self.MapSequence(srcVar, dstSDLVariable, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcVar, dstSDLVariable, node, leafTypeDict, names):
        lines = []
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.choice == OSS_%s_chosen) {\n" %
                         (self.maybeElse(childNo), srcVar, self.CleanName(child[0])))
            lines.extend(['    '+x for x in self.Map(
                         srcVar + ".u." + self.CleanName(child[0]),
                         "%s.u.u%d.%s" % (dstSDLVariable, childNo, self.CleanName(child[0])),
                         child[1],
                         leafTypeDict,
                         names)])
            lines.append("    %s.present = %d;\n" % (dstSDLVariable, childNo))
            lines.append("}\n")
        return lines

    def MapSequenceOf(self, srcVar, dstSDLVariable, node, leafTypeDict, names):
        lines = []
        lines.append("{\n")
        uniqueId = self.UniqueID()
        lines.append("    int i%s;\n" % uniqueId)
        lines.append("    %s.length = %s.count;\n" % (dstSDLVariable, srcVar))
        lines.append("    for(i%s=0; i%s<%s.count; i%s++) {\n" % (uniqueId, uniqueId, srcVar, uniqueId))
        lines.extend(["        " + x for x in self.Map(
                     srcVar + ".value[i%s]" % uniqueId,
                     "%s.cont[i%s]" % (dstSDLVariable, uniqueId),
                     node._containedType,
                     leafTypeDict,
                     names)])
        lines.append("    }\n")
        lines.append("}\n")
        self.DecreaseUniqueID()
        return lines

    def MapSetOf(self, unused_srcVar, unused_dstSDLVariable, node, unused_leafTypeDict, unused_names):
        panic("The PragmaDev mapper does not support SETOF. Please use SEQUENCEOF instead (%s)" % node.Location())  # pragma: nocover


class RTDS_GlueGenerator(ASynchronousToolGlueGenerator):
    def __init__(self):
        ASynchronousToolGlueGenerator.__init__(self)
        self.FromRTDSToASN1SCC = FromRTDSToASN1SCC()
        self.FromRTDSToOSS = FromRTDSToOSS()
        self.FromASN1SCCtoRTDS = FromASN1SCCtoRTDS()
        self.FromOSStoRTDS = FromOSStoRTDS()

    def Version(self):
        print "Code generator: " + "$Id: rtds_B_mapper.py 2390 2012-07-19 12:39:17Z ttsiodras $"

    def HeadersOnStartup(self, unused_asnFile, unused_outputDir, unused_maybeFVname):
        self.C_HeaderFile.write("#include <assert.h>\n\n")
        self.C_HeaderFile.write("#include \"%s.h\"\n" % self.asn_name)
        self.C_HeaderFile.write("#include \"RTDS_gen.h\"\n\n")
        self.C_HeaderFile.write("#include \"RTDSdataView.h\"\n\n")

    def Encoder(self, nodeTypename, node, leafTypeDict, names, encoding):
        if encoding.lower() in ["uper", "acn"]:
            return
        fileOutHeader = self.C_HeaderFile
        fileOutSource = self.C_SourceFile
        isPointer = True
        if isinstance(node, AsnBasicNode) or isinstance(node, AsnEnumerated):
            isPointer = False
        fileOutHeader.write(
            "void Convert_%s_from_RTDS_to_ASN1SCC(asn1Scc%s *ptrASN1SCC, %s %sRTDS);\n" %
            (self.CleanNameAsToolWants(nodeTypename),
            self.CleanNameAsToolWants(nodeTypename),
            self.CleanNameAsToolWants(nodeTypename),
            "*" if isPointer else ""))
        fileOutSource.write(
            "void Convert_%s_from_RTDS_to_ASN1SCC(asn1Scc%s *ptrASN1SCC, %s %sRTDS)\n{\n" %
            (self.CleanNameAsToolWants(nodeTypename),
            self.CleanNameAsToolWants(nodeTypename),
            self.CleanNameAsToolWants(nodeTypename),
            "*" if isPointer else ""))

        # Write the mapping code for the message
        if self.useOSS:
            lines = self.FromRTDSToOSS.Map(
                "(%sRTDS)" % ("*" if isPointer else ""),
                "(*ptrASN1SCC)",
                node,
                leafTypeDict,
                names)
        else:
            lines = self.FromRTDSToASN1SCC.Map(
                "(%sRTDS)" % ("*" if isPointer else ""),
                "(*ptrASN1SCC)",
                node,
                leafTypeDict,
                names)

        lines = ["    "+x.rstrip() for x in lines]
        fileOutSource.write("\n".join(lines))
        fileOutSource.write("\n}\n\n")

    def Decoder(self, nodeTypename, node, leafTypeDict, names, encoding):
        if encoding.lower() in ["uper", "acn"]:
            return
        fileOutHeader = self.C_HeaderFile
        fileOutSource = self.C_SourceFile
        fileOutHeader.write(
            "void Convert_%s_from_ASN1SCC_to_RTDS(%s *ptrRTDS, const asn1Scc%s *ptrASN1SCC);\n" %
            (self.CleanNameAsToolWants(nodeTypename),
            self.CleanNameAsToolWants(nodeTypename),
            self.CleanNameAsToolWants(nodeTypename)))

        fileOutSource.write(
            "void Convert_%s_from_ASN1SCC_to_RTDS(%s *ptrRTDS, const asn1Scc%s *ptrASN1SCC)\n{\n" %
            (self.CleanNameAsToolWants(nodeTypename),
            self.CleanNameAsToolWants(nodeTypename),
            self.CleanNameAsToolWants(nodeTypename)))

        if self.useOSS:
            lines = self.FromOSStoRTDS.Map(
                "(*ptrASN1SCC)",
                "(*ptrRTDS)",
                node,
                leafTypeDict,
                names)
        else:
            lines = self.FromASN1SCCtoRTDS.Map(
                "(*ptrASN1SCC)",
                "(*ptrRTDS)",
                node,
                leafTypeDict,
                names)

        lines = ["    "+x.rstrip() for x in lines]
        fileOutSource.write("\n".join(lines))
        fileOutSource.write("\n}\n\n")


def OnStartup(modelingLanguage, asnFile, outputDir, maybeFVname, useOSS):
    global rtdsBackend
    rtdsBackend = RTDS_GlueGenerator()
    rtdsBackend.OnStartup(modelingLanguage, asnFile, outputDir, maybeFVname, useOSS)
    global cBackend
    cBackend = c_B_mapper.C_GlueGenerator()
    cBackend.OnStartup("C", asnFile, outputDir, maybeFVname, useOSS)


def OnBasic(nodeTypename, node, leafTypeDict, names):
    rtdsBackend.OnBasic(nodeTypename, node, leafTypeDict, names)
    cBackend.OnBasic(nodeTypename, node, leafTypeDict, names)


def OnSequence(nodeTypename, node, leafTypeDict, names):
    rtdsBackend.OnSequence(nodeTypename, node, leafTypeDict, names)
    cBackend.OnSequence(nodeTypename, node, leafTypeDict, names)


def OnSet(nodeTypename, node, leafTypeDict, names):
    rtdsBackend.OnSet(nodeTypename, node, leafTypeDict, names)  # pragma: nocover
    cBackend.OnSet(nodeTypename, node, leafTypeDict, names)  # pragma: nocover


def OnEnumerated(nodeTypename, node, leafTypeDict, names):
    rtdsBackend.OnEnumerated(nodeTypename, node, leafTypeDict, names)
    cBackend.OnEnumerated(nodeTypename, node, leafTypeDict, names)


def OnSequenceOf(nodeTypename, node, leafTypeDict, names):
    rtdsBackend.OnSequenceOf(nodeTypename, node, leafTypeDict, names)
    cBackend.OnSequenceOf(nodeTypename, node, leafTypeDict, names)


def OnSetOf(nodeTypename, node, leafTypeDict, names):
    rtdsBackend.OnSetOf(nodeTypename, node, leafTypeDict, names)  # pragma: nocover
    cBackend.OnSetOf(nodeTypename, node, leafTypeDict, names)  # pragma: nocover


def OnChoice(nodeTypename, node, leafTypeDict, names):
    rtdsBackend.OnChoice(nodeTypename, node, leafTypeDict, names)
    cBackend.OnChoice(nodeTypename, node, leafTypeDict, names)


def OnShutdown(modelingLanguage, asnFile, maybeFVname):
    rtdsBackend.OnShutdown(modelingLanguage, asnFile, maybeFVname)
    cBackend.OnShutdown("C", asnFile, maybeFVname)
