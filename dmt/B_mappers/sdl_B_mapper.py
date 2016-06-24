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
This is the code generator for the ObjectGeode code mappers.
This backend is called by aadl2glueC, when an OG subprogram
is identified in the input concurrency view.

All the ASSERT supported encodings are handled by this code
in the form of generated C macros:

  DECLARE_Typename
  DEFINE_Typename
  ENCODE_UPER_Typename     (uses Semantix's asn1scc)
  ENCODE_ACN_Typename     (uses Semantix's asn1scc)
  ENCODE_NATIVE_Typename   (uses memory dumps)
  DECODE_UPER_Typename     (uses Semantix's asn1scc)
  DECODE_ACN_Typename     (uses Semantix's asn1scc)
  DECODE_NATIVE_Typename   (uses memory dumps)

The macros are called from the wrapping layer, created by
Maxime Perottin's buildSupport.

Implementation notes: OG is by far the most complex case;
It is used to model asynchronous processes (SDL)...

The following are done by the buildSupport prior to this backend:

vm_if.c :

 For each Provided Interface which is provided by the modeled APLC,
 a "bridge" function must be created inside this file. This function
 will be in one of two forms:
 (a) if the PI has no associated PARAMETER with it, then this function
     is simply doing
     (I)   G2S_OUTPUT(...);
     (II)  sdl_loop_FVNAME();

 (b) if the PI has an associated PARAMETER with it, then this function
     must
     (I)   decode the ASN.1 message (incoming arguments: pointer,length)
     (II)  place the decoded values in the appropriate ObjectGeode generated
           global variable (for this PI)
     (III) G2S_OUTPUT(...);
     (IV)  sdl_loop_FVNAME();

hpostdef.h :

  OG-related definitions: for each type used by this APLC, a call to

    DEFINE_ASN1TYPENAME(name_of_variable)

  must be issued, to reserve space for the variable. The macro knows
  (by way of this code generator) what size to reserve to accomodate
  the maximum configuration of this message.

  Also, for each Required Interface used by the modeled APLC, this header
  file must also declare a C MACRO:
         #define riname(param1, param2, ...)
  which will
     (I)   encode all the input data from the input params, via the
           ENCODE_ macros, into the reserved spaces (the DEFINE_ASN1TYPENAME
           ones)
     (II)  call the vm callback to access the RI (vm_fvname_riname)
     (III) decode all the output data from the output params, via the
           DECODE_ macros.
  This MACRO will be called by the ObjectGeode generated code whenever the
  RI is to be called.

hpredef.h :

 Contains the prototypes (extern declarations) of the vm callbacks.
'''

from ..commonPy.asnAST import isSequenceVariable, sourceSequenceLimit, AsnInt, AsnBool, AsnReal, AsnEnumerated

from ..commonPy.recursiveMapper import RecursiveMapper
from .asynchronousTool import ASynchronousToolGlueGenerator

isAsynchronous = True
ogBackend = None


def Version():
    print(("Code generator: " + "$Id: og_B_mapper.py 2390 2012-07-19 12:39:17Z ttsiodras $"))


# noinspection PyListCreation
class FromObjectGeodeToASN1SCC(RecursiveMapper):
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
        return ["%s = (%s==SDL_TRUE)?0xff:0;\n" % (destVar, srcSDLVariable)]

    def MapOctetString(self, srcSDLVariable, destVar, node, __, ___):
        lines = []
        lines.append("{\n")
        lines.append("    int i;\n")
        lines.append("    for(i=0; i<%s.length; i++) {\n" % srcSDLVariable)
        lines.append("        unsigned char value = 0;\n")
        lines.append("        if(%s.cont[i].cont[0]) value |= 128;\n" % srcSDLVariable)
        lines.append("        if(%s.cont[i].cont[1]) value |= 64;\n" % srcSDLVariable)
        lines.append("        if(%s.cont[i].cont[2]) value |= 32;\n" % srcSDLVariable)
        lines.append("        if(%s.cont[i].cont[3]) value |= 16;\n" % srcSDLVariable)
        lines.append("        if(%s.cont[i].cont[4]) value |= 8;\n" % srcSDLVariable)
        lines.append("        if(%s.cont[i].cont[5]) value |= 4;\n" % srcSDLVariable)
        lines.append("        if(%s.cont[i].cont[6]) value |= 2;\n" % srcSDLVariable)
        lines.append("        if(%s.cont[i].cont[7]) value |= 1;\n" % srcSDLVariable)
        lines.append("        %s.arr[i] = value;\n" % destVar)
        lines.append("    }\n")
        # for i in xrange(0, node._range[-1]):
        #     lines.append("    placeHolder[%d] = %s[%d];\n" % (i, srcSDLVariable, i))
        if isSequenceVariable(node):
            lines.append("    %s.nCount = %s.length;\n" % (destVar, srcSDLVariable))
        lines.append("}\n")
        return lines

    def MapEnumerated(self, srcSDLVariable, destVar, _, __, ___):
        return ["%s = %s;\n" % (destVar, srcSDLVariable)]

    def MapSequence(self, srcSDLVariable, destVar, node, leafTypeDict, names):
        lines = []
        for child in node._members:
            lines.extend(
                self.Map(
                    "%s.fd_%s" % (srcSDLVariable, self.CleanName(child[0]).lower()),
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
            lines.extend(
                ["    " + x
                 for x in self.Map(
                     "%s.u.u%d.fd_%s" % (srcSDLVariable, childNo, self.CleanName(child[0]).lower()),
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
        lines.extend(
            ["        " + x
             for x in self.Map(
                 "%s.cont[i%s]" % (srcSDLVariable, uniqueId),
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

    def MapSetOf(self, srcSDLVariable, destVar, node, leafTypeDict, names):
        return self.MapSequenceOf(srcSDLVariable, destVar, node, leafTypeDict, names)  # pragma: nocover


# noinspection PyListCreation
class FromObjectGeodeToOSS(RecursiveMapper):
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
        lines.append("        unsigned char value = 0;\n")
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
        # for i in xrange(0, node._range[-1]):
        #     lines.append("    placeHolder[%d] = %s[%d];\n" % (i, srcSDLVariable, i))
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
                    "%s.fd_%s" % (srcSDLVariable, self.CleanName(child[0]).lower()),
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
            lines.extend(
                ["    " + x
                 for x in self.Map(
                     "%s.u.u%d.fd_%s" % (srcSDLVariable, childNo, self.CleanName(child[0]).lower()),
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
        lines.extend(
            ["        " + x
             for x in self.Map(
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

    def MapSetOf(self, srcSDLVariable, destVar, node, leafTypeDict, names):
        return self.MapSequenceOf(srcSDLVariable, destVar, node, leafTypeDict, names)  # pragma: nocover


# noinspection PyListCreation
class FromASN1SCCtoObjectGeode(RecursiveMapper):
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
        # for i in xrange(0, node._range[-1]):
        #     lines.append("%s[%d] = %s->buf[%d];\n" % (dstSDLVariable, i, srcVar, i))
        lines = []
        limit = sourceSequenceLimit(node, srcVar)
        lines.append("{\n")
        lines.append("    int i;\n")
        lines.append("    for(i=0; i<%s; i++) {\n" % limit)
        lines.append("        unsigned char value = %s.arr[i];\n" % srcVar)
        lines.append("        %s.cont[i].cont[0] = (value & 128) >> 7;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].cont[1] = (value & 64) >> 6;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].cont[2] = (value & 32) >> 5;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].cont[3] = (value & 16) >> 4;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].cont[4] = (value & 8) >> 3;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].cont[5] = (value & 4) >> 2;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].cont[6] = (value & 2) >> 1;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].cont[7] = value & 1;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].length = 8;\n" % dstSDLVariable)
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
        lines.append("    %s.length = %s;\n" % (dstSDLVariable, limit))
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
                    "%s.fd_%s" % (dstSDLVariable, self.CleanName(child[0]).lower()),
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
            lines.extend(
                ['    ' + x
                 for x in self.Map(
                     srcVar + ".u." + self.CleanName(child[0]),
                     "%s.u.u%d.fd_%s" % (dstSDLVariable, childNo, self.CleanName(child[0]).lower()),
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
        limit = sourceSequenceLimit(node, srcVar)
        lines.append("    %s.length = %s;\n" % (dstSDLVariable, limit))
        lines.append("    for(i%s=0; i%s<%s; i%s++) {\n" % (uniqueId, uniqueId, limit, uniqueId))
        lines.extend(
            ["        " + x
             for x in self.Map(
                 srcVar + ".arr[i%s]" % uniqueId,
                 "%s.cont[i%s]" % (dstSDLVariable, uniqueId),
                 node._containedType,
                 leafTypeDict,
                 names)])
        lines.append("    }\n")
        lines.append("}\n")
        self.DecreaseUniqueID()
        return lines

    def MapSetOf(self, srcVar, dstSDLVariable, node, leafTypeDict, names):
        return self.MapSequenceOf(srcVar, dstSDLVariable, node, leafTypeDict, names)  # pragma: nocover


# noinspection PyListCreation
class FromOSStoObjectGeode(RecursiveMapper):
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
        # for i in xrange(0, node._range[-1]):
        #     lines.append("%s[%d] = %s->buf[%d];\n" % (dstSDLVariable, i, srcVar, i))
        lines.append("{\n")
        lines.append("    int i;\n")
        lines.append("    for(i=0; i<%s.length; i++) {\n" % srcVar)
        lines.append("        unsigned char value = %s.value[i];\n" % srcVar)
        lines.append("        %s.cont[i].cont[0] = value & 128;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].cont[1] = value & 64;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].cont[2] = value & 32;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].cont[3] = value & 16;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].cont[4] = value & 8;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].cont[5] = value & 4;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].cont[6] = value & 2;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].cont[7] = value & 1;\n" % dstSDLVariable)
        lines.append("        %s.cont[i].length = 8;\n" % dstSDLVariable)
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
                    "%s.fd_%s" % (dstSDLVariable, self.CleanName(child[0]).lower()),
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
            lines.extend(
                ['    ' + x
                 for x in self.Map(
                     srcVar + ".u." + self.CleanName(child[0]),
                     "%s.u.u%d.fd_%s" % (dstSDLVariable, childNo, self.CleanName(child[0]).lower()),
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
        lines.extend(
            ["        " + x
             for x in self.Map(
                 srcVar + ".value[i%s]" % uniqueId,
                 "%s.cont[i%s]" % (dstSDLVariable, uniqueId),
                 node._containedType,
                 leafTypeDict,
                 names)])
        lines.append("    }\n")
        lines.append("}\n")
        self.DecreaseUniqueID()
        return lines

    def MapSetOf(self, srcVar, dstSDLVariable, node, leafTypeDict, names):
        return self.MapSequenceOf(srcVar, dstSDLVariable, node, leafTypeDict, names)  # pragma: nocover


class OG_GlueGenerator(ASynchronousToolGlueGenerator):
    def __init__(self):
        ASynchronousToolGlueGenerator.__init__(self)
        self.FromObjectGeodeToASN1SCC = FromObjectGeodeToASN1SCC()
        self.FromObjectGeodeToOSS = FromObjectGeodeToOSS()
        self.FromASN1SCCtoObjectGeode = FromASN1SCCtoObjectGeode()
        self.FromOSStoObjectGeode = FromOSStoObjectGeode()
        self.declarations = {}

    def Version(self):
        print(("Code generator: " + "$Id: og_B_mapper.py 2390 2012-07-19 12:39:17Z ttsiodras $"))  # pragma: no cover

    def HeadersOnStartup(self, unused_asnFile, unused_outputDir, unused_maybeFVname):
        self.C_HeaderFile.write("#include <assert.h>\n\n")
        if self.useOSS:
            self.C_HeaderFile.write("#include \"%s.oss.h\" // OSS generated\n\n" % self.asn_name)
            self.C_HeaderFile.write("#include \"%s.h\" // Space certified compiler (only for REQUIRED_BYTES_FOR_ENCODING)\n\n" % self.asn_name)
            self.C_HeaderFile.write("extern OssGlobal *g_world;\n\n")
        else:
            self.C_HeaderFile.write("#include \"%s.h\" // Space certified compiler generated\n\n" % self.asn_name)
        self.C_HeaderFile.write("#define ASSERT_MAX(a, b)  (((a) > (b)) ? (a) : (b))\n\n")
        self.C_HeaderFile.write("#define ASSERT_MAX3(a, b, c) ((ASSERT_MAX(a,b)<c) ? (c) : (ASSERT_MAX(a,b)))\n\n")
        self.C_HeaderFile.write("#ifdef __linux__\n")
        self.C_HeaderFile.write("#define CLEAR_MEM(ptr, size)  (void)memset(ptr, 0, size)\n")
        self.C_HeaderFile.write("#else\n")
        self.C_HeaderFile.write("#define CLEAR_MEM(ptr, size)\n")
        self.C_HeaderFile.write("#endif\n\n")

    def Encoder(self, nodeTypename, node, leafTypeDict, names, encoding):
        fileOutHeader = self.C_HeaderFile

        # This method also generates the DECLARE and DEFINE macros.
        if nodeTypename not in self.declarations:
            self.declarations[nodeTypename] = 1
            fileOutHeader.write("#define DECLARE_%s(varName) \\\n" % self.CleanNameAsToolWants(nodeTypename))
            fileOutHeader.write("    extern char varName[ASSERT_MAX3(asn1Scc%s_REQUIRED_BYTES_FOR_ENCODING, asn1Scc%s_REQUIRED_BYTES_FOR_ACN_ENCODING, sizeof(asn1Scc%s))];\\\n" %
                                (self.CleanNameAsToolWants(nodeTypename),
                                 self.CleanNameAsToolWants(nodeTypename),
                                 self.CleanNameAsToolWants(nodeTypename)))
            fileOutHeader.write("    extern int varName##_len;\\\n\\\n\n")

            fileOutHeader.write("#define DEFINE_%s(varName) \\\n" %
                                self.CleanNameAsToolWants(nodeTypename))
            fileOutHeader.write("    char varName[ASSERT_MAX3(asn1Scc%s_REQUIRED_BYTES_FOR_ENCODING, asn1Scc%s_REQUIRED_BYTES_FOR_ACN_ENCODING, sizeof(asn1Scc%s))];\\\n" %
                                (self.CleanNameAsToolWants(nodeTypename),
                                 self.CleanNameAsToolWants(nodeTypename),
                                 self.CleanNameAsToolWants(nodeTypename)))
            fileOutHeader.write("    int varName##_len;\\\n\\\n\n")

        # Create the macro that does the encoding
        fileOutHeader.write(
            "#define ENCODE_%s_%s(varName, param1) {\\\n" %
            ({"uper": "UPER", "native": "NATIVE", "acn": "ACN"}[encoding.lower()], self.CleanNameAsToolWants(nodeTypename)))

        if self.useOSS and encoding.lower() == "uper":
            fileOutHeader.write("    STATIC OssBuf strm;\\\n")
            fileOutHeader.write("    STATIC OSS_%s var_%s;\\\n" %
                                (self.CleanNameAsToolWants(nodeTypename),
                                 self.CleanNameAsToolWants(nodeTypename)))
            fileOutHeader.write("\\\n    strm.value=NULL;\\\n")
            fileOutHeader.write("    strm.length = 0;\\\n")
        elif encoding.lower() in ["uper", "acn"]:
            fileOutHeader.write("    int errorCode = 314159;\\\n")
            fileOutHeader.write("    STATIC BitStream strm;\\\n")
            fileOutHeader.write(
                "    STATIC asn1Scc%s var_%s;\\\n" %
                (self.CleanNameAsToolWants(nodeTypename), self.CleanNameAsToolWants(nodeTypename)))
            fileOutHeader.write(
                "\\\n    BitStream_Init(&strm, varName, asn1Scc%s_REQUIRED_BYTES_FOR_%sENCODING);\\\n" %
                (self.CleanNameAsToolWants(nodeTypename), "ACN_" if encoding.lower() == "acn" else ""))
        else:
            fileOutHeader.write(
                "    STATIC asn1Scc%s var_%s;\\\n" %
                (self.CleanNameAsToolWants(nodeTypename), self.CleanNameAsToolWants(nodeTypename)))
            fileOutHeader.write(
                "    CLEAR_MEM(&var_%s, sizeof(var_%s));\\\n" %
                (self.CleanNameAsToolWants(nodeTypename), self.CleanNameAsToolWants(nodeTypename)))

        # Write the mapping code for the message
        if self.useOSS and encoding.lower() == "uper":
            lines = self.FromObjectGeodeToOSS.Map(
                # (isinstance(node, AsnInt) or isinstance(node, AsnBool)) and "(param1)" or "(*(param1))",
                "(param1)",
                "var_" + self.CleanNameAsToolWants(nodeTypename),
                node,
                leafTypeDict,
                names)
        else:
            lines = self.FromObjectGeodeToASN1SCC.Map(
                # (isinstance(node, AsnInt) or isinstance(node, AsnBool)) and "(param1)" or "(*(param1))",
                "(param1)",
                "var_" + self.CleanNameAsToolWants(nodeTypename),
                node,
                leafTypeDict,
                names)

        lines = ["    " + x.rstrip() + "\\" for x in lines]
        fileOutHeader.write("\n".join(lines))

        # Call the encoder
        if self.useOSS and encoding.lower() == "uper":
            fileOutHeader.write(
                "\n    if (0 != ossEncode(g_world, OSS_%s_PDU, &var_%s, &strm)) {\\\n" %
                (self.CleanNameAsToolWants(nodeTypename), self.CleanNameAsToolWants(nodeTypename)))
            fileOutHeader.write(
                '\tfprintf(stderr, "Could not encode %s (at %%s, %%d), error message was %%s\\n", __FILE__, __LINE__, ossGetErrMsg(g_world));\\\n' %
                nodeTypename)
            fileOutHeader.write("        varName##_len = -1;\\\n")
            fileOutHeader.write("    } else {\\\n")
            fileOutHeader.write("        memcpy(&varName[0], strm.value, strm.length);\\\n")
            fileOutHeader.write("        ossFreeBuf(g_world, strm.value);\\\n")
            fileOutHeader.write("        varName##_len = strm.length;\\\n")
            fileOutHeader.write("    }\\\n")
            fileOutHeader.write("}\n\n")
        elif encoding.lower() in ["uper", "acn"]:
            fileOutHeader.write(
                "\n    if (asn1Scc%s_%sEncode(&var_%s, &strm, &errorCode, TRUE) == FALSE) {\\\n" %
                (self.CleanNameAsToolWants(nodeTypename),
                 "ACN_" if encoding.lower() == "acn" else "",
                 self.CleanNameAsToolWants(nodeTypename)))
            fileOutHeader.write(
                '\tfprintf(stderr, "Could not encode %s (at %%s, %%d), error code was %%d\\n", __FILE__, __LINE__, errorCode);\\\n' %
                nodeTypename)
            fileOutHeader.write("        varName##_len = -1;\\\n")
            fileOutHeader.write("    } else {\\\n")
            fileOutHeader.write("        varName##_len = BitStream_GetLength(&strm);\\\n")
            fileOutHeader.write("    }\\\n")
            fileOutHeader.write("}\n\n")
        else:
            fileOutHeader.write(
                "\n    memcpy(&varName[0], &var_%s, sizeof(asn1Scc%s));\\\n" %
                (self.CleanNameAsToolWants(nodeTypename), self.CleanNameAsToolWants(nodeTypename)))
            fileOutHeader.write(
                "    varName##_len = sizeof(asn1Scc%s);\\\n" %
                self.CleanNameAsToolWants(nodeTypename))
            fileOutHeader.write("}\n\n")

        coding = {"uper": "UPER", "native": "NATIVE", "acn": "ACN"}[encoding.lower()]
        if isinstance(node, AsnInt) or isinstance(node, AsnBool) or isinstance(node, AsnReal) or isinstance(node, AsnEnumerated):
            fileOutHeader.write(
                "#define ENCODE_SYNC_%s_%s(varName, param1) ENCODE_%s_%s(varName, param1)\n\n" %
                (coding,
                 self.CleanNameAsToolWants(nodeTypename),
                 coding,
                 self.CleanNameAsToolWants(nodeTypename)))
            fileOutHeader.write(
                "#define ENCODE_ASYNC_%s_%s(varName, param1) ENCODE_%s_%s(varName, param1)\n\n" %
                (coding,
                 self.CleanNameAsToolWants(nodeTypename),
                 coding,
                 self.CleanNameAsToolWants(nodeTypename)))
        else:
            fileOutHeader.write(
                "#define ENCODE_SYNC_%s_%s(varName, param1) ENCODE_%s_%s(varName, param1)\n\n" %
                (coding,
                 self.CleanNameAsToolWants(nodeTypename),
                 coding,
                 self.CleanNameAsToolWants(nodeTypename)))
            fileOutHeader.write(
                "#define ENCODE_ASYNC_%s_%s(varName, param1) ENCODE_%s_%s(varName, (*param1))\n\n" %
                (coding,
                 self.CleanNameAsToolWants(nodeTypename),
                 coding,
                 self.CleanNameAsToolWants(nodeTypename)))

    def Decoder(self, nodeTypename, node, leafTypeDict, names, encoding):
        fileOutHeader = self.C_HeaderFile
        fileOutHeader.write(
            "#define DECODE_%s_%s(pBuffer, iBufferSize, pSdlVar) {\\\n" %
            ({"uper": "UPER", "native": "NATIVE", "acn": "ACN"}[encoding.lower()], self.CleanNameAsToolWants(nodeTypename)))

        if self.useOSS and encoding.lower() == "uper":
            fileOutHeader.write("    int pdutype = OSS_%s_PDU;\\\n" % self.CleanNameAsToolWants(nodeTypename))
            fileOutHeader.write("    STATIC OssBuf strm;\\\n")
            fileOutHeader.write(
                "    OSS_%s *pVar_%s = NULL;\\\n" %
                (self.CleanNameAsToolWants(nodeTypename), self.CleanNameAsToolWants(nodeTypename)))
            fileOutHeader.write("    strm.value = pBuffer;\\\n")
            fileOutHeader.write("    strm.length = iBufferSize;\\\n")
            fileOutHeader.write(
                "    if (0 == ossDecode(g_world, &pdutype, &strm, (void**)&pVar_%s)) {\\\n" %
                (self.CleanNameAsToolWants(nodeTypename)))
        elif encoding.lower() in ["uper", "acn"]:
            fileOutHeader.write("    int errorCode = 314159;\\\n")
            fileOutHeader.write("    STATIC BitStream strm;\\\n")
            fileOutHeader.write(
                "    STATIC asn1Scc%s var_%s;\\\n" %
                (self.CleanNameAsToolWants(nodeTypename), self.CleanNameAsToolWants(nodeTypename)))
            fileOutHeader.write("    BitStream_AttachBuffer(&strm, pBuffer, iBufferSize);\\\n")
            fileOutHeader.write(
                "    if(asn1Scc%s_%sDecode(&var_%s, &strm, &errorCode)) {\\\n" %
                (self.CleanNameAsToolWants(nodeTypename), "ACN_" if encoding.lower() == "acn" else "", self.CleanNameAsToolWants(nodeTypename)))
        else:
            fileOutHeader.write(
                "    STATIC asn1Scc%s var_%s;\\\n" %
                (self.CleanNameAsToolWants(nodeTypename), self.CleanNameAsToolWants(nodeTypename)))
            fileOutHeader.write(
                "    assert(iBufferSize == sizeof(asn1Scc%s));\\\n" %
                self.CleanNameAsToolWants(nodeTypename))
            fileOutHeader.write(
                "    memcpy(&var_%s, pBuffer, sizeof(asn1Scc%s));\\\n" %
                (self.CleanNameAsToolWants(nodeTypename), self.CleanNameAsToolWants(nodeTypename)))
            fileOutHeader.write("    {\\\n")

        # dstSDLVariable = (isinstance(node, AsnInt) or isinstance(node, AsnBool)) and "(pSdlVar)" or "(*(pSdlVar))"
        # dstSDLVariable = (isinstance(node, AsnInt)) and "(pSdlVar)" or "(*(pSdlVar))"
        dstSDLVariable = "(*(pSdlVar))"

        if self.useOSS and encoding.lower() == "uper":
            lines = self.FromOSStoObjectGeode.Map(
                "(*pVar_" + self.CleanNameAsToolWants(nodeTypename) + ")",
                dstSDLVariable,
                node,
                leafTypeDict,
                names)
        else:
            lines = self.FromASN1SCCtoObjectGeode.Map(
                "var_" + self.CleanNameAsToolWants(nodeTypename),
                dstSDLVariable,
                node,
                leafTypeDict,
                names)

        lines = ["        " + x.rstrip() + "\\" for x in lines]
        fileOutHeader.write("\n".join(lines))

        if self.useOSS and encoding.lower() == "uper":
            fileOutHeader.write("\n        ossFreeBuf(g_world, pVar_%s);\\\n" % self.CleanNameAsToolWants(nodeTypename))
            fileOutHeader.write("        /*return 0*/;\\\n")
            fileOutHeader.write("    } else {\\\n")
            fileOutHeader.write('        fprintf(stderr, "Could not decode %s\\n");\\\n' % (self.CleanNameAsToolWants(nodeTypename)))
            fileOutHeader.write("        /*return -1*/;\\\n")
            fileOutHeader.write("    }\\\n")
            fileOutHeader.write("}\n\n")
        elif encoding.lower() in ["uper", "acn"]:
            fileOutHeader.write("\n        /*return 0*/;\\\n")
            fileOutHeader.write("    } else {\\\n")
            fileOutHeader.write('\tfprintf(stderr, "Could not decode %s\\n");\\\n' % (self.CleanNameAsToolWants(nodeTypename)))
            fileOutHeader.write("        /*return -1*/;\\\n")
            fileOutHeader.write("    }\\\n")
            fileOutHeader.write("}\n\n")
        else:
            fileOutHeader.write("\n        /*return 0*/;\\\n")
            fileOutHeader.write("    }\\\n")
            fileOutHeader.write("}\n\n")

        # fileOutHeader.write(
        #     "#define DECODE_%s(pBuffer, iBufferSize, pSdlVar) DECODE_UPER_%s(pBuffer, iBufferSize, pSdlVar)\n\n" %
        #     (self.CleanNameAsToolWants(nodeTypename), self.CleanNameAsToolWants(nodeTypename)))


def OnStartup(modelingLanguage, asnFile, outputDir, maybeFVname, useOSS):
    global ogBackend
    ogBackend = OG_GlueGenerator()
    ogBackend.OnStartup(modelingLanguage, asnFile, outputDir, maybeFVname, useOSS)


def OnBasic(nodeTypename, node, leafTypeDict, names):
    ogBackend.OnBasic(nodeTypename, node, leafTypeDict, names)


def OnSequence(nodeTypename, node, leafTypeDict, names):
    ogBackend.OnSequence(nodeTypename, node, leafTypeDict, names)


def OnSet(nodeTypename, node, leafTypeDict, names):
    ogBackend.OnSet(nodeTypename, node, leafTypeDict, names)  # pragma: nocover


def OnEnumerated(nodeTypename, node, leafTypeDict, names):
    ogBackend.OnEnumerated(nodeTypename, node, leafTypeDict, names)


def OnSequenceOf(nodeTypename, node, leafTypeDict, names):
    ogBackend.OnSequenceOf(nodeTypename, node, leafTypeDict, names)


def OnSetOf(nodeTypename, node, leafTypeDict, names):
    ogBackend.OnSetOf(nodeTypename, node, leafTypeDict, names)  # pragma: nocover


def OnChoice(nodeTypename, node, leafTypeDict, names):
    ogBackend.OnChoice(nodeTypename, node, leafTypeDict, names)


def OnShutdown(modelingLanguage, asnFile, maybeFVname):
    ogBackend.OnShutdown(modelingLanguage, asnFile, maybeFVname)
