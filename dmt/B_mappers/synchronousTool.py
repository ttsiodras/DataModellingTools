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
Base class for all synchronous tools
'''

import re
import os

from typing import IO, Any, Generic, TypeVar  # NOQA pylint: disable=unused-import

from ..commonPy.utility import panic, inform, panicWithCallStack
from ..commonPy.aadlAST import InParam, OutParam, InOutParam, ApLevelContainer, Param
from ..commonPy.recursiveMapper import RecursiveMapperGeneric
from ..commonPy.asnAST import AsnNode
from ..commonPy.asnParser import AST_Lookup, AST_Leaftypes


TSource = TypeVar('TSource')
TDestin = TypeVar('TDestin')


class SynchronousToolGlueGeneratorGeneric(Generic[TSource, TDestin]):

    ##############################################
    # Parts to override for each synchronous tool

    def Version(self) -> None:  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a SynchronousToolGlueGenerator...")  # pragma: no cover

    def FromToolToASN1SCC(self) -> RecursiveMapperGeneric:  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a SynchronousToolGlueGenerator...")  # pragma: no cover

    def FromToolToOSS(self) -> RecursiveMapperGeneric:  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a SynchronousToolGlueGenerator...")  # pragma: no cover

    def FromASN1SCCtoTool(self) -> RecursiveMapperGeneric:  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a SynchronousToolGlueGenerator...")  # pragma: no cover

    def FromOSStoTool(self) -> RecursiveMapperGeneric:  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a SynchronousToolGlueGenerator...")  # pragma: no cover

    def HeadersOnStartup(self, unused_modelingLanguage: str, unused_asnFile: str, unused_subProgram: ApLevelContainer, unused_subProgramImplementation: str, unused_outputDir: str, unused_maybeFVname: str) -> None:  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a SynchronousToolGlueGenerator...")  # pragma: no cover

    def SourceVar(self, unused_nodeTypename: str, unused_encoding: str, unused_node: AsnNode, unused_subProgram: ApLevelContainer, unused_subProgramImplementation: str, unused_param: Param, unused_leafTypeDict: AST_Leaftypes, unused_names: AST_Lookup) -> TSource:  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a SynchronousToolGlueGenerator...")  # pragma: no cover

    def TargetVar(self, unused_nodeTypename: str, unused_encoding: str, unused_node: AsnNode, unused_subProgram: ApLevelContainer, unused_subProgramImplementation: str, unused_param: Param, unused_leafTypeDict: AST_Leaftypes, unused_names: AST_Lookup) -> TDestin:  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a SynchronousToolGlueGenerator...")  # pragma: no cover

    def InitializeBlock(self, unused_modelingLanguage: str, unused_asnFile: str, unused_sp: ApLevelContainer, unused_subProgramImplementation: str, unused_maybeFVname: str) -> None:  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a SynchronousToolGlueGenerator...")  # pragma: no cover

    def ExecuteBlock(self, unused_modelingLanguage: str, unused_asnFile: str, unused_sp: ApLevelContainer, unused_subProgramImplementation: str, unused_maybeFVname: str) -> None:  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a SynchronousToolGlueGenerator...")  # pragma: no cover

    ########################################################
    # Parts to possibly override for each synchronous tool

    # noinspection PyMethodMayBeStatic
    def CleanNameAsToolWants(self, name: str) -> str:  # pylint: disable=no-self-use
        return re.sub(r'[^a-zA-Z0-9_]', '_', name)

    # noinspection PyMethodMayBeStatic
    def CleanNameAsADAWants(self, name: str) -> str:  # pylint: disable=no-self-use
        return re.sub(r'[^a-zA-Z0-9_]', '_', name)

    ##########################################
    # Common parts for all synchronous tools

    def __init__(self) -> None:
        # The files written to
        self.C_HeaderFile = None  # type: IO[Any]
        self.C_SourceFile = None  # type: IO[Any]
        self.ADA_HeaderFile = None  # type: IO[Any]
        self.ADA_SourceFile = None  # type: IO[Any]
        self.asn_name = ""
        self.supportedEncodings = ['native', 'uper', 'acn']
        self.dir = None  # type: str
        self.useOSS = None  # type: bool

    def OnStartup(self,
                  modelingLanguage: str,
                  asnFile: str,
                  subProgram: ApLevelContainer,
                  subProgramImplementation: str,
                  outputDir: str,
                  maybeFVname: str,
                  useOSS: bool) -> None:
        if modelingLanguage == "QGenAda":
            self.dir = outputDir
            self.useOSS = useOSS

            outputADAsourceFilename = self.CleanNameAsADAWants(subProgram._id + "_" + subProgramImplementation) + "_wrapper.adb"
            outputADAsourceFilename = outputADAsourceFilename.lower()
            outputADAheaderFilename = self.CleanNameAsADAWants(subProgram._id + "_" + subProgramImplementation) + "_wrapper.ads"
            outputADAheaderFilename = outputADAheaderFilename.lower()

            inform(str(self.__class__) + ": Creating file '%s'...", outputADAheaderFilename)
            self.ADA_HeaderFile = open(outputDir + outputADAheaderFilename, 'w')

            inform(str(self.__class__) + ": Creating file '%s'...", outputADAsourceFilename)
            self.ADA_SourceFile = open(outputDir + outputADAsourceFilename, 'w')

            self.asn_name = os.path.basename(os.path.splitext(asnFile)[0])

            self.ADA_HeaderFile.write('with taste_dataview;\n')
            self.ADA_HeaderFile.write('use taste_dataview;\n')
            self.ADA_HeaderFile.write('with %s_types;\n' % self.CleanNameAsADAWants(subProgram._id))
            self.ADA_HeaderFile.write('use %s_types;\n\n' % self.CleanNameAsADAWants(subProgram._id))
            self.ADA_HeaderFile.write(
                'package %s is\n\n' %
                self.CleanNameAsADAWants(subProgram._id + "_" + subProgramImplementation + "_wrapper"))

            self.ADA_SourceFile.write('with %s;\n' % self.CleanNameAsADAWants(subProgram._id))
            self.ADA_SourceFile.write('with %s_types;\n' % self.CleanNameAsADAWants(subProgram._id))
            self.ADA_SourceFile.write('use %s_types;\n\n' % self.CleanNameAsADAWants(subProgram._id))
            self.ADA_SourceFile.write(
                'package body %s is\n\n' %
                self.CleanNameAsADAWants(subProgram._id + "_" + subProgramImplementation + "_wrapper"))
        else:
            self.dir = outputDir
            self.useOSS = useOSS

            outputCheaderFilename = \
                self.CleanNameAsToolWants(subProgram._id + "_" + subProgramImplementation) + "." + self.CleanNameAsToolWants(modelingLanguage) + ".h"
            outputCsourceFilename = \
                self.CleanNameAsToolWants(subProgram._id + "_" + subProgramImplementation) + "." + self.CleanNameAsToolWants(modelingLanguage) + ".c"
            outputADAsourceFilename = self.CleanNameAsADAWants(subProgram._id + "_" + subProgramImplementation) + ".adb"
            outputADAsourceFilename = outputADAsourceFilename.lower()
            outputADAheaderFilename = self.CleanNameAsADAWants(subProgram._id + "_" + subProgramImplementation) + ".ads"
            outputADAheaderFilename = outputADAheaderFilename.lower()

            inform(str(self.__class__) + ": Creating file '%s'...", outputCheaderFilename)
            self.C_HeaderFile = open(outputDir + outputCheaderFilename, 'w')

            inform(str(self.__class__) + ": Creating file '%s'...", outputCsourceFilename)
            self.C_SourceFile = open(outputDir + outputCsourceFilename, 'w')

            inform(str(self.__class__) + ": Creating file '%s'...", outputADAheaderFilename)
            self.ADA_HeaderFile = open(outputDir + outputADAheaderFilename, 'w')

            inform(str(self.__class__) + ": Creating file '%s'...", outputADAsourceFilename)
            self.ADA_SourceFile = open(outputDir + outputADAsourceFilename, 'w')

            self.asn_name = os.path.basename(os.path.splitext(asnFile)[0])

            ID = modelingLanguage.upper() + "_" + \
                os.path.basename(asnFile).replace(".", "").upper() + "_" + \
                self.CleanNameAsToolWants(subProgram._id + "_" + subProgramImplementation).upper()
            ID = re.sub(r'[^A-Za-z0-9_]', '_', ID).upper()
            self.C_HeaderFile.write("#ifndef __%s_H__\n" % ID)
            self.C_HeaderFile.write("#define __%s_H__\n\n" % ID)
            self.C_HeaderFile.write("#include <stdlib.h> /* for size_t */\n")
            if subProgramImplementation.lower() == "c" and subProgram._fpgaConfigurations is not '':
                self.C_HeaderFile.write("#include \"C_ASN1_Types.h\"\n")
            self.C_HeaderFile.write("\n")

            self.C_SourceFile.write("#ifdef __unix__\n")
            self.C_SourceFile.write("#include <stdio.h>\n")
            self.C_SourceFile.write("#include <string.h>\n\n")
            self.C_SourceFile.write("#include <assert.h>\n\n")
            self.C_SourceFile.write("#endif\n")

            self.C_SourceFile.write("#include \"%s\"\n" % outputCheaderFilename)

            self.HeadersOnStartup(modelingLanguage, asnFile, subProgram, subProgramImplementation, outputDir, maybeFVname)

            self.ADA_HeaderFile.write('with Interfaces.C.Extensions;\n')
            self.ADA_HeaderFile.write('use Interfaces.C.Extensions;\n\n')
            self.ADA_HeaderFile.write(
                'package %s is\n\n' %
                self.CleanNameAsADAWants(subProgram._id + "_" + subProgramImplementation))

            self.ADA_SourceFile.write('with Interfaces.C.Extensions;\n')
            self.ADA_SourceFile.write('use Interfaces.C.Extensions;\n\n')
            self.ADA_SourceFile.write(
                'package body %s is\n\n' %
                self.CleanNameAsADAWants(subProgram._id + "_" + subProgramImplementation))

    def Encoder(self,
                nodeTypename: str,
                encoding: str,
                node: AsnNode,
                subProgram: ApLevelContainer,
                subProgramImplementation: str,
                param: Param,
                leafTypeDict: AST_Leaftypes,
                names: AST_Lookup) -> None:
        if encoding.lower() not in self.supportedEncodings:
            panic(str(self.__class__) + ": in (%s), encoding can be one of %s (not '%s')" % (  # pragma: no cover
                subProgram._id + "." + subProgramImplementation, self.supportedEncodings, encoding))  # pragma: no cover

        tmpSpName = "Convert_From_%s_To_%s_In_%s_%s" % \
            (self.CleanNameAsADAWants(nodeTypename),
             encoding.lower(),
             self.CleanNameAsADAWants(subProgram._id + "_" + subProgramImplementation),
             self.CleanNameAsADAWants(param._id))

        srcVar = self.SourceVar(nodeTypename, encoding, node, subProgram, subProgramImplementation, param, leafTypeDict, names)

        if subProgramImplementation == "QGenAda":
            self.ADA_HeaderFile.write(
                "    procedure Ada_%s(QGen_OUT : in %s; T_OUT : out %s);\n" %
                (tmpSpName, self.CleanNameAsToolWants(nodeTypename), "asn1Scc" + self.CleanNameAsToolWants(nodeTypename)))
            self.ADA_SourceFile.write(
                "    procedure Ada_%s(QGen_OUT : in %s; T_OUT : out %s) is\n" %
                (tmpSpName, self.CleanNameAsToolWants(nodeTypename), "asn1Scc" + self.CleanNameAsToolWants(nodeTypename)))
            self.ADA_SourceFile.write('begin\n')

            toolToAsn1 = self.FromToolToASN1SCC()
            lines = toolToAsn1.Map(
                "QGen_OUT",
                "T_OUT",
                node,
                leafTypeDict,
                names) if toolToAsn1 else []

            lines = ["        " + x for x in lines]
            self.ADA_SourceFile.write("".join(lines))

            self.ADA_SourceFile.write(
                "    end Ada_%s;\n\n" % tmpSpName)
        else:
            self.C_HeaderFile.write(
                "int %s(void *pBuffer, size_t iMaxBufferSize);\n" % tmpSpName)
            self.ADA_HeaderFile.write(
                "procedure Ada_%s(pBuffer : in Interfaces.C.char_array; iMaxBufferSize : in Integer; bytesWritten : out Integer);\n" % tmpSpName)
            self.ADA_SourceFile.write(
                "procedure Ada_%s(pBuffer : in Interfaces.C.char_array; iMaxBufferSize : in Integer; bytesWritten : out Integer) is\n" % tmpSpName)
            self.ADA_SourceFile.write(
                "    function C_%s(pBuffer : Interfaces.C.char_array; iMaxBufferSize : Integer) return Integer;\n" % tmpSpName)
            self.ADA_SourceFile.write(
                '    pragma Import(C, C_%s, "%s");\n' % (tmpSpName, tmpSpName))
            self.ADA_SourceFile.write(
                'begin\n'
                '    bytesWritten := C_%s(pBuffer, iMaxBufferSize);\n' % tmpSpName)
            self.ADA_SourceFile.write(
                "end Ada_%s;\n\n" % tmpSpName)
            self.C_SourceFile.write(
                "int %s(void *pBuffer, size_t iMaxBufferSize)\n{\n" % tmpSpName)

            if self.useOSS and encoding.lower() == "uper":
                self.C_SourceFile.write(
                    "    STATIC OSS_%s var_%s;\n" %
                    (self.CleanNameAsToolWants(nodeTypename), self.CleanNameAsToolWants(nodeTypename)))
            else:
                self.C_SourceFile.write(
                    "    STATIC asn1Scc%s var_%s;\n" %
                    (self.CleanNameAsToolWants(nodeTypename), self.CleanNameAsToolWants(nodeTypename)))

            if encoding.lower() in ["uper", "acn"]:
                if self.useOSS:
                    self.C_SourceFile.write("    STATIC OssBuf strm;\n")
                else:
                    self.C_SourceFile.write("    int errorCode;\n")
                    self.C_SourceFile.write("    STATIC BitStream strm;\n\n")
                    # setup the asn1c encoder
                    self.C_SourceFile.write("    BitStream_Init(&strm, pBuffer, iMaxBufferSize);\n")

            # Write the mapping code for the message
            if self.useOSS and encoding.lower() == "uper":
                toolToAsn1 = self.FromToolToOSS()
            else:
                toolToAsn1 = self.FromToolToASN1SCC()
            lines = toolToAsn1.Map(
                srcVar,
                "var_" + self.CleanNameAsToolWants(nodeTypename),
                node,
                leafTypeDict,
                names) if toolToAsn1 else []

            lines = ["    " + x for x in lines]
            self.C_SourceFile.write("".join(lines))

            if self.useOSS and encoding.lower() == "uper":
                # setup the OSS encoder
                self.C_SourceFile.write("\n    strm.value = NULL;\n")
                self.C_SourceFile.write("    strm.length = 0;\n")
                self.C_SourceFile.write(
                    "    if (ossEncode(g_world, OSS_%s_PDU, &var_%s, &strm) != 0) {\n" %
                    (self.CleanNameAsToolWants(nodeTypename), self.CleanNameAsToolWants(nodeTypename)))
                self.C_SourceFile.write("#ifdef __unix__\n")
                self.C_SourceFile.write(
                    '        fprintf(stderr, "Could not encode %s (at %%s, %%d), errorMessage was %%s\\n", __FILE__, __LINE__, ossGetErrMsg(g_world));\n' % nodeTypename)
                self.C_SourceFile.write("#endif\n")
                self.C_SourceFile.write("        return -1;\n")
                self.C_SourceFile.write("    } else {\n")
                self.C_SourceFile.write("        assert(strm.length <= iMaxBufferSize);\n")
                self.C_SourceFile.write("        memcpy(pBuffer, strm.value, strm.length);\n")
                self.C_SourceFile.write("        ossFreeBuf(g_world, strm.value);\n")
                self.C_SourceFile.write("        return strm.length;\n")
                self.C_SourceFile.write("    }\n")
                self.C_SourceFile.write("}\n\n")
            elif encoding.lower() in ["uper", "acn"]:
                self.C_SourceFile.write(
                    "    if (asn1Scc%s_%sEncode(&var_%s, &strm, &errorCode, TRUE) == FALSE) {\n" %
                    (self.CleanNameAsToolWants(nodeTypename),
                     "ACN_" if encoding.lower() == "acn" else "",
                     self.CleanNameAsToolWants(nodeTypename)))
                self.C_SourceFile.write("#ifdef __unix__\n")
                self.C_SourceFile.write(
                    '        fprintf(stderr, "Could not encode %s (at %%s, %%d), errorCode was %%d\\n", __FILE__, __LINE__, errorCode);\n' % nodeTypename)
                self.C_SourceFile.write("#endif\n")
                self.C_SourceFile.write("        return -1;\n")
                self.C_SourceFile.write("    } else {\n")
                self.C_SourceFile.write("        return BitStream_GetLength(&strm);\n")
                self.C_SourceFile.write("    }\n")
                self.C_SourceFile.write("}\n\n")
            elif encoding.lower() == "native":
                self.C_SourceFile.write(
                    "    memcpy(pBuffer, &var_%s, sizeof(asn1Scc%s) );\n" %
                    (self.CleanNameAsToolWants(nodeTypename), self.CleanNameAsToolWants(nodeTypename)))
                self.C_SourceFile.write("    return sizeof(asn1Scc%s);\n" % self.CleanNameAsToolWants(nodeTypename))
                self.C_SourceFile.write("}\n\n")

    def Decoder(self,
                nodeTypename: str,
                encoding: str,
                node: AsnNode,
                subProgram: ApLevelContainer,
                subProgramImplementation: str,
                param: Param,
                leafTypeDict: AST_Leaftypes,
                names: AST_Lookup) -> None:
        tmpSpName = "Convert_From_%s_To_%s_In_%s_%s" % \
            (encoding.lower(),
             self.CleanNameAsADAWants(nodeTypename),
             self.CleanNameAsADAWants(subProgram._id + "_" + subProgramImplementation),
             param._id)

        targetVar = self.TargetVar(nodeTypename, encoding, node, subProgram, subProgramImplementation, param, leafTypeDict, names)

        if subProgramImplementation == "QGenAda":
            self.ADA_HeaderFile.write(
                "    procedure Ada_%s(T_IN : in %s; QGen_IN : out %s);\n" %
                (tmpSpName, "asn1Scc" + self.CleanNameAsToolWants(nodeTypename), self.CleanNameAsToolWants(nodeTypename)))
            self.ADA_SourceFile.write(
                "    procedure Ada_%s(T_IN : in %s; QGen_IN : out %s) is\n" %
                (tmpSpName, "asn1Scc" + self.CleanNameAsToolWants(nodeTypename), self.CleanNameAsToolWants(nodeTypename)))
            self.ADA_SourceFile.write('    begin\n')

            asn1ToTool = self.FromASN1SCCtoTool()
            lines = asn1ToTool.Map(
                "T_IN",
                "QGen_IN",
                node,
                leafTypeDict,
                names) if asn1ToTool else []
            lines = ["        " + x for x in lines]

            self.ADA_SourceFile.write("".join(lines))

            self.ADA_SourceFile.write(
                "    end Ada_%s;\n\n" % tmpSpName)
        else:
            if encoding.lower() not in self.supportedEncodings:
                panic(str(self.__class__) + ": in (%s), encoding can be one of %s (not '%s')" %  # pragma: no cover
                      (subProgram._id + "." + subProgramImplementation, self.supportedEncodings, encoding))  # pragma: no cover

            self.C_HeaderFile.write(
                "int %s(void *pBuffer, size_t iBufferSize);\n" % tmpSpName)

            self.ADA_HeaderFile.write(
                "procedure Ada_%s(pBuffer : Interfaces.C.char_array; iBufferSize : Integer);\n" % tmpSpName)
            self.ADA_SourceFile.write(
                "procedure Ada_%s(pBuffer : Interfaces.C.char_array; iBufferSize : Integer) is\n" % tmpSpName)
            self.ADA_SourceFile.write(
                "    procedure C_%s(pBuffer : Interfaces.C.char_array; iBufferSize : Integer);\n" % tmpSpName)
            self.ADA_SourceFile.write(
                '    pragma Import(C, C_%s, "%s");\n' % (tmpSpName, tmpSpName))
            self.ADA_SourceFile.write(
                'begin\n'
                '    C_%s(pBuffer, iBufferSize);\n' % tmpSpName)
            self.ADA_SourceFile.write(
                "end Ada_%s;\n\n" % tmpSpName)
            self.C_SourceFile.write(
                "int %s(void *pBuffer, size_t iBufferSize)\n{\n" % tmpSpName)

            if self.useOSS and encoding.lower() == "uper":
                self.C_SourceFile.write("    int pdutype = OSS_%s_PDU;\n" % self.CleanNameAsToolWants(nodeTypename))
                self.C_SourceFile.write("    STATIC OssBuf strm;\n")
                self.C_SourceFile.write("    OSS_%s *pVar_%s = NULL;\n\n" %
                                        (self.CleanNameAsToolWants(nodeTypename),
                                         self.CleanNameAsToolWants(nodeTypename)))
                self.C_SourceFile.write("    strm.value = pBuffer;\n")
                self.C_SourceFile.write("    strm.length = iBufferSize;\n")
                self.C_SourceFile.write("    if (0 == ossDecode(g_world, &pdutype, &strm, (void**)&pVar_%s)) {\n" %
                                        self.CleanNameAsToolWants(nodeTypename))
                self.C_SourceFile.write("        /* Decoding succeeded */\n")
            else:
                self.C_SourceFile.write("    STATIC asn1Scc%s var_%s;\n" %
                                        (self.CleanNameAsToolWants(nodeTypename), self.CleanNameAsToolWants(nodeTypename)))
                if encoding.lower() in ["uper", "acn"]:
                    self.C_SourceFile.write("    int errorCode;\n")
                    self.C_SourceFile.write("    STATIC BitStream strm;\n")
                    self.C_SourceFile.write("    BitStream_AttachBuffer(&strm, pBuffer, iBufferSize);\n\n")
                    self.C_SourceFile.write("    if (asn1Scc%s_%sDecode(&var_%s, &strm, &errorCode)) {\n" %
                                            (self.CleanNameAsToolWants(nodeTypename),
                                             "ACN_" if encoding.lower() == "acn" else "",
                                             self.CleanNameAsToolWants(nodeTypename)))
                    self.C_SourceFile.write("        /* Decoding succeeded */\n")
                elif encoding.lower() == "native":
                    self.C_SourceFile.write("    var_%s = *(asn1Scc%s *) pBuffer;\n    {\n" %
                                            (self.CleanNameAsToolWants(nodeTypename),
                                             self.CleanNameAsToolWants(nodeTypename)))

            if self.useOSS and encoding.lower() == "uper":
                asn1ToTool = self.FromOSStoTool()
                lines = asn1ToTool.Map(
                    "(*pVar_" + self.CleanNameAsToolWants(nodeTypename) + ")",
                    targetVar,
                    node,
                    leafTypeDict,
                    names) if asn1ToTool else []
            else:
                asn1ToTool = self.FromASN1SCCtoTool()
                lines = asn1ToTool.Map(
                    "var_" + self.CleanNameAsToolWants(nodeTypename),
                    targetVar,
                    node,
                    leafTypeDict,
                    names) if asn1ToTool else []
            lines = ["        " + x for x in lines]
            self.C_SourceFile.write("".join(lines))

            if self.useOSS and encoding.lower() == "uper":
                self.C_SourceFile.write("        ossFreeBuf(g_world, pVar_%s);\n" % self.CleanNameAsToolWants(nodeTypename))
                self.C_SourceFile.write("        return 0;\n")
                self.C_SourceFile.write("    } else {\n")
                self.C_SourceFile.write("#ifdef __unix__\n")
                self.C_SourceFile.write(
                    '        fprintf(stderr, "Could not decode %s (at %%s, %%d), error message was %%s\\n", __FILE__, __LINE__, ossGetErrMsg(g_world));\n' % nodeTypename)
                self.C_SourceFile.write("#endif\n")
                self.C_SourceFile.write("        return -1;\n")
                self.C_SourceFile.write("    }\n")
                self.C_SourceFile.write("}\n\n")
            elif encoding.lower() in ["uper", "acn"]:
                self.C_SourceFile.write("        return 0;\n")
                self.C_SourceFile.write("    } else {\n")
                self.C_SourceFile.write("#ifdef __unix__\n")
                self.C_SourceFile.write(
                    '        fprintf(stderr, "Could not decode %s (at %%s, %%d), error code was %%d\\n", __FILE__, __LINE__, errorCode);\n' % nodeTypename)
                self.C_SourceFile.write("#endif\n")
                self.C_SourceFile.write("        return -1;\n")
                self.C_SourceFile.write("    }\n")
                self.C_SourceFile.write("}\n\n")
            else:
                self.C_SourceFile.write("        return 0;\n")
                self.C_SourceFile.write("    }\n")
                self.C_SourceFile.write("}\n\n")

    def Common(self,
               nodeTypename: str,
               node: AsnNode,
               subProgram: ApLevelContainer,
               subProgramImplementation: str,
               param: Param,
               leafTypeDict: AST_Leaftypes,
               names: AST_Lookup) -> None:
        if isinstance(param, (InOutParam, InParam)):
            self.Decoder(nodeTypename, param._sourceElement._encoding, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
        if isinstance(param, (InOutParam, OutParam)):
            self.Encoder(nodeTypename, param._sourceElement._encoding, node, subProgram, subProgramImplementation, param, leafTypeDict, names)

    def OnBasic(self, nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        realLeafType = leafTypeDict[nodeTypename]
        inform(str(self.__class__) + ": BASE: %s (%s)", nodeTypename, realLeafType)
        self.Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)

    def OnSequence(self, nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        inform(str(self.__class__) + ": SEQUENCE: %s", nodeTypename)
        self.Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)

    def OnSet(self, nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        inform(str(self.__class__) + ": SET: %s", nodeTypename)  # pragma: nocover
        self.Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover

    def OnEnumerated(self, nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        inform(str(self.__class__) + ": ENUMERATED: %s", nodeTypename)
        self.Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)

    def OnSequenceOf(self, nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        inform(str(self.__class__) + ": SEQUENCEOF: %s", nodeTypename)
        self.Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)

    def OnSetOf(self, nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        inform(str(self.__class__) + ": SETOF: %s", nodeTypename)  # pragma: nocover
        self.Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover

    def OnChoice(self, nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        inform(str(self.__class__) + ": CHOICE: %s", nodeTypename)
        self.Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)

    def OnShutdown(self, modelingLanguage: str, asnFile: str, sp: ApLevelContainer, subProgramImplementation: str, maybeFVname: str) -> None:
        if modelingLanguage == "QGenAda":
            self.ADA_HeaderFile.write("    procedure Execute_%s (" % self.CleanNameAsADAWants(sp._id + "_" + subProgramImplementation))
            self.ADA_SourceFile.write("    procedure Execute_%s (" % self.CleanNameAsADAWants(sp._id + "_" + subProgramImplementation))
            for param in sp._params:
                if param._id != sp._params[0]._id:
                    self.ADA_HeaderFile.write('; ')
                    self.ADA_SourceFile.write('; ')
                self.ADA_HeaderFile.write(self.CleanNameAsToolWants(param._id) + " : access asn1Scc" + self.CleanNameAsToolWants(param._signal._asnNodename))
                self.ADA_SourceFile.write(self.CleanNameAsToolWants(param._id) + " : access asn1Scc" + self.CleanNameAsToolWants(param._signal._asnNodename))

            self.ADA_HeaderFile.write(");\n")
            self.ADA_SourceFile.write(") is\n")
            for param in sp._params:
                self.ADA_SourceFile.write("        %s : aliased %s;\n" % ("QGen_" + self.CleanNameAsToolWants(param._id), self.CleanNameAsToolWants(param._signal._asnNodename)))
            self.ADA_SourceFile.write("    begin\n\n")
            for param in sp._params:
                nodeTypename = param._signal._asnNodename
                encoding = param._sourceElement._encoding
                tmpSpName = "Ada_Convert_From_%s_To_%s_In_%s_%s" % \
                    (encoding.lower(),
                     self.CleanNameAsADAWants(nodeTypename),
                     self.CleanNameAsADAWants(sp._id + "_" + subProgramImplementation),
                     self.CleanNameAsADAWants(param._id))
                if isinstance(param, InParam):
                    self.ADA_SourceFile.write(
                        '        %s(%s.all, QGen_%s);\n' % (
                            tmpSpName,
                            self.CleanNameAsToolWants(param._id),
                            self.CleanNameAsToolWants(param._id)))

            self.ADA_SourceFile.write("\n        %s.comp (" % self.CleanNameAsADAWants(sp._id))
            for param in sp._params:
                if param._id != sp._params[0]._id:
                    self.ADA_SourceFile.write(', ')
                self.ADA_SourceFile.write("QGen_" + self.CleanNameAsToolWants(param._id))
            self.ADA_SourceFile.write(");\n\n")

            # Encode outputs
            for param in sp._params:
                nodeTypename = param._signal._asnNodename
                encoding = param._sourceElement._encoding
                tmpSpName = "Ada_Convert_From_%s_To_%s_In_%s_%s" % \
                    (self.CleanNameAsADAWants(nodeTypename),
                     encoding.lower(),
                     self.CleanNameAsADAWants(sp._id + "_" + subProgramImplementation),
                     param._id)
                if isinstance(param, InOutParam) or isinstance(param, OutParam):
                    self.ADA_SourceFile.write(
                        '        %s(QGen_%s, %s.all);\n' % (
                            tmpSpName,
                            self.CleanNameAsToolWants(param._id),
                            self.CleanNameAsToolWants(param._id)))
            self.ADA_SourceFile.write("    end Execute_%s;\n" % self.CleanNameAsADAWants(sp._id + "_" + subProgramImplementation))
            self.ADA_SourceFile.write(
                'end %s;\n' %
                self.CleanNameAsADAWants(sp._id + "_" + subProgramImplementation + "_wrapper"))
            self.ADA_HeaderFile.write(
                'end %s;\n' %
                self.CleanNameAsADAWants(sp._id + "_" + subProgramImplementation + "_wrapper"))

        else:
            # Check if Function Block will exist both as SW and HW. If yes append suffix to avoid multiple definition errors.
            fpgaSuffix = ''
            dispatcherSuffix = "_Brave_Dispatch"
            if subProgramImplementation.lower() == "c" and sp._fpgaConfigurations is not '':
                fpgaSuffix = "_Brave_Fpga"
            
            self.C_HeaderFile.write("void Execute_%s();\n" % self.CleanNameAsADAWants(sp._id + "_" + subProgramImplementation))
            if maybeFVname != "":
                self.C_HeaderFile.write("void init_%s%s();\n" % (self.CleanNameAsADAWants(maybeFVname), fpgaSuffix))
                self.C_HeaderFile.write("void %s_%s%s(" % (self.CleanNameAsADAWants(maybeFVname), self.CleanNameAsADAWants(sp._id), fpgaSuffix))
            else:  # pragma: no cover
                self.C_HeaderFile.write("void %s_init%s();\n" % (self.CleanNameAsADAWants(sp._id), fpgaSuffix))  # pragma: no cover
                self.C_HeaderFile.write("void %s%s(" % (self.CleanNameAsADAWants(sp._id), fpgaSuffix))  # pragma: no cover
            for param in sp._params:
                if param._id != sp._params[0]._id:
                    self.C_HeaderFile.write(', ')
                if isinstance(param, InParam):
                    self.C_HeaderFile.write('void *p' + self.CleanNameAsToolWants(param._id) + ', size_t size_' + self.CleanNameAsToolWants(param._id))
                else:
                    self.C_HeaderFile.write('void *p' + self.CleanNameAsToolWants(param._id) + ', size_t *pSize_' + self.CleanNameAsToolWants(param._id))
            self.C_HeaderFile.write(");\n")
            
            # Check if Function Block will exist both as SW and HW. If yes generate dispatcher function (to delegate to SW or HW).
            if subProgramImplementation.lower() == "c" and sp._fpgaConfigurations is not '':
                if maybeFVname != "":
                    self.C_HeaderFile.write("asn1SccMyInteger %s_%s%s(" % (self.CleanNameAsADAWants(maybeFVname), self.CleanNameAsADAWants(sp._id), dispatcherSuffix))
                else:  # pragma: no cover
                    self.C_HeaderFile.write("asn1SccMyInteger %s%s(" % (self.CleanNameAsADAWants(sp._id), dispatcherSuffix))  # pragma: no cover                    
                for param in sp._params:
                    if param._id != sp._params[0]._id:
                        self.C_HeaderFile.write(', ')
                    if isinstance(param, InParam):
                        self.C_HeaderFile.write('void *p' + self.CleanNameAsToolWants(param._id) + ', size_t size_' + self.CleanNameAsToolWants(param._id))
                    else:
                        self.C_HeaderFile.write('void *p' + self.CleanNameAsToolWants(param._id) + ', size_t *pSize_' + self.CleanNameAsToolWants(param._id))
                self.C_HeaderFile.write(");\n")            
            
            self.C_HeaderFile.write("\n#endif\n")

            self.C_SourceFile.write("void Execute_%s()\n{\n" % self.CleanNameAsADAWants(sp._id + "_" + subProgramImplementation))
            self.ExecuteBlock(modelingLanguage, asnFile, sp, subProgramImplementation, maybeFVname)
            self.C_SourceFile.write("}\n\n")

            if maybeFVname != "":
                self.C_SourceFile.write("void init_%s%s()\n" % (self.CleanNameAsADAWants(maybeFVname), fpgaSuffix))
            else:  # pragma: no cover
                self.C_SourceFile.write("void %s_init()\n" % self.CleanNameAsADAWants(sp._id))  # pragma: no cover
            self.C_SourceFile.write("{\n")
            self.InitializeBlock(modelingLanguage, asnFile, sp, subProgramImplementation, maybeFVname)
            # self.C_SourceFile.write("    extern void InitializeGlue();\n")
            # self.C_SourceFile.write("    InitializeGlue();\n")
            self.C_SourceFile.write("}\n\n")
            if maybeFVname != "":
                self.C_SourceFile.write("void %s_%s%s(" % (self.CleanNameAsADAWants(maybeFVname), self.CleanNameAsADAWants(sp._id), fpgaSuffix))
            else:  # pragma: no cover
                self.C_SourceFile.write("void %s(" % self.CleanNameAsADAWants(sp._id))  # pragma: no cover
            for param in sp._params:
                if param._id != sp._params[0]._id:
                    self.C_SourceFile.write(', ')
                if isinstance(param, InParam):
                    self.C_SourceFile.write('void *p' + self.CleanNameAsToolWants(param._id) + ', size_t size_' + self.CleanNameAsToolWants(param._id))
                else:
                    self.C_SourceFile.write('void *p' + self.CleanNameAsToolWants(param._id) + ', size_t *pSize_' + self.CleanNameAsToolWants(param._id))
            self.C_SourceFile.write(")\n{\n")

            # Decode inputs
            for param in sp._params:
                nodeTypename = param._signal._asnNodename
                encoding = param._sourceElement._encoding
                tmpSpName = "Convert_From_%s_To_%s_In_%s_%s" % \
                    (encoding.lower(),
                     self.CleanNameAsADAWants(nodeTypename),
                     self.CleanNameAsADAWants(sp._id + "_" + subProgramImplementation),
                     self.CleanNameAsADAWants(param._id))
                if isinstance(param, InParam):
                    self.C_SourceFile.write('    %s(p%s, size_%s);\n' %
                                            (tmpSpName,
                                             self.CleanNameAsToolWants(param._id),
                                             self.CleanNameAsToolWants(param._id)))
                elif isinstance(param, InOutParam):
                    self.C_SourceFile.write('    %s(p%s, *pSize_%s);\n' %  # pragma: no cover
                                            (tmpSpName,
                                             self.CleanNameAsToolWants(param._id),
                                             self.CleanNameAsToolWants(param._id)))  # pragma: no cover

            # Do functional work
            self.C_SourceFile.write("    Execute_%s();\n" % self.CleanNameAsADAWants(sp._id + "_" + subProgramImplementation))

            # Encode outputs
            for param in sp._params:
                nodeTypename = param._signal._asnNodename
                encoding = param._sourceElement._encoding
                tmpSpName = "Convert_From_%s_To_%s_In_%s_%s" % \
                    (self.CleanNameAsADAWants(nodeTypename),
                     encoding.lower(),
                     self.CleanNameAsADAWants(sp._id + "_" + subProgramImplementation),
                     param._id)
                if isinstance(param, InOutParam) or isinstance(param, OutParam):
                    self.C_SourceFile.write('    *pSize_%s = %s(p%s, %s);\n' %
                                            (self.CleanNameAsToolWants(param._id),
                                             tmpSpName,
                                             self.CleanNameAsToolWants(param._id),
                                             param._signal._asnSize))
            self.C_SourceFile.write("}\n\n")

            # Check if Function Block will exist both as SW and HW. If yes generate dispatcher function (to delegate to SW or HW).
            if subProgramImplementation.lower() == "c" and sp._fpgaConfigurations is not '':
                if maybeFVname != "":
                    self.C_SourceFile.write("asn1SccMyInteger %s_%s%s(" % (self.CleanNameAsADAWants(maybeFVname), self.CleanNameAsADAWants(sp._id), dispatcherSuffix))
                else:  # pragma: no cover
                    self.C_SourceFile.write("asn1SccMyInteger %s%s(" % (self.CleanNameAsADAWants(sp._id), dispatcherSuffix))  # pragma: no cover                    
                for param in sp._params:
                    if param._id != sp._params[0]._id:
                        self.C_SourceFile.write(', ')
                    if isinstance(param, InParam):
                        self.C_SourceFile.write('void *p' + self.CleanNameAsToolWants(param._id) + ', size_t size_' + self.CleanNameAsToolWants(param._id))
                    else:
                        self.C_SourceFile.write('void *p' + self.CleanNameAsToolWants(param._id) + ', size_t *pSize_' + self.CleanNameAsToolWants(param._id))
                self.C_SourceFile.write(")\n{\n")
                self.C_SourceFile.write('    /*\n')
                self.C_SourceFile.write('    Delegate to one or the other side (SW or HW) depending on whether the value of a global variable storing the current\n')
                self.C_SourceFile.write('    configuration equals one of those defined for the target function in new IV field.\n')
                self.C_SourceFile.write('    */\n')
                self.C_SourceFile.write('    extern const char p_szGlobalState[];\n')
                self.C_SourceFile.write('    char *fConfig;\n')
                self.C_SourceFile.write('    char fConfigList[30] = "%s";\n' % (sp._fpgaConfigurations))
                self.C_SourceFile.write('    fConfig = strtok(fConfigList, "_");\n')
                self.C_SourceFile.write('    while( fConfig != NULL ) {\n')
                self.C_SourceFile.write('       if(!strcmp(p_szGlobalState, fConfig)){\n')
                self.C_SourceFile.write('           // delegate to HW\n')
                self.C_SourceFile.write('           printf("[###### Dispatcher ######] Delegating to HW ... (to be implemented) \\n");\n')
                self.C_SourceFile.write('           // called_compute_something_Brave_Fpga(pinp, size_inp, poutp, pSize_outp);\n')
                self.C_SourceFile.write('           // delegated to HW, return 0\n')
                self.C_SourceFile.write('           return 0;\n')
                self.C_SourceFile.write('       }\n')
                self.C_SourceFile.write('       fConfig = strtok(NULL, "_");\n')
                self.C_SourceFile.write('    }\n')
                self.C_SourceFile.write('    printf("[###### Dispatcher ######] Delegating to SW ...\\n");\n')
                self.C_SourceFile.write('    // delegate to SW, return 1\n')
                self.C_SourceFile.write('    return 1;\n')
                self.C_SourceFile.write("}\n\n")

            self.ADA_HeaderFile.write(
                "procedure Ada_Execute_%s;\n" % self.CleanNameAsADAWants(sp._id + "_" + subProgramImplementation))
            self.ADA_HeaderFile.write('\nend %s;\n' % self.CleanNameAsADAWants(sp._id + "_" + subProgramImplementation))
            self.ADA_SourceFile.write(
                "procedure Ada_Execute_%s is\n" %
                self.CleanNameAsADAWants(sp._id + "_" + subProgramImplementation))
            self.ADA_SourceFile.write(
                "    procedure C_Execute_%s;\n" %
                self.CleanNameAsADAWants(sp._id + "_" + subProgramImplementation))
            self.ADA_SourceFile.write(
                '    pragma Import(C, C_Execute_%s, "Execute_%s");\n' %
                (
                    self.CleanNameAsADAWants(sp._id + "_" + subProgramImplementation),
                    self.CleanNameAsToolWants(sp._id + "_" + subProgramImplementation),
                ))

            self.ADA_SourceFile.write(
                'begin\n    C_Execute_%s;\n' %
                self.CleanNameAsADAWants(sp._id + "_" + subProgramImplementation))
            self.ADA_SourceFile.write(
                "end Ada_Execute_%s;\n\n" %
                self.CleanNameAsADAWants(sp._id + "_" + subProgramImplementation))
            self.ADA_SourceFile.write('\nend %s;\n' % self.CleanNameAsADAWants(sp._id + "_" + subProgramImplementation))


SynchronousToolGlueGenerator = SynchronousToolGlueGeneratorGeneric[str, str]
