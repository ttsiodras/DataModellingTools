# (C) Semantix Information Technologies.
#
# Semantix Information Technologies is licensing the code of the
# Data Modelling Tools (DMT) in the following dual-license mode:
#
# Commercial Developer License:
#       The DMT Commercial Developer License is the appropriate version
# to use for the development of proprietary and/or commercial software.
# This version is for developers/companies who do not want to share
# the source code they develop with others or otherwise comply with the
# terms of the GNU Lesser General Public License version 3.
#
# GNU LGPL v. 2.1:
#       This version of DMT is the one to use for the development of
# non-commercial applications, when you are willing to comply
# with the terms of the GNU Lesser General Public License version 3.
#
# The features of the two licenses are summarized below:
#
#                       Commercial
#                       Developer               LGPL
#                       License
#
# License cost          License fee charged     No license fee
#
# Must provide source
# code changes to DMT   No, modifications can   Yes, all source code
#                       be closed               must be provided back
#
# Can create            Yes, that is,           No, applications are subject
# proprietary           no source code needs    to the LGPL and all source code
# applications          to be disclosed         must be made available
#
# Support               Yes, 12 months of       No, but available separately
#                       premium technical       for purchase
#                       support
#
# Charge for Runtimes   None                    None

from typing import Tuple, Union, Dict, Any  # NOQA pylint: disable=unused-import

g_apLevelContainers = {}  # type: Dict[str, ApLevelContainer]

g_subProgramImplementations = []  # type: List[Tuple[str,str,str,str]]
g_processImplementations = []  # type: List[Tuple[str,str,str,str]]
g_threadImplementations = []  # type: List[Tuple[str,str,str,str]]

# AST classes


class AadlParameter:
    def __init__(self, direction: str, typ: str) -> None:
        assert direction in ['IN', 'OUT', 'INOUT']
        self._direction = direction
        self._type = typ
        self._encoding = ''


class AadlSubProgramFeature:
    def __init__(self, iid: str, parameter: AadlParameter) -> None:
        self._id = iid
        self._parameter = parameter


class AadlPropertyAssociationNoModes:
    def __init__(self, name: str, pe: Any) -> None:
        self._name = name
        self._propertyExpressionOrList = pe


class AadlPort:
    def __init__(self, direction: str, typ: str) -> None:
        self._direction = direction
        self._type = typ
        self._encoding = ''


class AadlEventPort:
    def __init__(self, direction: str, sp: 'ApLevelContainer') -> None:
        self._direction = direction
        self._sp = sp
        self._encoding = ''

    def __repr__(self) -> str:
        result = "AadlEventPort(" + self._direction + ","
        if self._sp:
            result += str(self._sp)
        result += ")"
        return result


class AadlEventDataPort(AadlPort):
    def __init__(self, direction: str, typ: str) -> None:
        AadlPort.__init__(self, direction, typ)


class AadlThreadFeature:
    def __init__(self, iid: str, port: AadlPort) -> None:
        assert isinstance(port, AadlPort)
        self._id = iid
        self._port = port


class AadlProcessFeature:
    def __init__(self, iid: str, port: AadlPort) -> None:
        assert isinstance(port, AadlPort)
        self._id = iid
        self._port = port


class AadlContainedPropertyAssociation:
    def __init__(self, name: str, value: Any) -> None:
        self._name = name
        self._value = value


class Signal:
    def __init__(self, asnFilename: str, asnNodename: str, asnSize: int) -> None:
        self._asnFilename = asnFilename
        self._asnNodename = asnNodename
        self._asnSize = asnSize


# class Port:
#     def __init__(self, signal):
#         self._signal = signal
#
#
# class DualPort(Port):
#     def __init__(self, signal):
#         Port.__init__(self, signal)
#
#
# class UniPort(Port):
#     def __init__(self, signal):
#         Port.__init__(self, signal)
#
#
# class IncomingUniPort(UniPort):
#     def __init__(self, signal):
#         UniPort.__init__(self, signal)
#
#
# class OutgoingUniPort(UniPort):
#     def __init__(self, signal):
#         UniPort.__init__(self, signal)


class Param:
    def __init__(self,
                 aplcID: str,
                 iid: str,
                 signal: Signal,
                 sourceElement: Union[AadlPort, AadlEventDataPort, AadlParameter]) -> None:
        self._id = iid
        # It is the Process, Thread or Subprogram ID
        self._aplcID = aplcID
        # Could be string (i.e. AADL DataType name) or Signal (i.e. asnFilename, asnNodename)
        self._signal = signal
        self._sourceElement = sourceElement  # Could be AadlPort, AadlEventDataPort, AadlParameter


class InParam(Param):
    def __init__(self,
                 aplcID: str,
                 iid: str,
                 signal: Signal,
                 sourceElement: Union[AadlPort, AadlEventDataPort, AadlParameter]) -> None:
        Param.__init__(self, aplcID, iid, signal, sourceElement)


class OutParam(Param):
    def __init__(self,
                 aplcID: str,
                 iid: str,
                 signal: Signal,
                 sourceElement: Union[AadlPort, AadlEventDataPort, AadlParameter]) -> None:
        Param.__init__(self, aplcID, iid, signal, sourceElement)


class InOutParam(Param):
    def __init__(self,
                 aplcID: str,
                 iid: str,
                 signal: Signal,
                 sourceElement: Union[AadlPort, AadlEventDataPort, AadlParameter]) -> None:
        Param.__init__(self, aplcID, iid, signal, sourceElement)


class UniquePortIdentifier:
    def __init__(self, componentId: str, portId: str) -> None:
        self._componentId = componentId
        self._portId = portId


class ApLevelContainer:
    def __init__(self, iid: str) -> None:
        self._id = iid
        self._params = []  # type: List[Param]
        self._connections = []  # type: List[Connection]
        self._language = None  # type: str

    def AddConnection(self, srcUniquePortId: UniquePortIdentifier, destUniquePortId: UniquePortIdentifier) -> None:
        if srcUniquePortId._componentId is None:
            srcUniquePortId._componentId = self._id
        if destUniquePortId._componentId is None:
            destUniquePortId._componentId = self._id
        self._connections.append(Connection(srcUniquePortId, destUniquePortId))

    def AddParam(self, param: Param) -> None:
        self._params.append(param)

    def SetLanguage(self, language: str) -> None:
        self._language = language


class Connection:
    def __init__(self, fromC: UniquePortIdentifier, toC: UniquePortIdentifier) -> None:
        self._from = fromC
        self._to = toC
