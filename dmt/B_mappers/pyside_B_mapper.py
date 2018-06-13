# (C) Semantix Information Technologies for the mapper design.
# (C) European Space Agency for the Pyside GUI code - Author: Maxime Perrotin

import re
import os
from typing import List

from ..commonPy.asnAST import (
    AsnInt, AsnBool, AsnReal, AsnEnumerated,
    AsnOctetString, AsnChoice, AsnSequence, AsnSet,
    AsnSequenceOf, AsnSetOf, AsnMetaMember, AsnNode)

from ..commonPy.utility import panic
from ..commonPy.asnParser import AST_Lookup, AST_Leaftypes
from ..commonPy.aadlAST import ApLevelContainer, Param

g_PyDataModel = None
g_iter = 1
g_IFCount = 0
g_BackendFile = None
g_fromPysideToASN1 = []  # type: List[str]
g_fromASN1ToPyside = []  # type: List[str]
g_QUiFile = None
g_bStarted = False       # type: bool
g_firstElem = True       # type: bool
g_asnId = ""             # type: str
g_needsComa = False      # type: bool
g_onceOnly = True        # type: bool


def CleanName(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


def OneTimeOnly(
        unused_modelingLanguage: str,
        unused_asnFile: str,
        subProgram: ApLevelContainer,
        subProgramImplementation: str,
        outputDir: str,
        FVname: str,
        unused_useOSS: bool) -> None:
    global g_PyDataModel
    g_PyDataModel = open(outputDir + 'datamodel.py', 'w')
    g_PyDataModel.write('''#!/usr/bin/python

import DV

FVname = "{fvname}"

tc = {{}}
tm = {{}}
errCodes = {{}}
'''.format(fvname=FVname))

    global g_QUiFile
    g_QUiFile = open(outputDir + 'guilayout.ui', 'w')
    g_QUiFile.write('''<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>MainWindow</class>
 <widget class="TasteMainWindow" name="MainWindow">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>710</width>
    <height>575</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>{fvName}</string>
  </property>
  <property name="tabShape">
   <enum>QTabWidget::Rounded</enum>
  </property>
  <property name="dockOptions">
   <set>QMainWindow::AllowNestedDocks|QMainWindow::AllowTabbedDocks|QMainWindow::AnimatedDocks</set>
  </property>
  <widget class="QWidget" name="centralWidget">
  <layout class="QVBoxLayout" name="verticalLayout">
     <item>
      <widget class="QLabel" name="tasteLogo" native="true">
       <property name="pixmap">
        <pixmap>tasteLogo_white.png</pixmap>
       </property>
      </widget>
     </item>
     <item>
      <widget class="QLabel" name="instructions" native="true">
       <property name="text">
        <string>Available test scripts:</string>
       </property>
      </widget>
     </item>
     <item>
      <widget class="QListWidget" name="msc" native="true"/>
     </item>
     <item>
      <layout class="QHBoxLayout" name="horizontalLayout">
       <item>
        <widget class="QPushButton" name="runMSC">
         <property name="text">
          <string>Run</string>
         </property>
        </widget>
       </item>
       <item>
        <widget class="QPushButton" name="loadMSC">
         <property name="text">
          <string>Load</string>
         </property>
        </widget>
       </item>
       <item>
        <widget class="QPushButton" name="editMSC">
         <property name="text">
          <string>Edit</string>
         </property>
        </widget>
       </item>
      </layout>
     </item>
    </layout>
   </widget>
   <widget class="QStatusBar" name="statusBar"/>
'''.format(fvName=FVname))
    if FVname == "":
        panic("GUI APLCs must have an FV_Name attribute! (%s)\n" %
              subProgram._id + "." + subProgramImplementation)  # pragma: no cover


def OnStartup(
        modelingLanguage: str,
        asnFile: str,
        subProgram: ApLevelContainer,
        subProgramImplementation: str,
        outputDir: str,
        FVname: str,
        useOSS: bool) -> None:
    '''
        Called once per interface (PI or RI)
        (SUBPROGRAM IMPLEMENTATION in mini_cv.aadl)
    '''
    global g_bStarted
    if not g_bStarted:
        g_bStarted = True
        OneTimeOnly(modelingLanguage, asnFile, subProgram,
                    subProgramImplementation, outputDir, FVname, useOSS)

    CleanSP = CleanName(subProgram._id)

    # Create the per-PI/RI backend file that includes Encode/Decode functions
    global g_BackendFile
    g_BackendFile = open(outputDir + '%s_backend.py' % CleanSP, 'w')
    g_BackendFile.write('''#!/usr/bin/python

import sys
import ctypes
import Queue
import datamodel
import DV
import Stubs
try:
    import vn
    import asn1_python
except ImportError:
    # Support both the old and new installation schemes
    from asn1_value_editor import vn, asn1_python

import {asn1Module} as ASN1

# Optional GUI panel for this message - used to forward received TMs
editor = None
'''.format(asn1Module=CleanName(os.path.basename(asnFile))))

    global g_firstElem
    g_firstElem = True
    buttons = []  # type: List[List[str]]
    # RI = TC (Telecommand), PI = TM (Telemetry)
    if modelingLanguage.lower() == 'gui_ri':
        g_BackendFile.write('''
tcId = -1
msgQ = False
udp = False
shared_lib = False
ASN1_AST = None # Set by Scenario.py - point to the ASN.1 AST from Python.stg

# Variable containing a signal that is used to send a message via a dll
send_via_dll = None

try:
    import PythonController
except ImportError:
    pass

# External configuration point - user must select between message queues,
# UDP or shared libraries for exchanging messages with the main binary

def setMsgQ():
    global tcId
    global msgQ
    tcId = PythonController.i_{tcName}
    msgQ = True


def setUDP():
    global udp
    global tcId
    from _InterfaceEnum import i_{fvName}_RI_{tcName}
    tcId = i_{fvName}_RI_{tcName}
    udp = True


def setSharedLib(dll=None):
    # The shared library is loaded and initialized by the caller
    global shared_lib
    global {tcName}_via_shared_lib
    shared_lib = True
    {tcName}_via_shared_lib = dll.{fvName}_PI_{tcName}

'''.format(fvName=FVname, tcName=CleanSP))
        g_PyDataModel.write('\ntc["{tcName}"] = '.format(tcName=CleanSP))
        buttons = ([["sendButton", "Send TC"], ["loadButton", "Load TC"],
                    ["saveButton", "Save TC"]])
        classType = "asn1Editor"
    elif modelingLanguage.lower() == 'gui_pi':
        g_BackendFile.write('''

tmId = -1
shared_lib = None

# Class configured by the GUI with a signal to be emitted when a TM is received
tm_callback = None

try:
    import PythonController
except:
    pass

def setMsgQ():
    global tmId
    tmId = PythonController.i_{tmName}


def setUDP():
    global tmId
    from _InterfaceEnum import i_{fvName}_PI_{tmName}
    tmId = i_{fvName}_PI_{tmName}


def {tmName}(tm_ptr, size):
    """ Callback function when receiving this TM (opengeode-simulator) """
    if editor:
        editor.asn1Instance.SetData(tm_ptr)
        editor.pendingTM = True
        tm_callback.got_tm.emit()


# Callback function prototype - a void* param, and returning nothing
func = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_long)
cmp_func = func({tmName})

def setSharedLib(dll=None):
    # The shared library is loaded and initialized by the caller
    global shared_lib
    shared_lib = dll
    dll.register_{tmName}(cmp_func)

'''.format(tmName=CleanSP, fvName=FVname))
        g_PyDataModel.write('\ntm["{tmName}"] = '.format(tmName=CleanSP))
        buttons = ([["plotButton", "Plot"], ["meterButton", "Meter"],
                    ["unusedButton", "Unused"]])
        classType = "asn1Viewer"

    # global g_QUiFile
    global g_IFCount
    Left = 1
    Right = 2
    g_QUiFile.write('''\
  <widget class="QDockWidget" name="{direction}_{ifCount}">
   <property name="allowedAreas">
    <set>Qt::RightDockWidgetArea</set>
   </property>
   <property name="windowTitle">
    <string>{interfaceName}</string>
   </property>
   <attribute name="dockWidgetArea">
    <number>{widgetArea}</number>
   </attribute>
   <widget class="QWidget" name="dockWidgetContents">
    <layout class="QVBoxLayout" name="verticalLayout">
     <item>
      <widget class="{classType}" name="{interfaceName}" native="true"/>
     </item>
     <item>
      <layout class="QHBoxLayout" name="horizontalLayout">
       <item>
        <widget class="QPushButton" name="{buttons[0][0]}">
         <property name="text">
          <string>{buttons[0][1]}</string>
         </property>
        </widget>
       </item>
       <item>
        <widget class="QPushButton" name="{buttons[1][0]}">
         <property name="text">
          <string>{buttons[1][1]}</string>
         </property>
        </widget>
       </item>
       <item>
        <widget class="QPushButton" name="{buttons[2][0]}">
         <property name="text">
          <string>{buttons[2][1]}</string>
         </property>
        </widget>
       </item>
       <item>
        <widget class="QPushButton" name="customCombo">
         <property name="text">
          <string>Custom</string>
         </property>
        </widget>
       </item>
      </layout>
     </item>
    </layout>
   </widget>
  </widget>
'''.format(direction='tc' if modelingLanguage.lower() == 'gui_ri' else 'tm',
           widgetArea=Right if modelingLanguage.lower() == 'gui_ri' else Left,
           ifCount=g_IFCount, interfaceName=CleanSP, buttons=buttons,
           classType=classType))

    g_IFCount += 1

    # Get ASN.1 type associated with the PI/RI (if any)
    # and create an instance of it in the Encoder file.
    if len(subProgram._params) == 1:
        param = subProgram._params[0]
        CleanASNType = CleanName(param._signal._asnNodename)
        g_BackendFile.write('''
log = None
statusbar = None
udpController = None


def checkConstraints(asnVal):
    \'\'\' Check if the ASN.1 constraints are respected \'\'\'
    # asnVal input is a ctypes instance of an ASN.1 type
    isValid, errCode = asnVal.IsConstraintValid()
    if not isValid:
        errorMsg = datamodel.errCodes[errCode]['name'] + ': Constraint error! Constraint is: ' + datamodel.errCodes[errCode]['constraint']
        if log:
            log.error(errorMsg)
        return False
    else:
        return True


def encode_ACN(asnVal):
    \'\'\' Encore the native Asn1Scc structure in ACN \'\'\'

    # Check the ASN.1 constraints:
    if not checkConstraints(asnVal):
        return

    # Create a stream buffer to host the ACN-encoded data (for saving to file)
    buffer = ASN1.DataStream(DV.{asn1Type}_REQUIRED_BYTES_FOR_ACN_ENCODING)

    try:
        # Encode the value into the buffer
        asnVal.EncodeACN(buffer)
    except:
        if log:
            log.error('ACN Encoding failed')
        return

    return buffer.GetPyString()


def decode_ACN(ACN_encodedBuffer):
    \'\'\' Decode an ACN buffer and place it in a native Asn1Scc type  \'\'\'

    # Create a stream buffer, put the encoded data inside it, and decode from it
    buffer = ASN1.DataStream(DV.{asn1Type}_REQUIRED_BYTES_FOR_ACN_ENCODING)
    buffer.SetFromPyString(ACN_encodedBuffer)
    decoded_value = ASN1.{asn1Type}()
    decoded_value.DecodeACN(buffer)
    return decoded_value


def encode_uPER(asnVal):
    \'\'\' Encode the native Asn1Scc structure in uPER \'\'\'

    # Check the ASN.1 constraints:
    if not checkConstraints(asnVal): return

    # Create a stream buffer to host the UPER encoded data (for saving to file)
    buffer = ASN1.DataStream(DV.{asn1Type}_REQUIRED_BYTES_FOR_ENCODING)

    try:
        # Encode the value into the buffer
        asnVal.Encode(buffer)
    except:
        if log:
            log.error('uPER encoding failed')
        else:
            print '[ERROR] uPER encoding failed'
        return

    return buffer.GetPyString()


def decode_uPER(uPER_encodedBuffer):
    \'\'\' Decode an uPER buffer and place it in a native Asn1Scc type  \'\'\'

    # Create a stream buffer, put the encoded data inside it, and decode it
    buffer = ASN1.DataStream(DV.{asn1Type}_REQUIRED_BYTES_FOR_ENCODING)
    buffer.SetFromPyString(uPER_encodedBuffer)
    decoded_value = ASN1.{asn1Type}()
    decoded_value.Decode(buffer)
    return decoded_value
'''.format(asn1Type=CleanASNType))

        if modelingLanguage.lower() == "gui_pi":
            g_BackendFile.write('''

def decode_TM(rawTM):
    \'\'\' Decode a msgQ message (native encoding) \'\'\'
    tm = ASN1.{asn1Type}()
    tm.SetData(rawTM)
    return tm


def expect(Q, VNvalue, ignoreOther=False, timeout=None):
    \'\'\' Wait for a specific message - optionally ignoring others \'\'\'
    while True:
        try:
            (msgId, pDataFromMQ) = Q.get(block=True, timeout=timeout)
        except Queue.Empty:
            # Timeout expired
            raise IOError('Timeout expired')
        if msgId == tmId:
            #expectedValue = '{{ {interfaceName} ' + VNvalue + ' }}'
            expectedValue = VNvalue
            nativeData = decode_TM(pDataFromMQ)
            receivedValue = nativeData.GSER()
            if asn1_python.compareVnValues(receivedValue, expectedValue):
                Q.task_done()
                return
            else:
                Q.task_done()
                raise ValueError('Received {interfaceName} with wrong data: '\
+ vn.format_gser(receivedValue))
        elif not ignoreOther:
            Q.task_done()
            raise TypeError(
                "Expected {interfaceName} (%s), but received other\
 (%s)" % (str(tmId), str(msgId)))
        else:
            print 'Received other (%s), but still waiting for {interfaceName}'\
 % str(msgId)
            Q.task_done()
'''.format(asn1Type=CleanASNType, interfaceName=CleanSP.replace('_', '-')))

        elif modelingLanguage.lower() == "gui_ri":
            g_BackendFile.write('''


def send_{interfaceName}_VN(tc_gser):
    \''\' Send the TC with from input parameter in ASN.1 Value Notation \''\'
    instance = typeInstance()
    vn.valueNotationToCTypes(gser=tc_gser,
                             dest=instance,
                             sort=ASN1_AST['{asn1Type}'].type,
                             ASN1Mod=ASN1,
                             ASN1_AST=ASN1_AST)

    sendTC(instance)


def sendTC(tc):
    \''\' Depending on the configuration, send to msgQ, UDP or shared lib \''\'
    # tc is a ctypes instance of an ASN.1 type
    if msgQ:
        if checkConstraints(tc):
            try:
                PythonController.Invoke_{interfaceName}(tc)
            except IOError:
                raise
    elif udp:
        UPER_TC = encode_uPER(tc)
        if UPER_TC and udpController:
            udpController.UDP_Invoke(tcId, UPER_TC)
        else:
            if log:
                log.error('UPER Encoding or UDP Sending failed')
            else:
                print '[ERROR] UPER Encoding or UDP Sending failed'

    elif shared_lib:
        # TC is sent in native format
        # ptr = ctypes.cast(tc._ptr.__long__(), ctypes.POINTER(ctypes.c_long))
        # {interfaceName}_via_shared_lib(ptr)
        # The call to the dll will be done by the SDL handler that manages
        # the Undo stack and the the overal system state
        send_via_dll.dll.emit("{interfaceName}",
                              {interfaceName}_via_shared_lib,
                              tc)
'''.format(interfaceName=CleanSP, asn1Type=param._signal._asnNodename))

        global g_fromPysideToASN1
        g_fromPysideToASN1 = ['''

def fromPysideToASN1(_):
    print('DEPRECATED call to "fromPysideToASN1"')
    # Create a native ASN.1 variable of type {asn1Type}
    # {interfaceName} = ASN1.{asn1Type}()
    return None

def typeInstance():
    # Create an intance of an ASN.1 ctype
    return ASN1.{asn1Type}()
'''.format(interfaceName=CleanSP, asn1Type=CleanASNType)]

        global g_fromASN1ToPyside
        g_fromASN1ToPyside = ['''

def fromASN1ToPyside(_):
    print('DEPRECATED call to "fromASN1ToPyside"')
    return None
''']


def WriteCodeForGUIControls(prefixes: List[str],  # pylint: disable=invalid-sequence-index
                            parentControl: List[int],  # pylint: disable=invalid-sequence-index
                            node: AsnNode,
                            subProgram: ApLevelContainer,
                            subProgramImplementation: str,
                            param: Param,
                            leafTypeDict: AST_Leaftypes,
                            names: AST_Lookup,
                            nodeTypename: str='') -> None:
    global g_firstElem
    global g_onceOnly
    global g_asnId
    for prefix in prefixes:
        txtPrefix = re.sub(r'^.*\.', '', prefix)
    if not g_firstElem and g_onceOnly:
        g_PyDataModel.write(",\n")
    else:
        g_asnId = prefixes[0]
        g_firstElem = False

    # Create string to store the Asn1 and python representation of a field
    # (e.g. in asnStr: tc.a[0].b and in pyStr: ["tc"]["a"][0]["b"])
    pyStr = ""  # type: str
    asnStr = prefixes[0]  # type: str
    for i in range(1, len(prefixes)):
        if len(parentControl) >= i:
            asnStr += "[{index}]".format(index=parentControl[i - 1])
        asnStr += prefixes[i][len(prefixes[i - 1]):]

    splitted = prefixes[0].split('.')
    for item in splitted:
        pyStr += '''["{prefixKey}"]'''.format(prefixKey=item)
    for i in range(1, len(prefixes)):
        if len(parentControl) >= i:
            pyStr += "[{index}]".format(index=parentControl[i - 1])
        for item in prefixes[i][len(prefixes[i - 1]):].split('.'):
            if len(item) > 0:
                pyStr += '''["{prefixKey}"]'''.format(prefixKey=item)

    if isinstance(node, (AsnInt, AsnReal, AsnOctetString)):
        if isinstance(node, (AsnInt, AsnReal)):
            if g_onceOnly:
                g_PyDataModel.write(
                    '''{'nodeTypename': '%s', 'type': '%s', 'id': '%s', 'minR': %d, 'maxR': %d}''' % (
                        nodeTypename, node._name, txtPrefix,
                        node._range[0], node._range[1]))

        elif isinstance(node, AsnOctetString):
            if g_onceOnly:
                g_PyDataModel.write(
                    '''{'nodeTypename': '%s', 'type': 'STRING', 'id': '%s', 'minSize': %d, 'maxSize': %d}''' % (
                        nodeTypename, txtPrefix, node._range[0], node._range[1]))

    elif isinstance(node, AsnBool):
        if g_onceOnly:
            g_PyDataModel.write(
                '''{'nodeTypename': '%s', 'type': '%s', 'id': '%s', 'default': 'False'}''' % (
                    nodeTypename, node._name, txtPrefix))

    elif isinstance(node, AsnEnumerated):
        if g_onceOnly:
            global g_needsComa
            g_needsComa = False
            g_PyDataModel.write(
                '''{'nodeTypename': '%s', 'type': '%s', 'id': '%s', 'values':[''' % (
                    nodeTypename, node._name, txtPrefix))
            values = []
            valuesmap = []
            for enum_value in node._members:
                values.append('"' + enum_value[0] + '"')
                valuesmap.append('"%s": %s' % (enum_value[0], enum_value[1]))
                # enum_value[0]: name, enum_value[1]: integer value (or None)
            g_PyDataModel.write(', '.join(values) + ']')
            g_PyDataModel.write(', "valuesInt": {' + ', '.join(valuesmap) + '}}')

    elif isinstance(node, (AsnSequence, AsnChoice, AsnSet)):
        if g_onceOnly:
            g_PyDataModel.write(
                '''{'nodeTypename': '%s', 'type': '%s', 'id': '%s', ''' % (
                    nodeTypename, node._name, txtPrefix))
            if isinstance(node, AsnChoice):
                g_PyDataModel.write('''"choices":[''')
            elif isinstance(node, AsnSequence) or isinstance(node, AsnSet):
                g_PyDataModel.write('''"children":[''')
        # Recurse on children
        if node._members:
            g_firstElem = True
        else:
            # Empty sequence, nothing to set
            pass

        for child in node._members:
            # child[0] is the name of the field
            # child[2] is the string "field_PRESENT" used for choice indexes
            CleanChild = CleanName(child[0])
            childType = child[1]
            if isinstance(childType, AsnMetaMember):
                childType = names[childType._containedType]
            seqPrefix = prefixes[-1]
            prefixes[-1] = prefixes[-1] + "." + CleanChild
            WriteCodeForGUIControls(prefixes, parentControl, childType,
                                    subProgram, subProgramImplementation,
                                    param, leafTypeDict, names)
            prefixes[-1] = seqPrefix
        if g_onceOnly:
            if isinstance(node, AsnChoice):
                g_PyDataModel.write('], "choiceIdx": {')
                # the mapping choice->DV.choice_PRESENT is needed by the GUIs
                indexes = []
                for child in node._members:
                    indexes.append('"%s": DV.%s' % (CleanName(child[0]),
                                                    CleanName(child[2])))
                g_PyDataModel.write("%s}}" % ','.join(indexes))

            else:
                g_PyDataModel.write("]}")
    elif isinstance(node, (AsnSequenceOf, AsnSetOf)):
        if g_onceOnly:
            g_PyDataModel.write(
                "{'nodeTypename': '%s', 'type': 'SEQOF', 'id': '%s', 'minSize': %d, 'maxSize': %d, 'seqoftype':" % (
                    nodeTypename, txtPrefix, node._range[0], node._range[1]))
        containedNode = node._containedType
        if isinstance(containedNode, str):
            containedNode = names[containedNode]
        g_firstElem = True
        prefixes.append(prefixes[-1])
        l_lock = False
        for i in range(node._range[1]):
            parentControl.append(i)
            WriteCodeForGUIControls(prefixes,
                                    parentControl,
                                    containedNode,
                                    subProgram,
                                    subProgramImplementation,
                                    param,
                                    leafTypeDict,
                                    names)
            if g_onceOnly:
                g_PyDataModel.write("\n}")
            # l_lock prevents g_onceOnly to be reset during a recursive call
            if g_onceOnly:
                g_onceOnly = False
                l_lock = True
            del parentControl[-1]
        if l_lock:
            g_onceOnly = True
        del prefixes[-1]
    else:  # pragma: nocover
        panic("GUI codegen doesn't support this type yet (%s)" % str(node))  # pragma: nocover


def Common(
        nodeTypename: str,
        node: AsnNode,
        subProgram: ApLevelContainer,
        subProgramImplementation: str,
        param: Param,
        leafTypeDict: AST_Leaftypes,
        names: AST_Lookup) -> None:
    control = CleanName(subProgram._id)
    WriteCodeForGUIControls([control],   # prefixes, start with interface name
                            [],          # parentControl
                            node,
                            subProgram,
                            subProgramImplementation,
                            param,
                            leafTypeDict,
                            names,
                            nodeTypename)
    g_BackendFile.write(''.join(g_fromPysideToASN1))
    g_BackendFile.write(''.join(g_fromASN1ToPyside))
    g_BackendFile.close()


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
    # global g_PyDataModel
    # global g_QUiFile
    g_PyDataModel.write("\n")
    g_QUiFile.write(''' </widget>
 <layoutdefault spacing="6" margin="11"/>
 <customwidgets>
     <customwidget>
          <class>asn1Editor</class>
          <extends>QWidget</extends>
          <header>asn1_value_editor</header>
     </customwidget>
     <customwidget>
          <class>asn1Viewer</class>
          <extends>QWidget</extends>
          <header>asn1_value_editor</header>
     </customwidget>
     <customwidget>
          <class>TasteMainWindow</class>
          <extends>QMainWindow</extends>
          <header>TasteMainWindow</header>
     </customwidget>
 </customwidgets>
 <resources/>
 <connections/>
</ui>
''')
    g_PyDataModel.close()
    g_QUiFile.close()
    # This is for restart the module when it is used.
    global g_bStarted
    g_bStarted = False
