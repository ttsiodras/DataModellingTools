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
import sys
import re
import copy
import traceback
import DV


def panicWithCallStack(msg):
    """Print the panic msg in color, report the call stack, and die"""
    print >>sys.stderr, "\n"+chr(27)+"[35m" + msg + chr(27) + "[0m\n"
    print >>sys.stderr, "\nCall stack was:\n%s\n" % ("".join(traceback.format_stack()[:-1]))
    sys.exit(1)


def CleanNameAsPythonWants(name):
    """ASN.1 ids have minuses... turn non-ID chars to '_'"""
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)
Clean = CleanNameAsPythonWants


def myassert(b):
    """assert that shows the call stack when it fails"""
    if not b:
        panicWithCallStack("Assertion failed...")


class DataStream:
    """ASN1SCC BitStream equivalent"""
    def __init__(self, bufferSize):
        """bufferSize: use the DV.TYPENAME_REQUIRED_BYTES_FOR_ENCODING"""
        myassert(isinstance(bufferSize, int))
        self._bs = DV.BitStream()
        self._pMem = DV.new_byte_SWIG_PTR(bufferSize)
        self._bufferSize = bufferSize
        DV.BitStream_Init(self._bs, self._pMem, self._bufferSize)

    def __del__(self):
        DV.delete_byte_SWIG_PTR(self._pMem)

    def Reset(self):
        """Rewinds the currentByte and currentBit to the start"""
        self._bs.currentBit = 0
        self._bs.currentByte = 0

    def GetPyString(self):
        #print "Reading",
        msg = ""
        for i in xrange(0, self._bs.currentByte + ((self._bs.currentBit+7)/8)):
            b = DV.byte_SWIG_PTR_getitem(self._pMem, i)
            msg += chr(b)
            #print b, ",",
        #print "EOF"
        return msg

    def SetFromPyString(self, data):
        strLength = len(data)
        assert(self._bs.count >= strLength)
        self._bs.count = strLength
        #print "Writing",
        for i in xrange(0, strLength):
            b = ord(data[i])
            #print b, ",",
            DV.byte_SWIG_PTR_setitem(self._pMem, i, b)
        #print "EOF"


class COMMON(object):
    """This class is used to implement ALL the Python "proxy" classes for
ASN1SCC types.

It uses the __getattr__ call to hook into all the accesses that Python
considers "unexpected". Therefore, when the script does this...

    a = T_SEQUENCE()
    print a.x.Get()
    a.x.Set(12)

... __getattr__ is called to ask us how to provide a ".x" member.
We do two things to cope:

(1) we form the equivalent path to the C getter/setter function
    (in self._Caccessor)
(2) we form a list of params, which is basically the indexes of
    whatever arrays we meet in the access path

So if the script does...

    a.x.y[0].z.k[2].w.Get()

then the params list carries [0,2], to pass it as an argument to the
C getter when it is called (in response to the "Get" method call).

Some key points:
    When the chain ends (in a .Get, .Set, .GetLength or .SetLength
call), we have to reset the "paths" we have formed, so that the
next chain will restart from the beginning. That's what the Reset
method does.
However, we also have some helper functions for OCTET STRINGs:
GetPyString and SetFromPyString. These have to do a per-byte loop,
and if they used the "Get" and "Set" as they originally were,
the path would be reset after accessing the [0] element...
So we added a keyword boolean param called "reset", which disables
this Reset when it is used from within GetPyString and
SetFromPyString.
    Another keyword param is postfix: it is simply used to allow
re-use of the Get and Set code for the GetLength and SetLength
members of SEQUENCEOF/SETOFs and OCTETSTRINGs:

An example for SetLength:

  T_SEQUENCE ::= SEQUENCE { y SEQUENCE (SIZE(4)) OF INTEGER }

    a = T_SEQUENCE()
    a.y.SetLength(4)
    a.y[0].Set(1)
    a.y[1].Set(4)
    a.y[2].Set(9)
    a.y[3].Set(16)
"""

    allowed = ["_nodeTypeName", "_ptr", "_pErr", "_Caccessor", "_accessPath", "_params"]
