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

from typing import Set, Dict  # NOQA pylint: disable=unused-import

from ..commonPy.aadlAST import ApLevelContainer, Param
from ..commonPy.asnParser import AST_Leaftypes, AST_Lookup, AsnNode

g_HeaderFile = None
g_SourceFile = None
g_PythonFile = None

# Python statement list
g_headerPython = []
g_bodyPython = []
g_TMprocessors = []
g_footerPython = []

g_asn_name = ""
g_outputDir = ""
g_maybeFVname = ""
g_perFV = set()  # type: Set[str]
g_langPerSP = {}  # type: Dict[ApLevelContainer, str]


def CleanName(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


# Called once per RI (i.e. per SUBPROGRAM IMPLEMENTATION)
def OnStartup(modelingLanguage: str,
              asnFile: str,
              subProgram: ApLevelContainer,
              unused_subProgramImplementation: str,
              outputDir: str,
              maybeFVname: str,
              unused_useOSS: bool) -> None:
    g_langPerSP[subProgram] = modelingLanguage
    CleanSP = CleanName(subProgram._id)

    global g_maybeFVname
    g_maybeFVname = maybeFVname
    cleanFVname = CleanName(g_maybeFVname)

    global g_asn_name
    g_asn_name = os.path.basename(os.path.splitext(asnFile)[0]).replace("-", "_")

    if not os.path.exists(outputDir + "python"):
        os.mkdir(outputDir + "python")

    global g_PythonFile
    if g_PythonFile is None:
        g_PythonFile = open(outputDir + "python/PythonController.py", "w")
        g_headerPython.append("import threading, time, sys, os, ctypes\n")
        # g_headerPython.append("from PythonAccess import *")
        g_headerPython.append("import DV")
        g_headerPython.append('PythonAccess = ctypes.cdll.LoadLibrary("./PythonAccess.so")')
        g_headerPython.append('OpenMsgQueueForReading = PythonAccess.OpenMsgQueueForReading')
        g_headerPython.append('OpenMsgQueueForReading.restype = ctypes.c_int')
        g_headerPython.append('CloseMsgQueue =  PythonAccess.CloseMsgQueue')
        g_headerPython.append('GetMsgQueueBufferSize = PythonAccess.GetMsgQueueBufferSize')
        g_headerPython.append('GetMsgQueueBufferSize.restype = ctypes.c_int')
        g_headerPython.append('RetrieveMessageFromQueue = PythonAccess.RetrieveMessageFromQueue')
        g_headerPython.append('RetrieveMessageFromQueue.restype = ctypes.c_int')

    # By offering OpenMsgQueueForReading, CloseMsgQueue, GetMsgQueueBufferSize and RetrieveMessageFromQueue,
    # the python scripts can receive TMs on their own (used in the msc2py code).
    # For TCs, that is not necessary, since SendTC... functions have already been generated (see below)
    global g_HeaderFile
    if g_HeaderFile is None:
        g_HeaderFile = open(outputDir + "python/gui_api.h", "w")
        g_HeaderFile.write('#ifndef __HEADER_' + cleanFVname + "_H__\n")
        g_HeaderFile.write('#define __HEADER_' + cleanFVname + "_H__\n\n")
        g_HeaderFile.write('typedef unsigned char byte;\n\n')
        g_HeaderFile.write("int OpenMsgQueueForReading(char *queueName);\n")
        g_HeaderFile.write("void CloseMsgQueue(int queue_id);\n")
        g_HeaderFile.write("int GetMsgQueueBufferSize(int queue_id);\n")
        g_HeaderFile.write("int RetrieveMessageFromQueue(int queue_id, int maxSize, byte *pBuf);\n")

    global g_SourceFile
    if g_SourceFile is None:
        g_SourceFile = open(outputDir + "python/gui_api.c", "w")
        g_SourceFile.write('#include <stdio.h>\n')
        g_SourceFile.write('#include <string.h>\n')
        g_SourceFile.write('#include <unistd.h>\n')
        g_SourceFile.write('#include <sys/types.h>\n')
        g_SourceFile.write('#include <mqueue.h>\n\n')
        g_SourceFile.write('#include "%s.h"\n' % os.path.basename(os.path.splitext(asnFile)[0]))
        g_SourceFile.write('#include "%s_enums_def.h"\n' % cleanFVname)
        g_SourceFile.write('#include "queue_manager.h"\n\n')
        g_SourceFile.write("int OpenMsgQueueForReading(char *queueName)\n")
        g_SourceFile.write("{\n    mqd_t queue_id;\n")
        g_SourceFile.write("    if (0 == open_exchange_queue_for_reading(queueName, &queue_id))\n")
        g_SourceFile.write("        return queue_id;\n")
        g_SourceFile.write("    return -1;\n")
        g_SourceFile.write("}\n\n")
        g_SourceFile.write("void CloseMsgQueue(int queue_id)\n")
        g_SourceFile.write("{\n    mq_close(queue_id);\n")
        g_SourceFile.write("}\n\n")
        g_SourceFile.write("int GetMsgQueueBufferSize(int _queue_id)\n")
        g_SourceFile.write("{\n    struct mq_attr mqstat;\n")
        g_SourceFile.write("    mq_getattr(_queue_id, &mqstat);\n")
        g_SourceFile.write("    return mqstat.mq_msgsize;\n")
        g_SourceFile.write("}\n\n")
        g_SourceFile.write("int RetrieveMessageFromQueue(int queue_id, int maxSize, byte *pBuf)\n")
        g_SourceFile.write("{\n")
        g_SourceFile.write("    int message_received_type = -1;\n")
        g_SourceFile.write("    retrieve_message_from_queue(queue_id, maxSize, pBuf, &message_received_type);\n")
        g_SourceFile.write("    return(message_received_type);\n")
        g_SourceFile.write("}\n\n")

    # have we ever seen before the combination of FVname and Language?
    if maybeFVname + modelingLanguage.lower() not in g_perFV:
        # No, check for things that must be instantiated once per FV+Lang
        g_perFV.add(maybeFVname + modelingLanguage.lower())

        # The first time you see an FV with an sp_impl that is also a GUI_PI, create a thread to poll /FVName_PI_queue
        if modelingLanguage.lower() == "gui_pi":
            # We have telemetry, we need a thread polling the /xyz_PI_queue (xyz: g_maybeFVname)

            g_headerPython.append("import " + g_asn_name + "_asn")
            g_bodyPython.append("class Poll_" + cleanFVname + "(threading.Thread):")
            g_bodyPython.append("    def run(self):")
            g_bodyPython.append('        self._bDie = False')
            g_bodyPython.append('        while True:')
            g_bodyPython.append('            if self._bDie:')
            g_bodyPython.append('                return')
            g_bodyPython.append('            self._msgQueue = OpenMsgQueueForReading(str(os.geteuid()) + "_' + maybeFVname + '_PI_Python_queue")')
            g_bodyPython.append('            if (self._msgQueue != -1): break')
            g_bodyPython.append('            print "Communication channel over %%d_%s_PI_Python_queue not established yet...\\n" %% os.geteuid()' % maybeFVname)
            g_bodyPython.append('            time.sleep(1)')
            g_bodyPython.append('        bufferSize = GetMsgQueueBufferSize(self._msgQueue)')
            g_bodyPython.append('        self._pMem = ctypes.create_string_buffer(bufferSize).raw')
            g_bodyPython.append('        while not self._bDie:')
            g_bodyPython.append('            self.messageReceivedType = RetrieveMessageFromQueue(self._msgQueue, bufferSize, self._pMem)')
            g_bodyPython.append('            if self.messageReceivedType == -1:')
            g_bodyPython.append('                time.sleep(0.01)')
            g_bodyPython.append('                continue')
            g_bodyPython.append('            ProcessTM(self)')
            g_footerPython.append('if __name__ == "__main__":')
            g_footerPython.append('    poll_' + cleanFVname + ' = Poll_' + cleanFVname + '()')
            g_footerPython.append('    poll_' + cleanFVname + '.start()')
            g_footerPython.append('    try:')
            g_footerPython.append('        time.sleep(1e8)')
            g_footerPython.append('    except:')
            g_footerPython.append('        poll_' + cleanFVname + '._bDie = True')
            g_footerPython.append('        poll_' + cleanFVname + '.join()')
    if modelingLanguage.lower() == "gui_pi":
        g_SourceFile.write('T_' + cleanFVname + '_PI_list ii_' + CleanSP + ' = i_' + CleanSP + ';\n')
        g_TMprocessors.append('    if self.messageReceivedType == i_' + CleanSP + ':')
        g_TMprocessors.append('        print "\\n"+chr(27)+"[32m" + "Received Telemetry: ' + CleanSP + '" + chr(27) + "[0m\\n"')
        g_TMprocessors.append('        backup = self._pMem')
        for param in subProgram._params:
            CleanParam = CleanName(param._id)
            g_TMprocessors.append("        # Read the data for param %s" % param._id)
            g_TMprocessors.append("        var_%s = %s_asn.%s()" % (CleanParam, g_asn_name, CleanName(param._signal._asnNodename)))
            g_TMprocessors.append("        var_%s.SetData(self._pMem)" % CleanParam)
            g_TMprocessors.append('        print "Parameter %s:"' % CleanParam)
            g_TMprocessors.append('        var_%s.PrintAll()' % CleanParam)
            g_TMprocessors.append('        print')
            g_TMprocessors.append("        # self._pMem = DV.MovePtrBySizeOf_%s(self._pMem)" % CleanName(param._signal._asnNodename))
        g_TMprocessors.append("        # Revert the pointer to start of the data")
        g_TMprocessors.append('        self._pMem = backup')

    g_headerPython.append('i_' + CleanSP + ' = ctypes.c_int.in_dll(PythonAccess, "ii_' + CleanSP + '").value')
    if modelingLanguage.lower() == "gui_ri":
        g_SourceFile.write('T_' + cleanFVname + '_RI_list ii_' + CleanSP + ' = i_' + CleanSP + ';\n')
        g_headerPython.append('SendTC_' + CleanSP + ' = PythonAccess.SendTC_' + CleanSP)
        decl = '\ndef Invoke_%s(' % CleanSP
        parms = []
        for param in subProgram._params:
            CleanParam = CleanName(param._id)
            nodeTypename = param._signal._asnNodename
            parms.append("var_" + CleanName(nodeTypename))
        decl += ",".join(parms)
        decl += "):"
        g_bodyPython.append(decl)
        g_bodyPython.append("    if -1 == SendTC_%s(%s):" % (CleanSP, ",".join([x + "._ptr" for x in parms])))
        g_bodyPython.append("        print 'Failed to send TC: %s...\\n'" % CleanSP)
        g_bodyPython.append("        raise IOError(\"%s\")" % CleanSP)

        g_SourceFile.write('typedef struct {\n')
        g_SourceFile.write('    int tc_id;\n')
        for param in subProgram._params:
            nodeTypename = param._signal._asnNodename
            CleanParam = CleanName(param._id)
            g_SourceFile.write('    %s %s;\n' % (CleanName(nodeTypename), CleanParam))
        g_SourceFile.write('} %s_TCDATA;\n\n' % CleanSP)

        parms = []
        for param in subProgram._params:
            nodeTypename = param._signal._asnNodename
            CleanParam = CleanName(param._id)
            # parms.append("%s *p_%s" % (CleanName(nodeTypename), CleanParam))
            parms.append("void *p_%s" % CleanParam)
        g_HeaderFile.write('int SendTC_%s(%s);\n' % (CleanSP, ",".join(parms)))
        g_SourceFile.write('int SendTC_%s(%s)\n' % (CleanSP, ",".join(parms)))
        g_SourceFile.write('{\n')
        g_SourceFile.write('    static mqd_t q = (mqd_t)-2;\n')
        g_SourceFile.write('    if (((mqd_t)-2) == q) {\n')
        g_SourceFile.write('        static char QName[1024];\n')
        g_SourceFile.write('        sprintf(QName, "%%d_%s_RI_queue", geteuid());\n' % cleanFVname)
        # g_SourceFile.write('        q = mq_open(QName, O_RDWR | O_NONBLOCK);\n')
        g_SourceFile.write('        open_exchange_queue_for_writing(QName, &q);\n')
        g_SourceFile.write('    }\n')
        g_SourceFile.write('    %s_TCDATA data;\n' % CleanSP)
        g_SourceFile.write('    data.tc_id = (int) i_%s;\n' % CleanSP)
        g_SourceFile.write('    data.%s = * (%s *) p_%s;\n' % (CleanParam, CleanName(nodeTypename), CleanParam))
        g_SourceFile.write('    if (((mqd_t)-1) != q) {\n')
        g_SourceFile.write('        write_message_to_queue(q, sizeof(%s_TCDATA)-4, &data.%s, data.tc_id);\n' %
                           (CleanSP, subProgram._params[0]._id))
        g_SourceFile.write('    } else {\n')
        g_SourceFile.write('        return -1;\n')
        g_SourceFile.write('    }\n')
        g_SourceFile.write('    return 0;\n')
        g_SourceFile.write('}\n')


def Common(unused_nodeTypename: str, unused_node: AsnNode, unused_subProgram: ApLevelContainer, unused_subProgramImplementation: str, unused_param: Param, unused_leafTypeDict: AST_Leaftypes, unused_names: AST_Lookup) -> None:
    pass


def OnBasic(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSequence(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSet(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover


def OnEnumerated(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSequenceOf(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSetOf(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover


def OnChoice(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnShutdown(unused_modelingLanguage: str, unused_asnFile: str, unused_sp: ApLevelContainer, unused_subProgramImplementation: str, unused_maybeFVname: str) -> None:
    pass


def OnFinal() -> None:
    g_HeaderFile.write("\n#endif\n")
    g_PythonFile.write('\n'.join(g_headerPython))
    g_PythonFile.write('\n\n')
    g_PythonFile.write('\n'.join(g_bodyPython))
    g_PythonFile.write('\n\n')
    g_PythonFile.write('def ProcessTM(self):\n')
    if not g_TMprocessors:
        g_PythonFile.write('    pass\n')
    else:
        g_PythonFile.write('\n'.join(g_TMprocessors))
    g_PythonFile.write('\n\n')
    g_PythonFile.write('\n'.join(g_footerPython))
