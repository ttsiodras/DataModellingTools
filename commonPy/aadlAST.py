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
# terms of the GNU General Public License version 2.1.
#
# GNU GPL v. 2.1:
#       This version of DMT is the one to use for the development of
# non-commercial applications, when you are willing to comply
# with the terms of the GNU General Public License version 2.1.
#
# The features of the two licenses are summarized below:
#
#                       Commercial
#                       Developer               GPL
#                       License
#
# License cost          License fee charged     No license fee
#
# Must provide source
# code changes to DMT   No, modifications can   Yes, all source code
#                       be closed               must be provided back
#
# Can create            Yes, that is,           No, applications are subject
# proprietary           no source code needs    to the GPL and all source code
# applications          to be disclosed         must be made available
#
# Support               Yes, 12 months of       No, but available separately
#                       premium technical       for purchase
#                       support
#
# Charge for Runtimes   None                    None
#
#g_nodes    = []
g_signals = {}
g_apLevelContainers = {}

g_subProgramImplementations = []
g_processImplementations = []
g_threadImplementations = []

g_systems = {}

# AST classes


class AadlParameter:
    def __init__(self, direction, type):
        assert direction in ['IN', 'OUT', 'INOUT']
        self._direction = direction
        self._type = type


class AadlSubProgramFeature:
    def __init__(self, id, parameter):
        self._id = id
        self._parameter = parameter


class AadlPropertyAssociationNoModes:
    def __init__(self, name, pe):
        self._name = name
        self._propertyExpressionOrList = pe


class AadlPort:
    def __init__(self, direction, type):
        self._direction = direction
        self._type = type


class AadlEventPort:
    def __init__(self, direction, sp):
        self._direction = direction
        self._sp = sp

    def __repr__(self):
        result = "AadlEventPort("+self._direction+","
        if self._sp:
            result+=self._sp
        result+=")"
        return result


class AadlEventDataPort(AadlPort):
    def __init__(self, direction, type):
        AadlPort.__init__(self, direction, type)


class AadlThreadFeature:
    def __init__(self, id, port):
        assert(isinstance(port, AadlPort))
        self._id = id
        self._port = port


class AadlProcessFeature:
    def __init__(self, id, port):
        assert(isinstance(port, AadlPort))
        self._id = id
        self._port = port


class AadlContainedPropertyAssociation:
    def __init__(self, name, value):
        self._name = name
        self._value = value


class Signal:
    def __init__(self, asnFilename, asnNodename, asnSize):
        self._asnFilename = asnFilename
        self._asnNodename = asnNodename
        self._asnSize = asnSize


class Port:
    def __init__(self, signal):
        self._signal = signal


class DualPort(Port):
    def __init__(self, signal):
        Port.__init__(self, signal)


class UniPort(Port):
    def __init__(self, signal):
        Port.__init__(self, signal)


class IncomingUniPort(UniPort):
    def __init__(self, signal):
        UniPort.__init__(self, signal)


class OutgoingUniPort(UniPort):
    def __init__(self, signal):
        UniPort.__init__(self, signal)


class ApLevelContainer:
    def __init__(self, id):
        self._id = id
        self._calls = []
        self._params = []
        self._connections = []
        self._language = None

    def AddCalledAPLC(self, idAPLC):
        self._calls.append(idAPLC)

    def AddConnection(self, srcUniquePortId, destUniquePortId):
        if srcUniquePortId._componentId is None:
            srcUniquePortId._componentId = self._id
        if destUniquePortId._componentId is None:
            destUniquePortId._componentId = self._id
        self._connections.append(Connection(srcUniquePortId, destUniquePortId))

    def AddParam(self, param):
        self._params.append(param)

    def SetLanguage(self, language):
        self._language = language


class Param:
    def __init__(self, aplcID, id, signal, sourceElement):
        self._id = id
        # It is the Process, Thread or Subprogram ID
        self._aplcID = aplcID
        # Could be string (i.e. AADL DataType name) or Signal (i.e. asnFilename, asnNodename)
        self._signal = signal
        self._sourceElement = sourceElement  # Could be AadlPort, AadlEventDataPort, AadlParameter


class InParam(Param):
    def __init__(self, aplcID, id, signal, sourceElement):
        Param.__init__(self, aplcID, id, signal, sourceElement)


class OutParam(Param):
    def __init__(self, aplcID, id, signal, sourceElement):
        Param.__init__(self, aplcID, id, signal, sourceElement)


class InOutParam(Param):
    def __init__(self, aplcID, id, signal, sourceElement):
        Param.__init__(self, aplcID, id, signal, sourceElement)


class UniquePortIdentifier:
    def __init__(self, componentId, portId):
        self._componentId = componentId
        self._portId = portId


class Connection:
    def __init__(self, fromC, toC):
        self._from = fromC
        self._to = toC