#, "Get", "GetLength", "Set", "SetLength", "Reset", "Encode", "Decode", "SetFromPyString", "GetPyString", "allowed"]

    def __init__(self, nodeTypeName):
        myassert(isinstance(nodeTypeName, str))
        self._nodeTypeName = nodeTypeName
        self._ptr = getattr(DV, "new_" + Clean(nodeTypeName) + "_SWIG_PTR")(1)
        getattr(DV, Clean(nodeTypeName) + "_Initialize")(self._ptr)
        self._pErr = DV.new_int_SWIG_PTR(1)
        self.Reset()

    def Reset(self, state=None):
        if state is None:
            self._Caccessor = ""
            self._params = []
            self._accessPath = ""
        else:
            self._Caccessor, self._params, self._accessPath = state[0][:], copy.deepcopy(state[1]), state[2][:]

    def GetState(self):
        return self._Caccessor[:], copy.deepcopy(self._params), self._accessPath[:]

    def __del__(self):
        DV.delete_int_SWIG_PTR(self._pErr)
        getattr(DV, "delete_" + Clean(self._nodeTypeName) + "_SWIG_PTR")(self._ptr)

    def __str__(self):
        return "Choose the information you want - whole-structure or sequence dump not supported."

    def __getattr__(self, x):
        self._Caccessor += "_"+Clean(x)
        self._accessPath += "."+x
        return self

    def __setattr__(self, name, value):
        if name not in COMMON.allowed:
            self.Reset()
            panicWithCallStack("You can only use .Set(XYZ) and .SetLength(XYZ) to assign values, don't use '='")
        object.__setattr__(self, name, value)

    def __getitem__(self, idx):
        self._Caccessor += "_iDx"
        self._params.append(idx)
        self._accessPath += "[" + str(idx) + "]"
        return self

    def Get(self, **args):  # postfix="", reset=True
        try:
            bridgeFunc = getattr(DV, Clean(self._nodeTypeName) + "_" + self._Caccessor + "_Get"+args.get("postfix", ""))
            retVal = bridgeFunc(self._ptr, *self._params)
        except:
            oldAP = self._accessPath
            if args.get("reset", True):
                self.Reset()
            panicWithCallStack("The access path you used (%s) is not valid." % oldAP)
        if args.get("reset", True):
            self.Reset()
        return retVal

    def Set(self, value, **args):  # postfix="", reset=True
        try:
            #print Clean(self._nodeTypeName) + "_" + self._Caccessor + "_Set"+postfix
            bridgeFunc = getattr(DV, Clean(self._nodeTypeName) + "_" + self._Caccessor + "_Set"+args.get("postfix", ""))
            self._params.append(value)
            bridgeFunc(self._ptr, *self._params)
            self._params.pop()
        except:
            oldAP = self._accessPath
            if args.get("reset", True):
                self.Reset()
            panicWithCallStack(
                "The access path you used (%s) or the value you tried to assign (%s) is not valid." %
                (oldAP, str(value)))
        if args.get("reset", True):
            self.Reset()

    def GetLength(self, reset=True):
        return self.Get(postfix="Length", reset=reset)

    def SetLength(self, value, reset=True):
        self.Set(value, postfix="Length", reset=reset)

    def Encode(self, bitstream, bACN=False):
        """Returns (booleanSuccess, ASN1SCC iErrorCode)
grep for the errorcode value inside ASN1SCC generated headers."""
        myassert(isinstance(bitstream, DataStream))
        DV.BitStream_Init(bitstream._bs, bitstream._pMem, bitstream._bufferSize)
        suffix = "_ACN_Encode" if bACN else "_Encode"
        EncodeFunc = getattr(DV, Clean(self._nodeTypeName) + suffix)
        success = EncodeFunc(self._ptr, bitstream._bs, self._pErr, True)
        if not success:
            panicWithCallStack("Error in Encode, code:%d" % DV.int_SWIG_PTR_getitem(self._pErr, 0))

    def Decode(self, bitstream, bACN=False):
        """Returns (booleanSuccess, ASN1SCC iErrorCode)
grep for the errorcode value inside ASN1SCC generated headers."""
        myassert(isinstance(bitstream, DataStream))
        suffix = "_ACN_Decode" if bACN else "_Decode"
        DecodeFunc = getattr(DV, Clean(self._nodeTypeName) + suffix)
        success = DecodeFunc(self._ptr, bitstream._bs, self._pErr)
        if not success:
            panicWithCallStack("Error in Decode, code:%d" % DV.int_SWIG_PTR_getitem(self._pErr, 0))

    def EncodeACN(self, bitstream):
        self.Encode(bitstream, True)

    def DecodeACN(self, bitstream):
        self.Decode(bitstream, True)

# Type-specific helpers...

# OCTET STRING

    def SetFromPyString(self, src):
        strLength = len(src)
        self.SetLength(strLength, False)
        self._Caccessor += "_iDx"
        accessPath = self._accessPath
        for idx in xrange(0, strLength):
            self._params.append(idx)
            self._accessPath = accessPath + "[" + str(idx) + "]"
            self.Set(ord(src[idx]), reset=False)
            self._params.pop()
        self.Reset()

    def GetPyString(self):
        retval = ""
        strLength = self.GetLength(False)
        self._Caccessor += "_iDx"
        accessPath = self._accessPath
        for idx in xrange(0, strLength):
            self._params.append(idx)
            self._accessPath = accessPath + "[" + str(idx) + "]"
            retval += chr(self.Get(reset=False))
            self._params.pop()
        self.Reset()
        return retval
