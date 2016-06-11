### $ANTLR 2.7.7 (20120126): "aadl.g" -> "AadlParser.py"$
### import antlr and other modules ..
import sys
import antlr

version = sys.version.split()[0]
if version < '2.2.1':
    False = 0
if version < '2.3':
    True = not False
### header action >>> 

### header action <<< 
### preamble action>>>
from commonPy.aadlAST import *
from commonPy.utility import panic
import commonPy.configMT
global g_currentPackage
g_currentPackage = ""
### preamble action <<<

### import antlr.Token 
from antlr import Token
### >>>The Known Token Types <<<
SKIP                = antlr.SKIP
INVALID_TYPE        = antlr.INVALID_TYPE
EOF_TYPE            = antlr.EOF_TYPE
EOF                 = antlr.EOF
NULL_TREE_LOOKAHEAD = antlr.NULL_TREE_LOOKAHEAD
MIN_USER_TYPE       = antlr.MIN_USER_TYPE
PACKAGE = 4
END = 5
SEMI = 6
PUBLIC = 7
PRIVATE = 8
IDENT = 9
DOUBLECOLON = 10
NONE = 11
THREAD = 12
EXTENDS = 13
GROUP = 14
PROCESS = 15
SYSTEM = 16
SUBPROGRAM = 17
DATA = 18
PROCESSOR = 19
MEMORY = 20
BUS = 21
DEVICE = 22
DOT = 23
IMPL = 24
FEATURES = 25
COLON = 26
REFINED = 27
TO = 28
PROVIDES = 29
REQUIRES = 30
REFINES = 31
TYPE = 32
SUBCOMPONENTS = 33
ANNEX = 34
ANNEX_TEXT = 35
PROPERTY = 36
SET = 37
IS = 38
BOOLEAN = 39
STRING = 40
ENUMERATION = 41
LPAREN = 42
COMMA = 43
RPAREN = 44
UNITS = 45
ASSIGN = 46
STAR = 47
REAL = 48
INTEGER = 49
DOTDOT = 50
PLUS = 51
MINUS = 52
NUMERIC_LIT = 53
RANGE = 54
OF = 55
CLASSIFIER = 56
REFERENCE = 57
CONNECTIONS = 58
SERVER = 59
ACCESS = 60
INHERIT = 61
APPLIES = 62
ALL = 63
MODE = 64
PORT = 65
EVENT = 66
FLOW = 67
PARAMETER = 68
LIST = 69
CONSTANT = 70
DELTA = 71
PROPERTIES = 72
LCURLY = 73
RCURLY = 74
ASSIGNPLUS = 75
VALUE = 76
IN = 77
BINDING = 78
OR = 79
AND = 80
TRUE = 81
FALSE = 82
NOT = 83
STRING_LITERAL = 84
CALLS = 85
MODES = 86
INITIAL = 87
LTRANS = 88
RTRANS = 89
ARROW = 90
OUT = 91
INVERSE = 92
DARROW = 93
FLOWS = 94
SOURCE = 95
SINK = 96
PATH = 97
AADLSPEC = 98
NOTT = 99
TRANSITIONS = 100
HASH = 101
DIGIT = 102
EXPONENT = 103
INT_EXPONENT = 104
EXTENDED_DIGIT = 105
BASED_INTEGER = 106
BASE = 107
ESC = 108
HEX_DIGIT = 109
WS = 110
SL_COMMENT = 111

class Parser(antlr.LLkParser):
    ### user action >>>
    ### user action <<<
    
    def __init__(self, *args, **kwargs):
        antlr.LLkParser.__init__(self, *args, **kwargs)
        self.tokenNames = _tokenNames
        
    def aadl_specification(self):    
        
        pass
        _cnt3= 0
        while True:
            if (_tokenSet_0.member(self.LA(1))):
                pass
                self.aadl_declaration()
            else:
                break
            
            _cnt3 += 1
        if _cnt3 < 1:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        self.match(EOF_TYPE)
    
    def aadl_declaration(self):    
        
        pass
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [THREAD,PROCESS,SYSTEM,SUBPROGRAM,DATA,PROCESSOR,MEMORY,BUS,DEVICE]:
            pass
            self.component_classifier()
        elif la1 and la1 in [PORT]:
            pass
            self.port_group_type()
        elif la1 and la1 in [ANNEX]:
            pass
            self.annex_library()
        elif la1 and la1 in [PACKAGE]:
            pass
            self.package_spec()
        elif la1 and la1 in [PROPERTY]:
            pass
            self.property_set()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def component_classifier(self):    
        
        pass
        if (self.LA(1)==THREAD) and (self.LA(2)==IDENT):
            pass
            self.thread_type()
        elif (self.LA(1)==THREAD) and (self.LA(2)==IMPL):
            pass
            self.thread_implementation()
        elif (self.LA(1)==THREAD) and (self.LA(2)==GROUP) and (self.LA(3)==IDENT):
            pass
            self.thread_group_type()
        elif (self.LA(1)==THREAD) and (self.LA(2)==GROUP) and (self.LA(3)==IMPL):
            pass
            self.thread_group_implementation()
        elif (self.LA(1)==SYSTEM) and (self.LA(2)==IDENT):
            pass
            self.system_type()
        elif (self.LA(1)==SYSTEM) and (self.LA(2)==IMPL):
            pass
            self.system_implementation()
        elif (self.LA(1)==DATA) and (self.LA(2)==IDENT):
            pass
            self.data_type()
        elif (self.LA(1)==DATA) and (self.LA(2)==IMPL):
            pass
            self.data_implementation()
        elif (self.LA(1)==SUBPROGRAM) and (self.LA(2)==IDENT):
            pass
            self.subprogram_type()
        elif (self.LA(1)==SUBPROGRAM) and (self.LA(2)==IMPL):
            pass
            self.subprogram_implementation()
        elif (self.LA(1)==PROCESS) and (self.LA(2)==IDENT):
            pass
            self.process_type()
        elif (self.LA(1)==PROCESS) and (self.LA(2)==IMPL):
            pass
            self.process_implementation()
        elif (self.LA(1)==PROCESSOR) and (self.LA(2)==IDENT):
            pass
            self.processor_type()
        elif (self.LA(1)==PROCESSOR) and (self.LA(2)==IMPL):
            pass
            self.processor_implementation()
        elif (self.LA(1)==MEMORY) and (self.LA(2)==IDENT):
            pass
            self.memory_type()
        elif (self.LA(1)==MEMORY) and (self.LA(2)==IMPL):
            pass
            self.memory_implementation()
        elif (self.LA(1)==BUS) and (self.LA(2)==IDENT):
            pass
            self.bus_type()
        elif (self.LA(1)==BUS) and (self.LA(2)==IMPL):
            pass
            self.bus_implementation()
        elif (self.LA(1)==DEVICE) and (self.LA(2)==IDENT):
            pass
            self.device_type()
        elif (self.LA(1)==DEVICE) and (self.LA(2)==IMPL):
            pass
            self.device_implementation()
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
    
    def port_group_type(self):    
        
        defid = None
        id = None
        id2 = None
        pass
        self.match(PORT)
        self.match(GROUP)
        defid = self.LT(1)
        self.match(IDENT)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [EXTENDS]:
            pass
            self.match(EXTENDS)
            self.unique_type_name()
        elif la1 and la1 in [FEATURES,INVERSE]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FEATURES]:
            pass
            pass
            self.match(FEATURES)
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    id = self.LT(1)
                    self.match(IDENT)
                    self.match(COLON)
                    la1 = self.LA(1)
                    if False:
                        pass
                    elif la1 and la1 in [REFINED]:
                        pass
                        self.match(REFINED)
                        self.match(TO)
                    elif la1 and la1 in [PORT,IN,OUT]:
                        pass
                    else:
                            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                        
                    la1 = self.LA(1)
                    if False:
                        pass
                    elif la1 and la1 in [IN,OUT]:
                        pass
                        p=self.port_spec()
                    elif la1 and la1 in [PORT]:
                        pass
                        self.port_group_spec()
                    else:
                            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                        
                else:
                    break
                
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [INVERSE]:
                pass
                self.match(INVERSE)
                self.match(OF)
                self.unique_type_name()
            elif la1 and la1 in [END,ANNEX,PROPERTIES]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
        elif la1 and la1 in [INVERSE]:
            pass
            pass
            self.match(INVERSE)
            self.match(OF)
            self.unique_type_name()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PROPERTIES]:
            pass
            pa=self.propertyAssociations_no_modes()
        elif la1 and la1 in [END,ANNEX]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [ANNEX]:
            pass
            self.annex_subclause()
        elif la1 and la1 in [END]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(END)
        id2 = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def annex_library(self):    
        
        id = None
        at = None
        pass
        self.match(ANNEX)
        id = self.LT(1)
        self.match(IDENT)
        at = self.LT(1)
        self.match(ANNEX_TEXT)
        self.match(SEMI)
    
    def package_spec(self):    
        
        fl = None
        sl = None
        pass
        fl = self.LT(1)
        self.match(PACKAGE)
        p=self.package_name()
        if not self.inputState.guessing:
            global g_currentPackage
            g_currentPackage = p
            #print "Currently parsing package", g_currentPackage
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PUBLIC]:
            pass
            pass
            self.public_part()
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [PRIVATE]:
                pass
                self.private_part()
            elif la1 and la1 in [END]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
        elif la1 and la1 in [PRIVATE]:
            pass
            self.private_part()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(END)
        pn=self.package_name()
        sl = self.LT(1)
        self.match(SEMI)
    
    def property_set(self):    
        
        ps_id = None
        id = None
        ps_id2 = None
        pass
        self.match(PROPERTY)
        self.match(SET)
        ps_id = self.LT(1)
        self.match(IDENT)
        self.match(IS)
        _cnt307= 0
        while True:
            if (self.LA(1)==IDENT):
                pass
                id = self.LT(1)
                self.match(IDENT)
                self.match(COLON)
                la1 = self.LA(1)
                if False:
                    pass
                elif la1 and la1 in [CONSTANT]:
                    pass
                    self.property_constant()
                elif la1 and la1 in [TYPE]:
                    pass
                    self.property_type_declaration()
                elif la1 and la1 in [IDENT,BOOLEAN,STRING,ENUMERATION,UNITS,REAL,INTEGER,RANGE,CLASSIFIER,REFERENCE,ACCESS,INHERIT,LIST]:
                    pass
                    self.property_name_declaration()
                else:
                        raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                    
            else:
                break
            
            _cnt307 += 1
        if _cnt307 < 1:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        self.match(END)
        ps_id2 = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def thread_type(self):    
        
        id = None
        eid = None
        sl = None
        pass
        self.match(THREAD)
        id = self.LT(1)
        self.match(IDENT)
        if not self.inputState.guessing:
            #print "Now defining THREAD", id.getText()
            #print threadFeatures
            if not commonPy.configMT.g_bOnlySubprograms:
               sp = ApLevelContainer(id.getText())
               g_apLevelContainers[id.getText()] = sp
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [EXTENDS]:
            pass
            self.match(EXTENDS)
            self.unique_type_name()
        elif la1 and la1 in [END,FEATURES,ANNEX,PROPERTIES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FEATURES]:
            pass
            threadFeatures=self.featuresThread()
            if not self.inputState.guessing:
                if not commonPy.configMT.g_bOnlySubprograms:
                   for threadFeature in threadFeatures:
                      if threadFeature == None: continue
                      if threadFeature._port._type not in g_signals:
                         # panic("Line %d: Referenced datatype (%s) not defined yet" % \
                         #     (id.getLine(),threadFeature._port._type))
                         signal = threadFeature._port._type
                      else:
                         signal = g_signals[threadFeature._port._type]
                      if threadFeature._port._direction == "IN":
                         param = InParam(id.getText(), threadFeature._id, signal, threadFeature._port)
                      elif threadFeature._port._direction == "OUT":
                         param = OutParam(id.getText(), threadFeature._id, signal, threadFeature._port)
                      elif threadFeature._port._direction == "INOUT":
                         param = InOutParam(id.getText(), threadFeature._id, signal, threadFeature._port)
                      else:
                         panic("No IN/OUT/INOUT specified!")
                      sp.AddParam(param)
        elif la1 and la1 in [END,ANNEX,PROPERTIES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FLOWS]:
            pass
            self.flow_specs()
        elif la1 and la1 in [END,ANNEX,PROPERTIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PROPERTIES]:
            pass
            properties=self.propertyAssociations_no_modes()
            if not self.inputState.guessing:
                if not commonPy.configMT.g_bOnlySubprograms:
                   if properties != None:
                       if id.getText() not in g_apLevelContainers:
                          panic("Line %d: THREAD (%s) must first be declared before it is PROPERTIES-ed"  % (id.getLine(), id.getText()))
                       sp = g_apLevelContainers[id.getText()]
                       for property in properties:
                          if property._name[-15:].lower() == "source_language":
                              stripQuotes = property._propertyExpressionOrList.replace("\"", "")
                              sp.SetLanguage(stripQuotes)
        elif la1 and la1 in [END,ANNEX]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [ANNEX]:
            pass
            self.annex_subclause()
        elif la1 and la1 in [END]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(END)
        eid = self.LT(1)
        self.match(IDENT)
        sl = self.LT(1)
        self.match(SEMI)
    
    def thread_implementation(self):    
        
        typeid = None
        defid = None
        id = None
        id2 = None
        pass
        self.match(THREAD)
        self.match(IMPL)
        typeid = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        defid = self.LT(1)
        self.match(IDENT)
        if not self.inputState.guessing:
            if not commonPy.configMT.g_bOnlySubprograms:
               if typeid.getText() not in g_apLevelContainers:
                  panic("Line %d: Thread (%s) must first be declared before it is implemented" % (typeid.getLine(), typeid.getText()))
               sp = g_apLevelContainers[typeid.getText()]
               g_threadImplementations.append([typeid.getText(), defid.getText(), sp._language, ""])
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [EXTENDS]:
            pass
            self.match(EXTENDS)
            self.unique_impl_name()
        elif la1 and la1 in [END,REFINES,SUBCOMPONENTS,ANNEX,CONNECTIONS,PROPERTIES,CALLS,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINES]:
            pass
            self.refinestypeSubclause()
        elif la1 and la1 in [END,SUBCOMPONENTS,ANNEX,CONNECTIONS,PROPERTIES,CALLS,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [SUBCOMPONENTS]:
            pass
            self.threadSubcomponents()
        elif la1 and la1 in [END,ANNEX,CONNECTIONS,PROPERTIES,CALLS,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [CALLS]:
            pass
            self.callsSubclause()
        elif la1 and la1 in [END,ANNEX,CONNECTIONS,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [CONNECTIONS]:
            pass
            mesh=self.connectionsSubclause()
            if not self.inputState.guessing:
                if not commonPy.configMT.g_bOnlySubprograms:
                   for conn in mesh:
                       if conn._from._portId == None or conn._to._portId == None:
                           continue # One of _from,_to are connection_refinements (unsupported)
                       sp = g_apLevelContainers[typeid.getText()]
                       sp.AddConnection(conn._from, conn._to)
        elif la1 and la1 in [END,ANNEX,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FLOWS]:
            pass
            self.flow_impls()
        elif la1 and la1 in [END,ANNEX,PROPERTIES,MODES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        cci=self.common_component_impl()
        if not self.inputState.guessing:
            if not commonPy.configMT.g_bOnlySubprograms:
               if cci != None:
                   if typeid.getText() not in g_apLevelContainers:
                       panic("Line %d: THREAD (%s) must first be declared before it is implemented" % (typeid.getLine(), typeid.getText()))
                   sp = g_apLevelContainers[typeid.getText()]
                   for assoc in cci:
                       if assoc == None: continue
                       if assoc._name[-15:].lower() == "source_language":
                           stripQuotes = assoc._value.replace("\"", "")
                           #sp.SetLanguage(stripQuotes) 
                           g_threadImplementations[-1][2] = stripQuotes
                       if assoc._name[-15:].lower() == "fv_name":
                           stripQuotes = assoc._value.replace("\"", "")
                           #sp.SetLanguage(stripQuotes) 
                           g_threadImplementations[-1][3] = stripQuotes
        self.match(END)
        id = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        id2 = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def thread_group_type(self):    
        
        id = None
        eid = None
        pass
        self.match(THREAD)
        self.match(GROUP)
        id = self.LT(1)
        self.match(IDENT)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [EXTENDS]:
            pass
            self.match(EXTENDS)
            self.unique_type_name()
        elif la1 and la1 in [END,FEATURES,ANNEX,PROPERTIES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FEATURES]:
            pass
            self.featuresThreadGroup()
        elif la1 and la1 in [END,ANNEX,PROPERTIES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FLOWS]:
            pass
            self.flow_specs()
        elif la1 and la1 in [END,ANNEX,PROPERTIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PROPERTIES]:
            pass
            pa=self.propertyAssociations_no_modes()
        elif la1 and la1 in [END,ANNEX]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [ANNEX]:
            pass
            self.annex_subclause()
        elif la1 and la1 in [END]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(END)
        eid = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def thread_group_implementation(self):    
        
        typeid = None
        defid = None
        id = None
        id2 = None
        pass
        self.match(THREAD)
        self.match(GROUP)
        self.match(IMPL)
        typeid = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        defid = self.LT(1)
        self.match(IDENT)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [EXTENDS]:
            pass
            self.match(EXTENDS)
            self.unique_impl_name()
        elif la1 and la1 in [END,REFINES,SUBCOMPONENTS,ANNEX,CONNECTIONS,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINES]:
            pass
            self.refinestypeSubclause()
        elif la1 and la1 in [END,SUBCOMPONENTS,ANNEX,CONNECTIONS,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [SUBCOMPONENTS]:
            pass
            self.threadgroupSubcomponents()
        elif la1 and la1 in [END,ANNEX,CONNECTIONS,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [CONNECTIONS]:
            pass
            cs=self.connectionsSubclause()
        elif la1 and la1 in [END,ANNEX,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FLOWS]:
            pass
            self.flow_impls()
        elif la1 and la1 in [END,ANNEX,PROPERTIES,MODES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        cci=self.common_component_impl()
        self.match(END)
        id = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        id2 = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def system_type(self):    
        
        id = None
        eid = None
        pass
        self.match(SYSTEM)
        id = self.LT(1)
        self.match(IDENT)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [EXTENDS]:
            pass
            self.match(EXTENDS)
            self.unique_type_name()
        elif la1 and la1 in [END,FEATURES,ANNEX,PROPERTIES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FEATURES]:
            pass
            fe=self.featuresSystem()
            if not self.inputState.guessing:
                g_systems[id.getText()]=[x._sp for x in fe if x._direction == "OUT"]
                #print "Detected RIs for", id.getText(), g_systems[id.getText()]
        elif la1 and la1 in [END,ANNEX,PROPERTIES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FLOWS]:
            pass
            self.flow_specs()
        elif la1 and la1 in [END,ANNEX,PROPERTIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PROPERTIES]:
            pass
            pa=self.propertyAssociations_no_modes()
        elif la1 and la1 in [END,ANNEX]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [ANNEX]:
            pass
            self.annex_subclause()
        elif la1 and la1 in [END]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(END)
        eid = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def system_implementation(self):    
        
        typeid = None
        defid = None
        id = None
        id2 = None
        pass
        self.match(SYSTEM)
        self.match(IMPL)
        typeid = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        defid = self.LT(1)
        self.match(IDENT)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [EXTENDS]:
            pass
            self.match(EXTENDS)
            self.unique_impl_name()
        elif la1 and la1 in [END,REFINES,SUBCOMPONENTS,ANNEX,CONNECTIONS,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINES]:
            pass
            self.refinestypeSubclause()
        elif la1 and la1 in [END,SUBCOMPONENTS,ANNEX,CONNECTIONS,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [SUBCOMPONENTS]:
            pass
            self.systemSubcomponents()
        elif la1 and la1 in [END,ANNEX,CONNECTIONS,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [CONNECTIONS]:
            pass
            cs=self.connectionsSubclause()
        elif la1 and la1 in [END,ANNEX,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FLOWS]:
            pass
            self.flow_impls()
        elif la1 and la1 in [END,ANNEX,PROPERTIES,MODES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        cci=self.common_component_impl()
        self.match(END)
        id = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        id2 = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def data_type(self):    
        
        id = None
        eid = None
        pass
        self.match(DATA)
        id = self.LT(1)
        self.match(IDENT)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [EXTENDS]:
            pass
            self.match(EXTENDS)
            self.unique_type_name()
        elif la1 and la1 in [END,FEATURES,ANNEX,PROPERTIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FEATURES]:
            pass
            self.featuresData()
        elif la1 and la1 in [END,ANNEX,PROPERTIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PROPERTIES]:
            pass
            panms=self.propertyAssociations_no_modes()
            if not self.inputState.guessing:
                #print "Data definition of", id.getText(), panms
                asnFilename = ""
                asnNodename = ""
                asnSize = -1
                for prop in panms:
                   if prop._name.lower() == "source_text": asnFilename = prop._propertyExpressionOrList[1:-1]
                   elif prop._name.lower() == "type_source_name": asnNodename = prop._propertyExpressionOrList[1:-1]
                   elif prop._name.lower() == "source_data_size": 
                       try:
                           asnSize = int(prop._propertyExpressionOrList)
                       except:
                          panic("Line %d: DATA (%s) must have source_data_size be declared as [0-9]B (not '%s')"  % (id.getLine(), id.getText(), prop._propertyExpressionOrList))
                if asnFilename!="" and asnNodename!="" and asnSize != -1:
                   s = Signal(asnFilename, asnNodename, asnSize)
                   g_signals[id.getText()] = s
                   g_signals[g_currentPackage + "::" + id.getText()] = s
                else:
                  panic("Line %d: DATA (%s) must have Source_Text, Type_Source_Name and Source_Data_Size"  % (id.getLine(), id.getText()))
        elif la1 and la1 in [END,ANNEX]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [ANNEX]:
            pass
            self.annex_subclause()
        elif la1 and la1 in [END]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(END)
        eid = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def data_implementation(self):    
        
        typeid = None
        defid = None
        id = None
        id2 = None
        pass
        self.match(DATA)
        self.match(IMPL)
        typeid = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        defid = self.LT(1)
        self.match(IDENT)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [EXTENDS]:
            pass
            self.match(EXTENDS)
            self.unique_impl_name()
        elif la1 and la1 in [END,REFINES,SUBCOMPONENTS,ANNEX,CONNECTIONS,PROPERTIES,MODES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINES]:
            pass
            self.refinestypeSubclause()
        elif la1 and la1 in [END,SUBCOMPONENTS,ANNEX,CONNECTIONS,PROPERTIES,MODES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [SUBCOMPONENTS]:
            pass
            self.dataSubcomponents()
        elif la1 and la1 in [END,ANNEX,CONNECTIONS,PROPERTIES,MODES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [CONNECTIONS]:
            pass
            self.dataConnectionsSubclause()
        elif la1 and la1 in [END,ANNEX,PROPERTIES,MODES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        cci=self.common_component_impl()
        self.match(END)
        id = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        id2 = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def subprogram_type(self):    
        
        id = None
        eid = None
        pass
        self.match(SUBPROGRAM)
        id = self.LT(1)
        self.match(IDENT)
        if not self.inputState.guessing:
            #print "Now defining SUBPROGRAM", id.getText()
            #print f
            sp = ApLevelContainer(id.getText())
            g_apLevelContainers[id.getText()] = sp
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [EXTENDS]:
            pass
            self.match(EXTENDS)
            self.unique_type_name()
        elif la1 and la1 in [END,FEATURES,ANNEX,PROPERTIES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FEATURES]:
            pass
            features=self.featuresSubprogram()
            if not self.inputState.guessing:
                for spFeature in features:
                  if spFeature == None: continue
                  if spFeature._parameter._type not in g_signals:
                     # panic("Line %d: Referenced datatype (%s) not defined yet" % \
                     #    (id.getLine(),spFeature._parameter._type))
                     signal = spFeature._parameter._type
                  else:
                     signal = g_signals[spFeature._parameter._type]
                  if spFeature._parameter._direction == "IN":
                     param = InParam(id.getText(), spFeature._id, signal, spFeature._parameter)
                  elif spFeature._parameter._direction == "OUT":
                     param = OutParam(id.getText(), spFeature._id, signal, spFeature._parameter)
                  elif spFeature._parameter._direction == "INOUT":
                     param = InOutParam(id.getText(), spFeature._id, signal, spFeature._parameter)
                  else:
                     panic("No IN/OUT/INOUT specified!")
                  sp.AddParam(param)
        elif la1 and la1 in [END,ANNEX,PROPERTIES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FLOWS]:
            pass
            self.flow_specs()
        elif la1 and la1 in [END,ANNEX,PROPERTIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PROPERTIES]:
            pass
            properties=self.propertyAssociations_no_modes()
            if not self.inputState.guessing:
                if properties != None:
                   if id.getText() not in g_apLevelContainers:
                      panic("Line %d: SUBPROGRAM (%s) must first be declared before it is PROPERTIES-ed"  % (id.getLine(), id.getText()))
                   sp = g_apLevelContainers[id.getText()]
                   for property in properties:
                      if property._name[-15:].lower() == "source_language":
                          stripQuotes = property._propertyExpressionOrList.replace("\"", "")
                          sp.SetLanguage(stripQuotes)
        elif la1 and la1 in [END,ANNEX]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [ANNEX]:
            pass
            self.annex_subclause()
        elif la1 and la1 in [END]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(END)
        eid = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def subprogram_implementation(self):    
        
        typeid = None
        defid = None
        id = None
        id2 = None
        pass
        self.match(SUBPROGRAM)
        self.match(IMPL)
        typeid = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        defid = self.LT(1)
        self.match(IDENT)
        if not self.inputState.guessing:
            if typeid.getText() not in g_apLevelContainers:
               panic("Line %d: Subprogram (%s) must first be declared before it is implemented" % (typeid.getLine(), typeid.getText()))
            sp = g_apLevelContainers[typeid.getText()]
            g_subProgramImplementations.append([typeid.getText(), defid.getText(), sp._language, "" ])
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [EXTENDS]:
            pass
            self.match(EXTENDS)
            self.unique_impl_name()
        elif la1 and la1 in [END,REFINES,ANNEX,CONNECTIONS,PROPERTIES,CALLS,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINES]:
            pass
            self.refinestypeSubclause()
        elif la1 and la1 in [END,ANNEX,CONNECTIONS,PROPERTIES,CALLS,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [CALLS]:
            pass
            self.callsSubclause()
        elif la1 and la1 in [END,ANNEX,CONNECTIONS,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [CONNECTIONS]:
            pass
            mesh=self.connectionsSubclause()
            if not self.inputState.guessing:
                for conn in mesh:
                   if conn._from._portId == None or conn._to._portId == None:
                       continue # One of _from,_to are connection_refinements (unsupported)
                   sp = g_apLevelContainers[typeid.getText()]
                   sp.AddConnection(conn._from, conn._to)
        elif la1 and la1 in [END,ANNEX,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FLOWS]:
            pass
            self.flow_impls()
        elif la1 and la1 in [END,ANNEX,PROPERTIES,MODES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        c=self.common_component_impl()
        if not self.inputState.guessing:
            if c != None:
               if typeid.getText() not in g_apLevelContainers:
                   panic("Line %d: SUBPROGRAM (%s) must first be declared before it is implemented" % (typeid.getLine(), typeid.getText()))
               sp = g_apLevelContainers[typeid.getText()]
               for assoc in c:
                   if assoc == None: continue
                   if assoc._name[-15:].lower() == "source_language":
                       stripQuotes = assoc._value.replace("\"", "")
                       #sp.SetLanguage(stripQuotes) 
                       g_subProgramImplementations[-1][2] = stripQuotes
                   if assoc._name[-15:].lower() == "fv_name":
                       stripQuotes = assoc._value.replace("\"", "")
                       #sp.SetLanguage(stripQuotes) 
                       g_subProgramImplementations[-1][3] = stripQuotes
        self.match(END)
        id = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        id2 = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def process_type(self):    
        
        id = None
        eid = None
        pass
        self.match(PROCESS)
        id = self.LT(1)
        self.match(IDENT)
        if not self.inputState.guessing:
            if not commonPy.configMT.g_bOnlySubprograms:
               sp = ApLevelContainer(id.getText())
               g_apLevelContainers[id.getText()] = sp
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [EXTENDS]:
            pass
            self.match(EXTENDS)
            self.unique_type_name()
        elif la1 and la1 in [END,FEATURES,ANNEX,PROPERTIES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FEATURES]:
            pass
            processFeatures=self.featuresProcess()
            if not self.inputState.guessing:
                if not commonPy.configMT.g_bOnlySubprograms:
                   for processFeature in processFeatures:
                      if processFeature == None: continue
                      if processFeature._port._type not in g_signals:
                         # panic("Line %d: Referenced datatype (%s) not defined yet" % \
                         #     (id.getLine(),processFeature._port._type))
                         signal = processFeature._port._type
                      else:
                         signal = g_signals[processFeature._port._type]
                      if processFeature._port._direction == "IN":
                         param = InParam(id.getText(), processFeature._id, signal, processFeature._port)
                      elif processFeature._port._direction == "OUT":
                         param = OutParam(id.getText(), processFeature._id, signal, processFeature._port)
                      elif processFeature._port._direction == "INOUT":
                         param = InOutParam(id.getText(), processFeature._id, signal, processFeature._port)
                      else:
                         panic("No IN/OUT/INOUT specified!")
                      sp.AddParam(param)
        elif la1 and la1 in [END,ANNEX,PROPERTIES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FLOWS]:
            pass
            self.flow_specs()
        elif la1 and la1 in [END,ANNEX,PROPERTIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PROPERTIES]:
            pass
            properties=self.propertyAssociations_no_modes()
            if not self.inputState.guessing:
                if not commonPy.configMT.g_bOnlySubprograms:
                   if properties != None:
                       if id.getText() not in g_apLevelContainers:
                          panic("Line %d: PROCESS (%s) must first be declared before it is PROPERTIES-ed"  % (id.getLine(), id.getText()))
                       sp = g_apLevelContainers[id.getText()]
                       for property in properties:
                          if property._name[-15:].lower() == "source_language":
                              stripQuotes = property._propertyExpressionOrList.replace("\"", "")
                              sp.SetLanguage(stripQuotes)
        elif la1 and la1 in [END,ANNEX]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [ANNEX]:
            pass
            self.annex_subclause()
        elif la1 and la1 in [END]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(END)
        eid = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def process_implementation(self):    
        
        typeid = None
        defid = None
        id = None
        id2 = None
        pass
        self.match(PROCESS)
        self.match(IMPL)
        typeid = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        defid = self.LT(1)
        self.match(IDENT)
        if not self.inputState.guessing:
            if not commonPy.configMT.g_bOnlySubprograms:
               if typeid.getText() not in g_apLevelContainers:
                  panic("Line %d: Process (%s) must first be declared before it is implemented"  % (typeid.getLine(), typeid.getText()))
               sp = g_apLevelContainers[typeid.getText()]
               g_processImplementations.append([typeid.getText(), defid.getText(), sp._language, ""])
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [EXTENDS]:
            pass
            self.match(EXTENDS)
            self.unique_impl_name()
        elif la1 and la1 in [END,REFINES,SUBCOMPONENTS,ANNEX,CONNECTIONS,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINES]:
            pass
            self.refinestypeSubclause()
        elif la1 and la1 in [END,SUBCOMPONENTS,ANNEX,CONNECTIONS,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [SUBCOMPONENTS]:
            pass
            self.processSubcomponents()
        elif la1 and la1 in [END,ANNEX,CONNECTIONS,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [CONNECTIONS]:
            pass
            mesh=self.connectionsSubclause()
            if not self.inputState.guessing:
                if not commonPy.configMT.g_bOnlySubprograms:
                   for conn in mesh:
                       if conn._from._portId == None or conn._to._portId == None:
                           continue # One of _from,_to are connection_refinements (unsupported)
                       sp = g_apLevelContainers[typeid.getText()]
                       sp.AddConnection(conn._from, conn._to)
        elif la1 and la1 in [END,ANNEX,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FLOWS]:
            pass
            self.flow_impls()
        elif la1 and la1 in [END,ANNEX,PROPERTIES,MODES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        cci=self.common_component_impl()
        if not self.inputState.guessing:
            if not commonPy.configMT.g_bOnlySubprograms:
               if cci != None:
                   if typeid.getText() not in g_apLevelContainers:
                       panic("Line %d: PROCESS (%s) must first be declared before it is implemented" % (typeid.getLine(), typeid.getText()))
                   sp = g_apLevelContainers[typeid.getText()]
                   for assoc in cci:
                       if assoc == None: continue
                       if assoc._name[-15:].lower() == "source_language":
                           stripQuotes = assoc._value.replace("\"", "")
                           #sp.SetLanguage(stripQuotes) 
                           g_processImplementations[-1][2] = stripQuotes
                       if assoc._name[-15:].lower() == "fv_name":
                           stripQuotes = assoc._value.replace("\"", "")
                           #sp.SetLanguage(stripQuotes) 
                           g_processImplementations[-1][3] = stripQuotes
        self.match(END)
        id = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        id2 = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def processor_type(self):    
        
        id = None
        eid = None
        pass
        self.match(PROCESSOR)
        id = self.LT(1)
        self.match(IDENT)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [EXTENDS]:
            pass
            self.match(EXTENDS)
            self.unique_type_name()
        elif la1 and la1 in [END,FEATURES,ANNEX,PROPERTIES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FEATURES]:
            pass
            self.featuresProcessor()
        elif la1 and la1 in [END,ANNEX,PROPERTIES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FLOWS]:
            pass
            self.flow_specs()
        elif la1 and la1 in [END,ANNEX,PROPERTIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PROPERTIES]:
            pass
            pa=self.propertyAssociations_no_modes()
        elif la1 and la1 in [END,ANNEX]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [ANNEX]:
            pass
            self.annex_subclause()
        elif la1 and la1 in [END]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(END)
        eid = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def processor_implementation(self):    
        
        typeid = None
        defid = None
        id = None
        id2 = None
        pass
        self.match(PROCESSOR)
        self.match(IMPL)
        typeid = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        defid = self.LT(1)
        self.match(IDENT)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [EXTENDS]:
            pass
            self.match(EXTENDS)
            self.unique_impl_name()
        elif la1 and la1 in [END,REFINES,SUBCOMPONENTS,ANNEX,CONNECTIONS,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINES]:
            pass
            self.refinestypeSubclause()
        elif la1 and la1 in [END,SUBCOMPONENTS,ANNEX,CONNECTIONS,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [SUBCOMPONENTS]:
            pass
            self.processorSubcomponents()
        elif la1 and la1 in [END,ANNEX,CONNECTIONS,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [CONNECTIONS]:
            pass
            self.busConnectionsSubclause()
        elif la1 and la1 in [END,ANNEX,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FLOWS]:
            pass
            self.flow_impls()
        elif la1 and la1 in [END,ANNEX,PROPERTIES,MODES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        cci=self.common_component_impl()
        self.match(END)
        id = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        id2 = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def memory_type(self):    
        
        id = None
        eid = None
        pass
        self.match(MEMORY)
        id = self.LT(1)
        self.match(IDENT)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [EXTENDS]:
            pass
            self.match(EXTENDS)
            self.unique_type_name()
        elif la1 and la1 in [END,FEATURES,ANNEX,PROPERTIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FEATURES]:
            pass
            self.featuresMemory()
        elif la1 and la1 in [END,ANNEX,PROPERTIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PROPERTIES]:
            pass
            pa=self.propertyAssociations_no_modes()
        elif la1 and la1 in [END,ANNEX]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [ANNEX]:
            pass
            self.annex_subclause()
        elif la1 and la1 in [END]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(END)
        eid = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def memory_implementation(self):    
        
        typeid = None
        defid = None
        id = None
        id2 = None
        pass
        self.match(MEMORY)
        self.match(IMPL)
        typeid = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        defid = self.LT(1)
        self.match(IDENT)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [EXTENDS]:
            pass
            self.match(EXTENDS)
            self.unique_impl_name()
        elif la1 and la1 in [END,REFINES,SUBCOMPONENTS,ANNEX,CONNECTIONS,PROPERTIES,MODES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINES]:
            pass
            self.refinestypeSubclause()
        elif la1 and la1 in [END,SUBCOMPONENTS,ANNEX,CONNECTIONS,PROPERTIES,MODES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [SUBCOMPONENTS]:
            pass
            self.memorySubcomponents()
        elif la1 and la1 in [END,ANNEX,CONNECTIONS,PROPERTIES,MODES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [CONNECTIONS]:
            pass
            self.busConnectionsSubclause()
        elif la1 and la1 in [END,ANNEX,PROPERTIES,MODES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        cci=self.common_component_impl()
        self.match(END)
        id = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        id2 = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def bus_type(self):    
        
        id = None
        eid = None
        pass
        self.match(BUS)
        id = self.LT(1)
        self.match(IDENT)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [EXTENDS]:
            pass
            self.match(EXTENDS)
            self.unique_type_name()
        elif la1 and la1 in [END,FEATURES,ANNEX,PROPERTIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FEATURES]:
            pass
            self.featuresBus()
        elif la1 and la1 in [END,ANNEX,PROPERTIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PROPERTIES]:
            pass
            pa=self.propertyAssociations_no_modes()
        elif la1 and la1 in [END,ANNEX]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [ANNEX]:
            pass
            self.annex_subclause()
        elif la1 and la1 in [END]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(END)
        eid = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def bus_implementation(self):    
        
        typeid = None
        defid = None
        id = None
        id2 = None
        pass
        self.match(BUS)
        self.match(IMPL)
        typeid = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        defid = self.LT(1)
        self.match(IDENT)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [EXTENDS]:
            pass
            self.match(EXTENDS)
            self.unique_impl_name()
        elif la1 and la1 in [END,REFINES,ANNEX,PROPERTIES,MODES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINES]:
            pass
            self.refinestypeSubclause()
        elif la1 and la1 in [END,ANNEX,PROPERTIES,MODES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        cci=self.common_component_impl()
        self.match(END)
        id = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        id2 = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def device_type(self):    
        
        id = None
        eid = None
        pass
        self.match(DEVICE)
        id = self.LT(1)
        self.match(IDENT)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [EXTENDS]:
            pass
            self.match(EXTENDS)
            self.unique_type_name()
        elif la1 and la1 in [END,FEATURES,ANNEX,PROPERTIES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FEATURES]:
            pass
            self.featuresDevice()
        elif la1 and la1 in [END,ANNEX,PROPERTIES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FLOWS]:
            pass
            self.flow_specs()
        elif la1 and la1 in [END,ANNEX,PROPERTIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PROPERTIES]:
            pass
            pa=self.propertyAssociations_no_modes()
        elif la1 and la1 in [END,ANNEX]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [ANNEX]:
            pass
            self.annex_subclause()
        elif la1 and la1 in [END]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(END)
        eid = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def device_implementation(self):    
        
        typeid = None
        defid = None
        id = None
        id2 = None
        pass
        self.match(DEVICE)
        self.match(IMPL)
        typeid = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        defid = self.LT(1)
        self.match(IDENT)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [EXTENDS]:
            pass
            self.match(EXTENDS)
            self.unique_impl_name()
        elif la1 and la1 in [END,REFINES,ANNEX,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINES]:
            pass
            self.refinestypeSubclause()
        elif la1 and la1 in [END,ANNEX,PROPERTIES,MODES,FLOWS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [FLOWS]:
            pass
            self.flow_impls()
        elif la1 and la1 in [END,ANNEX,PROPERTIES,MODES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        cci=self.common_component_impl()
        self.match(END)
        id = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        id2 = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def package_file(self):    
        
        fl = None
        sl = None
        pass
        fl = self.LT(1)
        self.match(PACKAGE)
        p=self.package_name()
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PUBLIC]:
            pass
            pass
            self.public_part()
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [PRIVATE]:
                pass
                self.private_part()
            elif la1 and la1 in [END]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
        elif la1 and la1 in [PRIVATE]:
            pass
            self.private_part()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(END)
        p=self.package_name()
        sl = self.LT(1)
        self.match(SEMI)
        self.match(EOF_TYPE)
    
    def package_name(self):    
        pkgId = None
        
        id = None
        id2 = None
        pass
        if not self.inputState.guessing:
            pkgId = ""
        id = self.LT(1)
        self.match(IDENT)
        if not self.inputState.guessing:
            pkgId = id.getText()
        while True:
            if (self.LA(1)==DOUBLECOLON):
                pass
                self.match(DOUBLECOLON)
                id2 = self.LT(1)
                self.match(IDENT)
                if not self.inputState.guessing:
                    pkgId += "::" + id2.getText()
            else:
                break
            
        return pkgId
    
    def public_part(self):    
        
        pass
        self.match(PUBLIC)
        self.package_items()
    
    def private_part(self):    
        
        pass
        self.match(PRIVATE)
        self.package_items()
    
    def package_items(self):    
        
        pass
        _cnt20= 0
        while True:
            if (_tokenSet_1.member(self.LA(1))):
                pass
                self.package_item()
            else:
                break
            
            _cnt20 += 1
        if _cnt20 < 1:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PROPERTIES]:
            pass
            self.propertyAssociations()
        elif la1 and la1 in [END,PRIVATE]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def package_item(self):    
        
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [THREAD,PROCESS,SYSTEM,SUBPROGRAM,DATA,PROCESSOR,MEMORY,BUS,DEVICE]:
            pass
            self.component_classifier()
        elif la1 and la1 in [PORT]:
            pass
            self.port_group_type()
        elif la1 and la1 in [ANNEX]:
            pass
            self.annex_library()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def propertyAssociations(self):    
        
        pass
        self.match(PROPERTIES)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [NONE]:
            pass
            self.none_stmt()
        elif la1 and la1 in [IDENT]:
            pass
            _cnt455= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    p=self.property_association()
                else:
                    break
                
                _cnt455 += 1
            if _cnt455 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def none_stmt(self):    
        
        pass
        self.match(NONE)
        self.match(SEMI)
    
    def unique_type_name(self):    
        
        pid = None
        tid = None
        pass
        while True:
            if (self.LA(1)==IDENT) and (self.LA(2)==DOUBLECOLON):
                pass
                pid = self.LT(1)
                self.match(IDENT)
                self.match(DOUBLECOLON)
            else:
                break
            
        tid = self.LT(1)
        self.match(IDENT)
    
    def featuresThread(self):    
        threadParameters = None
        
        pass
        if not self.inputState.guessing:
            threadParameters = []
        self.match(FEATURES)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            _cnt171= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    t=self.threadFeature()
                    if not self.inputState.guessing:
                        threadParameters.append(t)
                else:
                    break
                
                _cnt171 += 1
            if _cnt171 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        return threadParameters
    
    def flow_specs(self):    
        
        pass
        self.match(FLOWS)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            _cnt684= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    self.flow_spec()
                else:
                    break
                
                _cnt684 += 1
            if _cnt684 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def propertyAssociations_no_modes(self):    
        tupleOfProperties = None
        
        pass
        if not self.inputState.guessing:
            tupleOfProperties = []
        self.match(PROPERTIES)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [NONE]:
            pass
            self.none_stmt()
        elif la1 and la1 in [IDENT]:
            pass
            _cnt463= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    panm=self.property_association_no_modes()
                    if not self.inputState.guessing:
                        tupleOfProperties.append(panm)
                else:
                    break
                
                _cnt463 += 1
            if _cnt463 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        return tupleOfProperties
    
    def annex_subclause(self):    
        
        id = None
        at = None
        pass
        self.match(ANNEX)
        id = self.LT(1)
        self.match(IDENT)
        at = self.LT(1)
        self.match(ANNEX_TEXT)
        self.match(SEMI)
    
    def featuresThreadGroup(self):    
        
        pass
        self.match(FEATURES)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            _cnt180= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    self.threadGroupFeature()
                else:
                    break
                
                _cnt180 += 1
            if _cnt180 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def featuresProcess(self):    
        fps = None
        
        pass
        if not self.inputState.guessing:
            fps = []
        self.match(FEATURES)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            _cnt189= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    p=self.processFeature()
                    if not self.inputState.guessing:
                        fps.append(p)
                else:
                    break
                
                _cnt189 += 1
            if _cnt189 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        return fps
    
    def featuresSystem(self):    
        result = None
        
        pass
        if not self.inputState.guessing:
            result = []
        self.match(FEATURES)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            _cnt198= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    sf=self.systemFeature()
                    if not self.inputState.guessing:
                        result.append(sf)
                else:
                    break
                
                _cnt198 += 1
            if _cnt198 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        return result
    
    def featuresSubprogram(self):    
        subProgramParameters = None
        
        pass
        if not self.inputState.guessing:
            subProgramParameters = []
        self.match(FEATURES)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            _cnt163= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    s=self.subprogramFeature()
                    if not self.inputState.guessing:
                        subProgramParameters.append(s)
                else:
                    break
                
                _cnt163 += 1
            if _cnt163 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        return subProgramParameters
    
    def featuresData(self):    
        
        pass
        self.match(FEATURES)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            _cnt155= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    self.dataFeature()
                else:
                    break
                
                _cnt155 += 1
            if _cnt155 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def featuresProcessor(self):    
        
        pass
        self.match(FEATURES)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            _cnt209= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    self.processorFeature()
                else:
                    break
                
                _cnt209 += 1
            if _cnt209 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def featuresMemory(self):    
        
        pass
        self.match(FEATURES)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            _cnt225= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    self.memoryFeature()
                else:
                    break
                
                _cnt225 += 1
            if _cnt225 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def featuresBus(self):    
        
        pass
        self.match(FEATURES)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            _cnt232= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    self.busFeature()
                else:
                    break
                
                _cnt232 += 1
            if _cnt232 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def featuresDevice(self):    
        
        pass
        self.match(FEATURES)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            _cnt217= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    self.deviceFeature()
                else:
                    break
                
                _cnt217 += 1
            if _cnt217 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def unique_impl_name(self):    
        
        pid = None
        tid = None
        iid = None
        pass
        while True:
            if (self.LA(1)==IDENT) and (self.LA(2)==DOUBLECOLON):
                pass
                pid = self.LT(1)
                self.match(IDENT)
                self.match(DOUBLECOLON)
            else:
                break
            
        tid = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        iid = self.LT(1)
        self.match(IDENT)
    
    def classifier_reference(self):    
        classifier = None
        
        ptid = None
        tid = None
        iid = None
        pass
        if not self.inputState.guessing:
            classifier = None
            ptid = None
        while True:
            if (self.LA(1)==IDENT) and (self.LA(2)==DOUBLECOLON):
                pass
                ptid = self.LT(1)
                self.match(IDENT)
                self.match(DOUBLECOLON)
            else:
                break
            
        tid = self.LT(1)
        self.match(IDENT)
        if not self.inputState.guessing:
            if ptid != None: classifier = ptid.getText() + "::" + tid.getText()
            else: classifier = g_currentPackage + "::" + tid.getText()
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [DOT]:
            pass
            self.match(DOT)
            iid = self.LT(1)
            self.match(IDENT)
        elif la1 and la1 in [SEMI,COMMA,RPAREN,APPLIES,LCURLY,IN]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        return classifier
    
    def common_component_impl(self):    
        listOfProperties = None
        
        pass
        if not self.inputState.guessing:
            listOfProperties = None
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [MODES]:
            pass
            self.mode_subclause()
        elif la1 and la1 in [END,ANNEX,PROPERTIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PROPERTIES]:
            pass
            c=self.containedPropertyAssociations()
            if not self.inputState.guessing:
                listOfProperties = c
        elif la1 and la1 in [END,ANNEX]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [ANNEX]:
            pass
            self.annex_subclause()
        elif la1 and la1 in [END]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        return listOfProperties
    
    def mode_subclause(self):    
        
        pass
        self.match(MODES)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [END,IDENT,ANNEX,PROPERTIES]:
            pass
            while True:
                if (self.LA(1)==IDENT) and (self.LA(2)==COLON):
                    pass
                    self.mode()
                else:
                    break
                
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    self.mode_transition()
                else:
                    break
                
        elif la1 and la1 in [NONE]:
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def containedPropertyAssociations(self):    
        listOfProperties = None
        
        pass
        if not self.inputState.guessing:
            listOfProperties = []
        self.match(PROPERTIES)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [NONE]:
            pass
            self.none_stmt()
        elif la1 and la1 in [IDENT]:
            pass
            _cnt459= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    c=self.contained_property_association()
                    if not self.inputState.guessing:
                        listOfProperties.append(c)
                else:
                    break
                
                _cnt459 += 1
            if _cnt459 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        return listOfProperties
    
    def refinestypeSubclause(self):    
        
        id = None
        pass
        self.match(REFINES)
        self.match(TYPE)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            _cnt240= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    id = self.LT(1)
                    self.match(IDENT)
                    self.match(COLON)
                    self.match(REFINED)
                    self.match(TO)
                    la1 = self.LA(1)
                    if False:
                        pass
                    elif la1 and la1 in [PORT]:
                        pass
                        self.port_group_spec()
                    elif la1 and la1 in [PROVIDES,REQUIRES]:
                        pass
                        self.subcomponent_access()
                    elif la1 and la1 in [SERVER]:
                        pass
                        self.server_subprogram()
                    elif la1 and la1 in [SUBPROGRAM]:
                        pass
                        self.data_subprogram()
                    else:
                        if (self.LA(1)==IN or self.LA(1)==OUT) and (self.LA(2)==DATA or self.LA(2)==EVENT or self.LA(2)==OUT) and (self.LA(3)==DATA or self.LA(3)==PORT or self.LA(3)==EVENT):
                            pass
                            p=self.port_spec()
                        elif (self.LA(1)==IN or self.LA(1)==OUT) and (self.LA(2)==PARAMETER or self.LA(2)==OUT) and (_tokenSet_2.member(self.LA(3))):
                            pass
                            pa=self.parameter()
                        else:
                            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                        
                else:
                    break
                
                _cnt240 += 1
            if _cnt240 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def threadSubcomponents(self):    
        
        pass
        self.match(SUBCOMPONENTS)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            _cnt245= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    self.threadSubcomponent()
                else:
                    break
                
                _cnt245 += 1
            if _cnt245 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def callsSubclause(self):    
        
        pass
        self.match(CALLS)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT,LCURLY]:
            pass
            _cnt546= 0
            while True:
                if (self.LA(1)==IDENT or self.LA(1)==LCURLY):
                    pass
                    self.subprogram_call_sequence()
                else:
                    break
                
                _cnt546 += 1
            if _cnt546 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def connectionsSubclause(self):    
        retValue = None
        
        pass
        if not self.inputState.guessing:
            retValue = []
        self.match(CONNECTIONS)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT,DATA,BUS,PORT,EVENT,PARAMETER]:
            pass
            _cnt634= 0
            while True:
                if (_tokenSet_3.member(self.LA(1))) and (_tokenSet_4.member(self.LA(2))) and (_tokenSet_5.member(self.LA(3))):
                    pass
                    c=self.connection()
                    if not self.inputState.guessing:
                        if c!=None: retValue.append(c)
                elif (self.LA(1)==IDENT) and (self.LA(2)==COLON) and (self.LA(3)==REFINED):
                    pass
                    cf=self.connection_refinement()
                else:
                    break
                
                _cnt634 += 1
            if _cnt634 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        return retValue
    
    def flow_impls(self):    
        
        pass
        self.match(FLOWS)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            _cnt701= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    self.flow_sequence()
                else:
                    break
                
                _cnt701 += 1
            if _cnt701 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def threadgroupSubcomponents(self):    
        
        pass
        self.match(SUBCOMPONENTS)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            _cnt260= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    self.threadgroupSubcomponent()
                else:
                    break
                
                _cnt260 += 1
            if _cnt260 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def processSubcomponents(self):    
        
        pass
        self.match(SUBCOMPONENTS)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            _cnt265= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    self.processSubcomponent()
                else:
                    break
                
                _cnt265 += 1
            if _cnt265 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def systemSubcomponents(self):    
        
        pass
        self.match(SUBCOMPONENTS)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            _cnt270= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    self.systemSubcomponent()
                else:
                    break
                
                _cnt270 += 1
            if _cnt270 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def dataSubcomponents(self):    
        
        pass
        self.match(SUBCOMPONENTS)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            _cnt275= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    self.dataSubcomponent()
                else:
                    break
                
                _cnt275 += 1
            if _cnt275 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def dataConnectionsSubclause(self):    
        
        pass
        self.match(CONNECTIONS)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT,DATA]:
            pass
            _cnt658= 0
            while True:
                if (self.LA(1)==IDENT or self.LA(1)==DATA) and (self.LA(2)==COLON or self.LA(2)==ACCESS) and (self.LA(3)==IDENT or self.LA(3)==DATA):
                    pass
                    self.data_access_connection_decl()
                elif (self.LA(1)==IDENT) and (self.LA(2)==COLON) and (self.LA(3)==REFINED):
                    pass
                    self.data_access_connection_refinement_decl()
                else:
                    break
                
                _cnt658 += 1
            if _cnt658 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def processorSubcomponents(self):    
        
        pass
        self.match(SUBCOMPONENTS)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            _cnt250= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    self.processorSubcomponent()
                else:
                    break
                
                _cnt250 += 1
            if _cnt250 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def busConnectionsSubclause(self):    
        
        pass
        self.match(CONNECTIONS)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT,BUS]:
            pass
            _cnt671= 0
            while True:
                if (self.LA(1)==IDENT or self.LA(1)==BUS) and (self.LA(2)==COLON or self.LA(2)==ACCESS) and (self.LA(3)==IDENT or self.LA(3)==BUS):
                    pass
                    self.bus_access_connection_decl()
                elif (self.LA(1)==IDENT) and (self.LA(2)==COLON) and (self.LA(3)==REFINED):
                    pass
                    self.bus_access_connection_refinement_decl()
                else:
                    break
                
                _cnt671 += 1
            if _cnt671 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def memorySubcomponents(self):    
        
        pass
        self.match(SUBCOMPONENTS)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            _cnt255= 0
            while True:
                if (self.LA(1)==IDENT):
                    pass
                    self.memorySubcomponent()
                else:
                    break
                
                _cnt255 += 1
            if _cnt255 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif la1 and la1 in [NONE]:
            pass
            pass
            self.none_stmt()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def dataFeature(self):    
        
        id = None
        pass
        id = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINED]:
            pass
            self.match(REFINED)
            self.match(TO)
        elif la1 and la1 in [SUBPROGRAM,PROVIDES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [SUBPROGRAM]:
            pass
            self.data_subprogram()
        elif la1 and la1 in [PROVIDES]:
            pass
            pass
            self.match(PROVIDES)
            self.dataAccess()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def data_subprogram(self):    
        
        pass
        self.match(SUBPROGRAM)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            cr=self.classifier_reference()
        elif la1 and la1 in [SEMI,LCURLY]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            cpa=self.curlyPropertyAssociations_no_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
    
    def dataAccess(self):    
        
        pass
        self.match(DATA)
        self.match(ACCESS)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            c=self.classifier_reference()
        elif la1 and la1 in [SEMI,LCURLY]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            cpa=self.curlyPropertyAssociations_no_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
    
    def subprogramFeature(self):    
        subProgramFeature = None
        
        id = None
        pass
        if not self.inputState.guessing:
            subProgramFeature = None
        id = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINED]:
            pass
            self.match(REFINED)
            self.match(TO)
        elif la1 and la1 in [REQUIRES,PORT,IN,OUT]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PORT]:
            pass
            self.port_group_spec()
        elif la1 and la1 in [REQUIRES]:
            pass
            pass
            self.match(REQUIRES)
            self.dataAccess()
        else:
            if (self.LA(1)==OUT) and (self.LA(2)==EVENT):
                pass
                self.subprogramPort()
            elif (self.LA(1)==IN or self.LA(1)==OUT) and (self.LA(2)==PARAMETER or self.LA(2)==OUT):
                pass
                p=self.parameter()
                if not self.inputState.guessing:
                    subProgramFeature = AadlSubProgramFeature(id.getText(), p)
            else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        return subProgramFeature
    
    def subprogramPort(self):    
        
        pass
        if (self.LA(1)==OUT) and (self.LA(2)==EVENT) and (self.LA(3)==PORT):
            pass
            self.match(OUT)
            self.match(EVENT)
            self.match(PORT)
        elif (self.LA(1)==OUT) and (self.LA(2)==EVENT) and (self.LA(3)==DATA):
            pass
            self.match(OUT)
            self.match(EVENT)
            self.match(DATA)
            self.match(PORT)
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [IDENT]:
                pass
                cr=self.classifier_reference()
            elif la1 and la1 in [SEMI,LCURLY]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            cpa=self.curlyPropertyAssociations_no_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
    
    def port_group_spec(self):    
        
        pass
        self.match(PORT)
        self.match(GROUP)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            self.unique_type_name()
        elif la1 and la1 in [SEMI,LCURLY]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            cpa=self.curlyPropertyAssociations_no_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
    
    def parameter(self):    
        param = None
        
        pass
        if not self.inputState.guessing:
            direction = None
            param = None
        if (self.LA(1)==IN) and (self.LA(2)==OUT):
            pass
            self.match(IN)
            self.match(OUT)
            if not self.inputState.guessing:
                direction = "INOUT"
        elif (self.LA(1)==IN) and (self.LA(2)==PARAMETER):
            pass
            self.match(IN)
            if not self.inputState.guessing:
                direction = "IN"
        elif (self.LA(1)==OUT):
            pass
            self.match(OUT)
            if not self.inputState.guessing:
                direction = "OUT"
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
        self.match(PARAMETER)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            c=self.classifier_reference()
            if not self.inputState.guessing:
                param = AadlParameter(direction, c) 
                param._encoding = "UPER"
        elif la1 and la1 in [SEMI,LCURLY]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            cpa=self.curlyPropertyAssociations_no_modes()
            if not self.inputState.guessing:
                if param != None:
                   encodings = [x._propertyExpressionOrList for x in cpa if x._name.lower()[-8:] == "encoding"]
                   if 1 == len(encodings):
                       param._encoding = encodings[0].capitalize()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
        return param
    
    def threadFeature(self):    
        tf = None
        
        id = None
        pass
        if not self.inputState.guessing:
            tf = None
        id = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINED]:
            pass
            self.match(REFINED)
            self.match(TO)
        elif la1 and la1 in [PROVIDES,REQUIRES,SERVER,PORT,IN,OUT]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IN,OUT]:
            pass
            p=self.port_spec()
            if not self.inputState.guessing:
                if p != None:
                   tf=AadlThreadFeature(id.getText(), p)
        elif la1 and la1 in [PORT]:
            pass
            self.port_group_spec()
        elif la1 and la1 in [SERVER]:
            pass
            self.server_subprogram()
        elif la1 and la1 in [PROVIDES]:
            pass
            pass
            self.match(PROVIDES)
            self.dataAccess()
        elif la1 and la1 in [REQUIRES]:
            pass
            pass
            self.match(REQUIRES)
            self.dataAccess()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        return tf
    
    def port_spec(self):    
        portSpecification = None
        
        pass
        if not self.inputState.guessing:
            portSpecification = None
            direction = None
        if (self.LA(1)==IN) and (self.LA(2)==OUT):
            pass
            self.match(IN)
            self.match(OUT)
            if not self.inputState.guessing:
                direction = "INOUT"
        elif (self.LA(1)==IN) and (self.LA(2)==DATA or self.LA(2)==EVENT):
            pass
            self.match(IN)
            if not self.inputState.guessing:
                direction = "IN"
        elif (self.LA(1)==OUT):
            pass
            self.match(OUT)
            if not self.inputState.guessing:
                direction = "OUT"
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
        p=self.port_type()
        if not self.inputState.guessing:
            if p != None:
               portSpecification = p
               p._direction = direction
               portSpecification._encoding = "UPER"
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            cpa=self.curlyPropertyAssociations_no_modes()
            if not self.inputState.guessing:
                if portSpecification != None:
                   encodings = [x._propertyExpressionOrList for x in cpa if x._name.lower()[-8:] == "encoding"]
                   if 1 == len(encodings):
                       portSpecification._encoding = encodings[0].capitalize()
                   calledSubprograms = [x._propertyExpressionOrList for x in cpa if x._name.lower()=="rcmoperation"]
                   if 1 == len(calledSubprograms):
                       assert( isinstance(portSpecification, AadlEventPort) )
                       portSpecification._sp = calledSubprograms[0][2:]
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
        return portSpecification
    
    def server_subprogram(self):    
        
        pass
        self.match(SERVER)
        self.match(SUBPROGRAM)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            self.unique_subprogram_reference()
        elif la1 and la1 in [SEMI,LCURLY]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            cpa=self.curlyPropertyAssociations_no_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
    
    def threadGroupFeature(self):    
        
        id = None
        pass
        id = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINED]:
            pass
            self.match(REFINED)
            self.match(TO)
        elif la1 and la1 in [PROVIDES,REQUIRES,SERVER,PORT,IN,OUT]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IN,OUT]:
            pass
            p=self.port_spec()
        elif la1 and la1 in [PORT]:
            pass
            self.port_group_spec()
        elif la1 and la1 in [SERVER]:
            pass
            self.server_subprogram()
        elif la1 and la1 in [PROVIDES]:
            pass
            pass
            self.match(PROVIDES)
            self.dataAccess()
        elif la1 and la1 in [REQUIRES]:
            pass
            pass
            self.match(REQUIRES)
            self.dataAccess()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def processFeature(self):    
        pf = None
        
        id = None
        pass
        if not self.inputState.guessing:
            pf = None
        id = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINED]:
            pass
            self.match(REFINED)
            self.match(TO)
        elif la1 and la1 in [PROVIDES,REQUIRES,SERVER,PORT,IN,OUT]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IN,OUT]:
            pass
            ps=self.port_spec()
            if not self.inputState.guessing:
                if ps != None:
                   pf = AadlProcessFeature(id.getText(), ps)
        elif la1 and la1 in [PORT]:
            pass
            self.port_group_spec()
        elif la1 and la1 in [SERVER]:
            pass
            self.server_subprogram()
        elif la1 and la1 in [PROVIDES]:
            pass
            pass
            self.match(PROVIDES)
            self.dataAccess()
        elif la1 and la1 in [REQUIRES]:
            pass
            pass
            self.match(REQUIRES)
            self.dataAccess()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        return pf
    
    def systemFeature(self):    
        result = None
        
        id = None
        pass
        if not self.inputState.guessing:
            result = None
        id = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINED]:
            pass
            self.match(REFINED)
            self.match(TO)
        elif la1 and la1 in [PROVIDES,REQUIRES,SERVER,PORT,IN,OUT]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IN,OUT]:
            pass
            p=self.port_spec()
            if not self.inputState.guessing:
                result=p
        elif la1 and la1 in [PORT]:
            pass
            self.port_group_spec()
        elif la1 and la1 in [SERVER]:
            pass
            self.server_subprogram()
        else:
            if (self.LA(1)==PROVIDES) and (self.LA(2)==DATA):
                pass
                pass
                self.match(PROVIDES)
                self.dataAccess()
            elif (self.LA(1)==PROVIDES) and (self.LA(2)==BUS):
                pass
                pass
                self.match(PROVIDES)
                self.busAccess()
            elif (self.LA(1)==REQUIRES) and (self.LA(2)==DATA):
                pass
                pass
                self.match(REQUIRES)
                self.dataAccess()
            elif (self.LA(1)==REQUIRES) and (self.LA(2)==BUS):
                pass
                pass
                self.match(REQUIRES)
                self.busAccess()
            else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        return result
    
    def busAccess(self):    
        
        pass
        self.match(BUS)
        self.match(ACCESS)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            cr=self.classifier_reference()
        elif la1 and la1 in [SEMI,LCURLY]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            cpa=self.curlyPropertyAssociations_no_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
    
    def processorFeature(self):    
        
        id = None
        pass
        id = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINED]:
            pass
            self.match(REFINED)
            self.match(TO)
        elif la1 and la1 in [REQUIRES,SERVER,PORT,IN,OUT]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IN,OUT]:
            pass
            ps=self.port_spec()
        elif la1 and la1 in [PORT]:
            pass
            self.port_group_spec()
        elif la1 and la1 in [SERVER]:
            pass
            self.server_subprogram()
        elif la1 and la1 in [REQUIRES]:
            pass
            pass
            self.match(REQUIRES)
            self.busAccess()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def deviceFeature(self):    
        
        id = None
        pass
        id = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINED]:
            pass
            self.match(REFINED)
            self.match(TO)
        elif la1 and la1 in [REQUIRES,SERVER,PORT,IN,OUT]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IN,OUT]:
            pass
            ps=self.port_spec()
        elif la1 and la1 in [PORT]:
            pass
            self.port_group_spec()
        elif la1 and la1 in [SERVER]:
            pass
            self.server_subprogram()
        elif la1 and la1 in [REQUIRES]:
            pass
            pass
            self.match(REQUIRES)
            self.busAccess()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def memoryFeature(self):    
        
        id = None
        pass
        id = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINED]:
            pass
            self.match(REFINED)
            self.match(TO)
        elif la1 and la1 in [REQUIRES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        pass
        self.match(REQUIRES)
        self.busAccess()
    
    def busFeature(self):    
        
        id = None
        pass
        id = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINED]:
            pass
            self.match(REFINED)
            self.match(TO)
        elif la1 and la1 in [REQUIRES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        pass
        self.match(REQUIRES)
        self.busAccess()
    
    def subcomponent_access(self):    
        
        if (self.LA(1)==REQUIRES) and (self.LA(2)==DATA):
            pass
            self.match(REQUIRES)
            self.dataAccess()
        elif (self.LA(1)==REQUIRES) and (self.LA(2)==BUS):
            pass
            self.match(REQUIRES)
            self.busAccess()
        elif (self.LA(1)==PROVIDES) and (self.LA(2)==DATA):
            pass
            self.match(PROVIDES)
            self.dataAccess()
        elif (self.LA(1)==PROVIDES) and (self.LA(2)==BUS):
            pass
            self.match(PROVIDES)
            self.busAccess()
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
    
    def threadSubcomponent(self):    
        
        id = None
        pass
        id = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINED]:
            pass
            self.match(REFINED)
            self.match(TO)
        elif la1 and la1 in [DATA]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(DATA)
        self.subcomponent_decl()
    
    def processorSubcomponent(self):    
        
        id = None
        pass
        id = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINED]:
            pass
            self.match(REFINED)
            self.match(TO)
        elif la1 and la1 in [MEMORY]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(MEMORY)
        self.subcomponent_decl()
    
    def memorySubcomponent(self):    
        
        id = None
        pass
        id = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINED]:
            pass
            self.match(REFINED)
            self.match(TO)
        elif la1 and la1 in [MEMORY]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(MEMORY)
        self.subcomponent_decl()
    
    def threadgroupSubcomponent(self):    
        
        id = None
        pass
        id = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINED]:
            pass
            self.match(REFINED)
            self.match(TO)
        elif la1 and la1 in [THREAD,DATA]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        if (self.LA(1)==DATA):
            pass
            self.match(DATA)
        elif (self.LA(1)==THREAD) and (self.LA(2)==GROUP):
            pass
            self.match(THREAD)
            self.match(GROUP)
        elif (self.LA(1)==THREAD) and (_tokenSet_6.member(self.LA(2))):
            pass
            self.match(THREAD)
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
        self.subcomponent_decl()
    
    def processSubcomponent(self):    
        
        id = None
        pass
        id = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINED]:
            pass
            self.match(REFINED)
            self.match(TO)
        elif la1 and la1 in [THREAD,DATA]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        if (self.LA(1)==DATA):
            pass
            self.match(DATA)
        elif (self.LA(1)==THREAD) and (self.LA(2)==GROUP):
            pass
            self.match(THREAD)
            self.match(GROUP)
        elif (self.LA(1)==THREAD) and (_tokenSet_6.member(self.LA(2))):
            pass
            self.match(THREAD)
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
        self.subcomponent_decl()
    
    def systemSubcomponent(self):    
        
        id = None
        pass
        id = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINED]:
            pass
            self.match(REFINED)
            self.match(TO)
        elif la1 and la1 in [PROCESS,SYSTEM,DATA,PROCESSOR,MEMORY,BUS,DEVICE]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [DATA]:
            pass
            self.match(DATA)
        elif la1 and la1 in [MEMORY]:
            pass
            self.match(MEMORY)
        elif la1 and la1 in [PROCESSOR]:
            pass
            self.match(PROCESSOR)
        elif la1 and la1 in [BUS]:
            pass
            self.match(BUS)
        elif la1 and la1 in [DEVICE]:
            pass
            self.match(DEVICE)
        elif la1 and la1 in [PROCESS]:
            pass
            self.match(PROCESS)
        elif la1 and la1 in [SYSTEM]:
            pass
            self.match(SYSTEM)
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.subcomponent_decl()
    
    def dataSubcomponent(self):    
        
        id = None
        pass
        id = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINED]:
            pass
            self.match(REFINED)
            self.match(TO)
        elif la1 and la1 in [DATA]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(DATA)
        self.subcomponent_decl()
    
    def subcomponent_decl(self):    
        
        pass
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            cr=self.classifier_reference()
        elif la1 and la1 in [SEMI,LCURLY,IN]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            self.containedCurlyPropertyAssociations()
        elif la1 and la1 in [SEMI,IN]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IN]:
            pass
            self.in_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
    
    def containedCurlyPropertyAssociations(self):    
        
        pass
        self.match(LCURLY)
        _cnt472= 0
        while True:
            if (self.LA(1)==IDENT):
                pass
                cpa=self.contained_property_association()
            else:
                break
            
            _cnt472 += 1
        if _cnt472 < 1:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        self.match(RCURLY)
    
    def in_modes(self):    
        
        m1 = None
        m2 = None
        pass
        self.match(IN)
        self.match(MODES)
        self.match(LPAREN)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            pass
            m1 = self.LT(1)
            self.match(IDENT)
            while True:
                if (self.LA(1)==COMMA):
                    pass
                    self.match(COMMA)
                    m2 = self.LT(1)
                    self.match(IDENT)
                else:
                    break
                
        elif la1 and la1 in [NONE]:
            pass
            self.match(NONE)
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(RPAREN)
    
    def propertyset_file(self):    
        
        ps_id = None
        id = None
        ps_id2 = None
        pass
        self.match(PROPERTY)
        self.match(SET)
        ps_id = self.LT(1)
        self.match(IDENT)
        self.match(IS)
        _cnt303= 0
        while True:
            if (self.LA(1)==IDENT):
                pass
                id = self.LT(1)
                self.match(IDENT)
                self.match(COLON)
                la1 = self.LA(1)
                if False:
                    pass
                elif la1 and la1 in [CONSTANT]:
                    pass
                    self.property_constant()
                elif la1 and la1 in [TYPE]:
                    pass
                    self.property_type_declaration()
                elif la1 and la1 in [IDENT,BOOLEAN,STRING,ENUMERATION,UNITS,REAL,INTEGER,RANGE,CLASSIFIER,REFERENCE,ACCESS,INHERIT,LIST]:
                    pass
                    self.property_name_declaration()
                else:
                        raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                    
            else:
                break
            
            _cnt303 += 1
        if _cnt303 < 1:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        self.match(END)
        ps_id2 = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
        self.match(EOF_TYPE)
    
    def property_constant(self):    
        
        pass
        self.match(CONSTANT)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT,BOOLEAN,STRING,REAL,INTEGER]:
            pass
            self.single_valued_property_constant()
        elif la1 and la1 in [LIST]:
            pass
            self.multi_valued_property_constant()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
    
    def property_type_declaration(self):    
        
        pass
        self.match(TYPE)
        self.property_type()
        self.match(SEMI)
    
    def property_name_declaration(self):    
        
        pass
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [ACCESS]:
            pass
            self.match(ACCESS)
        elif la1 and la1 in [IDENT,BOOLEAN,STRING,ENUMERATION,UNITS,REAL,INTEGER,RANGE,CLASSIFIER,REFERENCE,INHERIT,LIST]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [INHERIT]:
            pass
            self.match(INHERIT)
        elif la1 and la1 in [IDENT,BOOLEAN,STRING,ENUMERATION,UNITS,REAL,INTEGER,RANGE,CLASSIFIER,REFERENCE,LIST]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT,BOOLEAN,STRING,ENUMERATION,UNITS,REAL,INTEGER,RANGE,CLASSIFIER,REFERENCE]:
            pass
            self.single_valued_property()
        elif la1 and la1 in [LIST]:
            pass
            self.multi_valued_property()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(APPLIES)
        self.match(TO)
        self.match(LPAREN)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [THREAD,PROCESS,SYSTEM,SUBPROGRAM,DATA,PROCESSOR,MEMORY,BUS,DEVICE,CONNECTIONS,SERVER,ACCESS,MODE,PORT,EVENT,FLOW,PARAMETER]:
            pass
            pass
            self.property_owner()
            while True:
                if (self.LA(1)==COMMA):
                    pass
                    self.match(COMMA)
                    self.property_owner()
                else:
                    break
                
        elif la1 and la1 in [ALL]:
            pass
            pass
            self.match(ALL)
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(RPAREN)
        self.match(SEMI)
    
    def property_type(self):    
        
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [BOOLEAN]:
            pass
            self.boolean_type()
        elif la1 and la1 in [STRING]:
            pass
            self.string_type()
        elif la1 and la1 in [ENUMERATION]:
            pass
            self.enumeration_type()
        elif la1 and la1 in [UNITS]:
            pass
            self.units_type()
        elif la1 and la1 in [REAL]:
            pass
            self.real_type()
        elif la1 and la1 in [INTEGER]:
            pass
            self.integer_type()
        elif la1 and la1 in [RANGE]:
            pass
            self.range_type()
        elif la1 and la1 in [CLASSIFIER]:
            pass
            self.classifier_type()
        elif la1 and la1 in [REFERENCE]:
            pass
            self.component_property_type()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def boolean_type(self):    
        
        pass
        self.match(BOOLEAN)
    
    def string_type(self):    
        
        pass
        self.match(STRING)
    
    def enumeration_type(self):    
        
        pass
        self.unnamed_enumeration_type()
    
    def units_type(self):    
        
        pass
        self.match(UNITS)
        self.units_list()
    
    def real_type(self):    
        
        pass
        self.unnamed_real_type()
    
    def integer_type(self):    
        
        pass
        self.unnamed_integer_type()
    
    def range_type(self):    
        
        pass
        self.unnamed_range_type()
    
    def classifier_type(self):    
        
        pass
        self.unnamed_classifier_type()
    
    def component_property_type(self):    
        
        pass
        self.unnamed_component_property_type()
    
    def unnamed_property_type(self):    
        
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [BOOLEAN]:
            pass
            self.unnamed_boolean_type()
        elif la1 and la1 in [STRING]:
            pass
            self.unnamed_string_type()
        elif la1 and la1 in [ENUMERATION]:
            pass
            self.unnamed_enumeration_type()
        elif la1 and la1 in [UNITS]:
            pass
            self.unnamed_units_type()
        elif la1 and la1 in [REAL]:
            pass
            self.unnamed_real_type()
        elif la1 and la1 in [INTEGER]:
            pass
            self.unnamed_integer_type()
        elif la1 and la1 in [RANGE]:
            pass
            self.unnamed_range_type()
        elif la1 and la1 in [CLASSIFIER]:
            pass
            self.unnamed_classifier_type()
        elif la1 and la1 in [REFERENCE]:
            pass
            self.unnamed_component_property_type()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def unnamed_boolean_type(self):    
        
        pass
        self.match(BOOLEAN)
    
    def unnamed_string_type(self):    
        
        pass
        self.match(STRING)
    
    def unnamed_enumeration_type(self):    
        
        lit = None
        morelit = None
        pass
        self.match(ENUMERATION)
        self.match(LPAREN)
        lit = self.LT(1)
        self.match(IDENT)
        while True:
            if (self.LA(1)==COMMA):
                pass
                self.match(COMMA)
                morelit = self.LT(1)
                self.match(IDENT)
            else:
                break
            
        self.match(RPAREN)
    
    def unnamed_units_type(self):    
        
        pass
        self.match(UNITS)
        self.units_list()
    
    def unnamed_real_type(self):    
        
        pass
        self.match(REAL)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PLUS,MINUS,NUMERIC_LIT,VALUE]:
            pass
            self.real_range()
        elif la1 and la1 in [SEMI,UNITS,ASSIGN,APPLIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [UNITS]:
            pass
            self.match(UNITS)
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [IDENT]:
                pass
                self.unique_property_type_identifier()
            elif la1 and la1 in [LPAREN]:
                pass
                self.units_list()
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
        elif la1 and la1 in [SEMI,ASSIGN,APPLIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def unnamed_integer_type(self):    
        
        i = None
        pass
        i = self.LT(1)
        self.match(INTEGER)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PLUS,MINUS,NUMERIC_LIT,VALUE]:
            pass
            self.integer_range()
        elif la1 and la1 in [SEMI,UNITS,ASSIGN,APPLIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [UNITS]:
            pass
            self.match(UNITS)
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [IDENT]:
                pass
                self.unique_property_type_identifier()
            elif la1 and la1 in [LPAREN]:
                pass
                self.units_list()
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
        elif la1 and la1 in [SEMI,ASSIGN,APPLIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def unnamed_range_type(self):    
        
        pass
        self.match(RANGE)
        self.match(OF)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REAL]:
            pass
            self.unnamed_real_type()
        elif la1 and la1 in [INTEGER]:
            pass
            self.unnamed_integer_type()
        elif la1 and la1 in [IDENT]:
            pass
            self.unique_property_type_identifier()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def unnamed_classifier_type(self):    
        
        id = None
        pass
        self.match(CLASSIFIER)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LPAREN]:
            pass
            self.match(LPAREN)
            self.component_category()
            while True:
                if (self.LA(1)==COMMA):
                    pass
                    id = self.LT(1)
                    self.match(COMMA)
                    self.component_category()
                else:
                    break
                
            self.match(RPAREN)
        elif la1 and la1 in [SEMI,ASSIGN,APPLIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def unnamed_component_property_type(self):    
        
        id = None
        pass
        self.match(REFERENCE)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LPAREN]:
            pass
            self.match(LPAREN)
            self.referable_element_category()
            while True:
                if (self.LA(1)==COMMA):
                    pass
                    id = self.LT(1)
                    self.match(COMMA)
                    self.referable_element_category()
                else:
                    break
                
            self.match(RPAREN)
        elif la1 and la1 in [SEMI,ASSIGN,APPLIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def units_list(self):    
        
        lit = None
        morelit = None
        unitid = None
        pass
        self.match(LPAREN)
        lit = self.LT(1)
        self.match(IDENT)
        while True:
            if (self.LA(1)==COMMA):
                pass
                self.match(COMMA)
                morelit = self.LT(1)
                self.match(IDENT)
                self.match(ASSIGN)
                unitid = self.LT(1)
                self.match(IDENT)
                self.match(STAR)
                self.number_value()
            else:
                break
            
        self.match(RPAREN)
    
    def number_value(self):    
        
        numericval = None
        pass
        pass
        numericval = self.LT(1)
        self.match(NUMERIC_LIT)
    
    def real_range(self):    
        
        pass
        self.signed_aadlreal_or_constant()
        self.match(DOTDOT)
        self.signed_aadlreal_or_constant()
    
    def unique_property_type_identifier(self):    
        
        pset = None
        ptype = None
        pass
        if (self.LA(1)==IDENT) and (self.LA(2)==DOUBLECOLON):
            pass
            pset = self.LT(1)
            self.match(IDENT)
            self.match(DOUBLECOLON)
        elif (self.LA(1)==IDENT) and (self.LA(2)==SEMI or self.LA(2)==ASSIGN or self.LA(2)==APPLIES):
            pass
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
        ptype = self.LT(1)
        self.match(IDENT)
    
    def integer_range(self):    
        
        pass
        self.signed_aadlinteger_or_constant()
        self.match(DOTDOT)
        self.signed_aadlinteger_or_constant()
    
    def signed_aadlreal_or_constant(self):    
        
        if ((self.LA(1) >= PLUS and self.LA(1) <= NUMERIC_LIT)) and (_tokenSet_7.member(self.LA(2))):
            pass
            self.signed_aadlreal()
        elif (self.LA(1)==PLUS or self.LA(1)==MINUS or self.LA(1)==VALUE) and (self.LA(2)==LPAREN or self.LA(2)==VALUE):
            pass
            pass
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [PLUS]:
                pass
                self.match(PLUS)
            elif la1 and la1 in [MINUS]:
                pass
                self.match(MINUS)
            elif la1 and la1 in [VALUE]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
            self.property_name_constant_reference()
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
    
    def signed_aadlinteger_or_constant(self):    
        
        if ((self.LA(1) >= PLUS and self.LA(1) <= NUMERIC_LIT)) and (_tokenSet_7.member(self.LA(2))):
            pass
            self.signed_aadlinteger()
        elif (self.LA(1)==PLUS or self.LA(1)==MINUS or self.LA(1)==VALUE) and (self.LA(2)==LPAREN or self.LA(2)==VALUE):
            pass
            pass
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [PLUS]:
                pass
                self.match(PLUS)
            elif la1 and la1 in [MINUS]:
                pass
                self.match(MINUS)
            elif la1 and la1 in [VALUE]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
            self.property_name_constant_reference()
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
    
    def signed_aadlreal(self):    
        
        ui = None
        pass
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PLUS]:
            pass
            self.match(PLUS)
        elif la1 and la1 in [MINUS]:
            pass
            self.match(MINUS)
        elif la1 and la1 in [NUMERIC_LIT]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        pass
        self.real_literal()
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            ui = self.LT(1)
            self.match(IDENT)
        elif la1 and la1 in [SEMI,COMMA,RPAREN,UNITS,ASSIGN,DOTDOT,APPLIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def real_literal(self):    
        
        id = None
        pass
        id = self.LT(1)
        self.match(NUMERIC_LIT)
    
    def property_name_constant_reference(self):    
        
        pass
        self.match(VALUE)
        self.match(LPAREN)
        pnr=self.property_name_reference()
        self.match(RPAREN)
    
    def signed_aadlinteger(self):    
        
        ui = None
        pass
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PLUS]:
            pass
            self.match(PLUS)
        elif la1 and la1 in [MINUS]:
            pass
            self.match(MINUS)
        elif la1 and la1 in [NUMERIC_LIT]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        pass
        self.integer_literal()
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            ui = self.LT(1)
            self.match(IDENT)
        elif la1 and la1 in [SEMI,COMMA,RPAREN,UNITS,ASSIGN,DOTDOT,APPLIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def integer_literal(self):    
        
        id = None
        pass
        id = self.LT(1)
        self.match(NUMERIC_LIT)
    
    def signed_aadlnumeric(self):    
        retValue = None
        
        numericval = None
        ui = None
        pass
        if not self.inputState.guessing:
            retValue = None
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PLUS]:
            pass
            self.match(PLUS)
        elif la1 and la1 in [MINUS]:
            pass
            self.match(MINUS)
        elif la1 and la1 in [NUMERIC_LIT]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        pass
        numericval = self.LT(1)
        self.match(NUMERIC_LIT)
        if not self.inputState.guessing:
            retValue = numericval.getText()
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            ui = self.LT(1)
            self.match(IDENT)
        elif la1 and la1 in [SEMI,COMMA,RPAREN,DOTDOT,APPLIES,DELTA,IN]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        return retValue
    
    def signed_aadlnumeric_or_constant(self):    
        
        if ((self.LA(1) >= PLUS and self.LA(1) <= NUMERIC_LIT)) and (_tokenSet_8.member(self.LA(2))):
            pass
            s=self.signed_aadlnumeric()
        elif (self.LA(1)==PLUS or self.LA(1)==MINUS or self.LA(1)==VALUE) and (self.LA(2)==LPAREN or self.LA(2)==VALUE):
            pass
            pass
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [PLUS]:
                pass
                self.match(PLUS)
            elif la1 and la1 in [MINUS]:
                pass
                self.match(MINUS)
            elif la1 and la1 in [VALUE]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
            self.property_name_constant_reference()
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
    
    def signed_aadlnumeric_or_signed_constant(self):    
        retValue = None
        
        if ((self.LA(1) >= PLUS and self.LA(1) <= NUMERIC_LIT)) and (_tokenSet_9.member(self.LA(2))):
            pass
            if not self.inputState.guessing:
                retValue = None
            s=self.signed_aadlnumeric()
            if not self.inputState.guessing:
                retValue = s
        elif (self.LA(1)==PLUS or self.LA(1)==MINUS) and (self.LA(2)==VALUE):
            pass
            pass
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [PLUS]:
                pass
                self.match(PLUS)
            elif la1 and la1 in [MINUS]:
                pass
                self.match(MINUS)
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
            self.property_name_constant_reference()
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
        return retValue
    
    def component_category(self):    
        
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [DATA]:
            pass
            self.match(DATA)
        elif la1 and la1 in [SUBPROGRAM]:
            pass
            self.match(SUBPROGRAM)
        elif la1 and la1 in [PROCESS]:
            pass
            self.match(PROCESS)
        elif la1 and la1 in [PROCESSOR]:
            pass
            self.match(PROCESSOR)
        elif la1 and la1 in [MEMORY]:
            pass
            self.match(MEMORY)
        elif la1 and la1 in [BUS]:
            pass
            self.match(BUS)
        elif la1 and la1 in [DEVICE]:
            pass
            self.match(DEVICE)
        elif la1 and la1 in [SYSTEM]:
            pass
            self.match(SYSTEM)
        else:
            if (self.LA(1)==THREAD) and (self.LA(2)==GROUP):
                pass
                pass
                self.match(THREAD)
                self.match(GROUP)
            elif (self.LA(1)==THREAD) and (_tokenSet_10.member(self.LA(2))):
                pass
                self.match(THREAD)
            else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def referable_element_category(self):    
        
        pass
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [DATA]:
            pass
            self.match(DATA)
        elif la1 and la1 in [SUBPROGRAM]:
            pass
            self.match(SUBPROGRAM)
        elif la1 and la1 in [PROCESS]:
            pass
            self.match(PROCESS)
        elif la1 and la1 in [PROCESSOR]:
            pass
            self.match(PROCESSOR)
        elif la1 and la1 in [MEMORY]:
            pass
            self.match(MEMORY)
        elif la1 and la1 in [BUS]:
            pass
            self.match(BUS)
        elif la1 and la1 in [DEVICE]:
            pass
            self.match(DEVICE)
        elif la1 and la1 in [SYSTEM]:
            pass
            self.match(SYSTEM)
        elif la1 and la1 in [CONNECTIONS]:
            pass
            self.match(CONNECTIONS)
        elif la1 and la1 in [SERVER]:
            pass
            self.match(SERVER)
            self.match(SUBPROGRAM)
        else:
            if (self.LA(1)==THREAD) and (self.LA(2)==GROUP):
                pass
                self.match(THREAD)
                self.match(GROUP)
            elif (self.LA(1)==THREAD) and (self.LA(2)==COMMA or self.LA(2)==RPAREN):
                pass
                self.match(THREAD)
            else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def single_valued_property(self):    
        
        pass
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [BOOLEAN,STRING,ENUMERATION,UNITS,REAL,INTEGER,RANGE,CLASSIFIER,REFERENCE]:
            pass
            self.unnamed_property_type()
        elif la1 and la1 in [IDENT]:
            pass
            self.unique_property_type_identifier()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [ASSIGN]:
            pass
            self.match(ASSIGN)
            pe=self.property_expression()
        elif la1 and la1 in [APPLIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def multi_valued_property(self):    
        
        pass
        self.match(LIST)
        self.match(OF)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [BOOLEAN,STRING,ENUMERATION,UNITS,REAL,INTEGER,RANGE,CLASSIFIER,REFERENCE]:
            pass
            self.unnamed_property_type()
        elif la1 and la1 in [IDENT]:
            pass
            self.unique_property_type_identifier()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [ASSIGN]:
            pass
            self.match(ASSIGN)
            self.match(LPAREN)
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [IDENT,THREAD,PROCESS,SYSTEM,SUBPROGRAM,DATA,PROCESSOR,MEMORY,BUS,DEVICE,LPAREN,PLUS,MINUS,NUMERIC_LIT,REFERENCE,VALUE,TRUE,FALSE,NOT,STRING_LITERAL]:
                pass
                pe=self.property_expression()
                while True:
                    if (self.LA(1)==COMMA):
                        pass
                        self.match(COMMA)
                        pe=self.property_expression()
                    else:
                        break
                    
            elif la1 and la1 in [RPAREN]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
            self.match(RPAREN)
        elif la1 and la1 in [APPLIES]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def property_owner(self):    
        
        id1 = None
        id2 = None
        id3 = None
        id4 = None
        id5 = None
        id6 = None
        id7 = None
        id8 = None
        id9 = None
        id10 = None
        id11 = None
        id12 = None
        id13 = None
        id14 = None
        id15 = None
        id16 = None
        id17 = None
        id18 = None
        id19 = None
        id20 = None
        id21 = None
        id22 = None
        id23 = None
        id24 = None
        id25 = None
        id26 = None
        id27 = None
        pass
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [SUBPROGRAM]:
            pass
            id4 = self.LT(1)
            self.match(SUBPROGRAM)
        elif la1 and la1 in [PROCESS]:
            pass
            id5 = self.LT(1)
            self.match(PROCESS)
        elif la1 and la1 in [PROCESSOR]:
            pass
            id6 = self.LT(1)
            self.match(PROCESSOR)
        elif la1 and la1 in [MEMORY]:
            pass
            id7 = self.LT(1)
            self.match(MEMORY)
        elif la1 and la1 in [BUS]:
            pass
            id8 = self.LT(1)
            self.match(BUS)
        elif la1 and la1 in [DEVICE]:
            pass
            id9 = self.LT(1)
            self.match(DEVICE)
        elif la1 and la1 in [SYSTEM]:
            pass
            id10 = self.LT(1)
            self.match(SYSTEM)
        elif la1 and la1 in [CONNECTIONS]:
            pass
            id11 = self.LT(1)
            self.match(CONNECTIONS)
        elif la1 and la1 in [SERVER]:
            pass
            id12 = self.LT(1)
            self.match(SERVER)
            self.match(SUBPROGRAM)
        elif la1 and la1 in [MODE]:
            pass
            id13 = self.LT(1)
            self.match(MODE)
        elif la1 and la1 in [FLOW]:
            pass
            id24 = self.LT(1)
            self.match(FLOW)
        elif la1 and la1 in [ACCESS]:
            pass
            id25 = self.LT(1)
            self.match(ACCESS)
            self.match(CONNECTIONS)
        else:
            if (self.LA(1)==THREAD) and (self.LA(2)==GROUP):
                pass
                id1 = self.LT(1)
                self.match(THREAD)
                self.match(GROUP)
            elif (self.LA(1)==THREAD) and (self.LA(2)==IDENT or self.LA(2)==COMMA or self.LA(2)==RPAREN):
                pass
                id2 = self.LT(1)
                self.match(THREAD)
            elif (self.LA(1)==DATA) and (self.LA(2)==IDENT or self.LA(2)==COMMA or self.LA(2)==RPAREN):
                pass
                id3 = self.LT(1)
                self.match(DATA)
            elif (self.LA(1)==PORT) and (self.LA(2)==GROUP) and (self.LA(3)==CONNECTIONS):
                pass
                id14 = self.LT(1)
                self.match(PORT)
                self.match(GROUP)
                self.match(CONNECTIONS)
            elif (self.LA(1)==PORT) and (self.LA(2)==GROUP) and (self.LA(3)==IDENT or self.LA(3)==COMMA or self.LA(3)==RPAREN):
                pass
                id15 = self.LT(1)
                self.match(PORT)
                self.match(GROUP)
            elif (self.LA(1)==PORT) and (self.LA(2)==CONNECTIONS):
                pass
                id16 = self.LT(1)
                self.match(PORT)
                self.match(CONNECTIONS)
            elif (self.LA(1)==PORT) and (self.LA(2)==IDENT or self.LA(2)==COMMA or self.LA(2)==RPAREN):
                pass
                id17 = self.LT(1)
                self.match(PORT)
            elif (self.LA(1)==DATA) and (self.LA(2)==PORT) and (self.LA(3)==IDENT or self.LA(3)==COMMA or self.LA(3)==RPAREN):
                pass
                id18 = self.LT(1)
                self.match(DATA)
                self.match(PORT)
            elif (self.LA(1)==EVENT) and (self.LA(2)==DATA) and (self.LA(3)==PORT) and (self.LA(4)==IDENT or self.LA(4)==COMMA or self.LA(4)==RPAREN):
                pass
                id19 = self.LT(1)
                self.match(EVENT)
                self.match(DATA)
                self.match(PORT)
            elif (self.LA(1)==EVENT) and (self.LA(2)==PORT) and (self.LA(3)==IDENT or self.LA(3)==COMMA or self.LA(3)==RPAREN):
                pass
                id20 = self.LT(1)
                self.match(EVENT)
                self.match(PORT)
            elif (self.LA(1)==DATA) and (self.LA(2)==PORT) and (self.LA(3)==CONNECTIONS):
                pass
                id21 = self.LT(1)
                self.match(DATA)
                self.match(PORT)
                self.match(CONNECTIONS)
            elif (self.LA(1)==EVENT) and (self.LA(2)==DATA) and (self.LA(3)==PORT) and (self.LA(4)==CONNECTIONS):
                pass
                id22 = self.LT(1)
                self.match(EVENT)
                self.match(DATA)
                self.match(PORT)
                self.match(CONNECTIONS)
            elif (self.LA(1)==EVENT) and (self.LA(2)==PORT) and (self.LA(3)==CONNECTIONS):
                pass
                id23 = self.LT(1)
                self.match(EVENT)
                self.match(PORT)
                self.match(CONNECTIONS)
            elif (self.LA(1)==PARAMETER) and (self.LA(2)==IDENT or self.LA(2)==COMMA or self.LA(2)==RPAREN):
                pass
                id26 = self.LT(1)
                self.match(PARAMETER)
            elif (self.LA(1)==PARAMETER) and (self.LA(2)==CONNECTIONS):
                pass
                id27 = self.LT(1)
                self.match(PARAMETER)
                self.match(CONNECTIONS)
            else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            cr=self.classifier_reference()
        elif la1 and la1 in [COMMA,RPAREN]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def property_expression(self):    
        retValue = None
        
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PLUS,MINUS,NUMERIC_LIT]:
            pass
            if not self.inputState.guessing:
                retValue = None
            n=self.numeric_or_range_term()
        elif la1 and la1 in [REFERENCE]:
            pass
            self.reference_term()
        elif la1 and la1 in [IDENT]:
            pass
            e=self.enumeration_term()
        elif la1 and la1 in [STRING_LITERAL]:
            pass
            s=self.string_term()
            if not self.inputState.guessing:
                retValue = s
        elif la1 and la1 in [THREAD,PROCESS,SYSTEM,SUBPROGRAM,DATA,PROCESSOR,MEMORY,BUS,DEVICE]:
            pass
            c=self.component_classifier_term()
            if not self.inputState.guessing:
                retValue = c
        elif la1 and la1 in [LPAREN,VALUE,TRUE,FALSE,NOT]:
            pass
            self.logical_or()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        return retValue
    
    def single_valued_property_constant(self):    
        
        pass
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [INTEGER]:
            pass
            pass
            self.match(INTEGER)
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [IDENT]:
                pass
                self.unique_property_type_identifier()
            elif la1 and la1 in [ASSIGN]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
            self.match(ASSIGN)
            self.signed_aadlinteger()
        elif la1 and la1 in [REAL]:
            pass
            pass
            self.match(REAL)
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [IDENT]:
                pass
                self.unique_property_type_identifier()
            elif la1 and la1 in [ASSIGN]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
            self.match(ASSIGN)
            self.signed_aadlreal()
        elif la1 and la1 in [STRING]:
            pass
            pass
            self.match(STRING)
            self.match(ASSIGN)
            st=self.string_term()
        elif la1 and la1 in [BOOLEAN]:
            pass
            pass
            self.match(BOOLEAN)
            self.match(ASSIGN)
            self.true_false_value()
        elif la1 and la1 in [IDENT]:
            pass
            pass
            self.unique_property_type_identifier()
            self.match(ASSIGN)
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [IDENT]:
                pass
                et=self.enumeration_term()
            elif la1 and la1 in [PLUS,MINUS,NUMERIC_LIT]:
                pass
                pass
                synPredMatched415 = False
                if ((self.LA(1) >= PLUS and self.LA(1) <= NUMERIC_LIT)) and (self.LA(2)==IDENT or self.LA(2)==DOTDOT or self.LA(2)==NUMERIC_LIT) and (_tokenSet_11.member(self.LA(3))) and (_tokenSet_12.member(self.LA(4))):
                    _m415 = self.mark()
                    synPredMatched415 = True
                    self.inputState.guessing += 1
                    try:
                        pass
                        s=self.signed_aadlnumeric()
                        self.match(DOTDOT)
                    except antlr.RecognitionException as pe:
                        synPredMatched415 = False
                    self.rewind(_m415)
                    self.inputState.guessing -= 1
                if synPredMatched415:
                    pass
                    self.aadl_numeric_range()
                elif ((self.LA(1) >= PLUS and self.LA(1) <= NUMERIC_LIT)) and (self.LA(2)==SEMI or self.LA(2)==IDENT or self.LA(2)==NUMERIC_LIT) and (self.LA(3)==END or self.LA(3)==SEMI or self.LA(3)==IDENT) and (_tokenSet_13.member(self.LA(4))):
                    pass
                    ss=self.signed_aadlnumeric()
                else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def multi_valued_property_constant(self):    
        
        pass
        self.match(LIST)
        self.match(OF)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [INTEGER]:
            pass
            pass
            self.match(INTEGER)
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [IDENT]:
                pass
                self.unique_property_type_identifier()
            elif la1 and la1 in [ASSIGN]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
            self.match(ASSIGN)
            self.match(LPAREN)
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [PLUS,MINUS,NUMERIC_LIT]:
                pass
                self.signed_aadlinteger()
                while True:
                    if (self.LA(1)==COMMA):
                        pass
                        self.match(COMMA)
                        self.signed_aadlinteger()
                    else:
                        break
                    
            elif la1 and la1 in [RPAREN]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
            self.match(RPAREN)
        elif la1 and la1 in [REAL]:
            pass
            pass
            self.match(REAL)
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [IDENT]:
                pass
                self.unique_property_type_identifier()
            elif la1 and la1 in [ASSIGN]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
            self.match(ASSIGN)
            self.match(LPAREN)
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [PLUS,MINUS,NUMERIC_LIT]:
                pass
                self.signed_aadlreal()
                while True:
                    if (self.LA(1)==COMMA):
                        pass
                        self.match(COMMA)
                        self.signed_aadlreal()
                    else:
                        break
                    
            elif la1 and la1 in [RPAREN]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
            self.match(RPAREN)
        elif la1 and la1 in [STRING]:
            pass
            pass
            self.match(STRING)
            self.match(ASSIGN)
            self.match(LPAREN)
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [STRING_LITERAL]:
                pass
                st=self.string_term()
                while True:
                    if (self.LA(1)==COMMA):
                        pass
                        self.match(COMMA)
                        ste=self.string_term()
                    else:
                        break
                    
            elif la1 and la1 in [RPAREN]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
            self.match(RPAREN)
        elif la1 and la1 in [BOOLEAN]:
            pass
            pass
            self.match(BOOLEAN)
            self.match(ASSIGN)
            self.match(LPAREN)
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [TRUE,FALSE]:
                pass
                self.true_false_value()
                while True:
                    if (self.LA(1)==COMMA):
                        pass
                        self.match(COMMA)
                        self.true_false_value()
                    else:
                        break
                    
            elif la1 and la1 in [RPAREN]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
            self.match(RPAREN)
        elif la1 and la1 in [IDENT]:
            pass
            pass
            self.unique_property_type_identifier()
            self.match(ASSIGN)
            self.match(LPAREN)
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [IDENT]:
                pass
                pass
                et=self.enumeration_term()
                while True:
                    if (self.LA(1)==COMMA):
                        pass
                        self.match(COMMA)
                        ete=self.enumeration_term()
                    else:
                        break
                    
            elif la1 and la1 in [PLUS,MINUS,NUMERIC_LIT]:
                pass
                synPredMatched443 = False
                if ((self.LA(1) >= PLUS and self.LA(1) <= NUMERIC_LIT)) and (self.LA(2)==IDENT or self.LA(2)==DOTDOT or self.LA(2)==NUMERIC_LIT) and (_tokenSet_11.member(self.LA(3))) and (_tokenSet_14.member(self.LA(4))):
                    _m443 = self.mark()
                    synPredMatched443 = True
                    self.inputState.guessing += 1
                    try:
                        pass
                        self.signed_aadlnumeric()
                        self.match(DOTDOT)
                    except antlr.RecognitionException as pe:
                        synPredMatched443 = False
                    self.rewind(_m443)
                    self.inputState.guessing -= 1
                if synPredMatched443:
                    pass
                    pass
                    self.aadl_numeric_range()
                    while True:
                        if (self.LA(1)==COMMA):
                            pass
                            self.match(COMMA)
                            self.aadl_numeric_range()
                        else:
                            break
                        
                elif ((self.LA(1) >= PLUS and self.LA(1) <= NUMERIC_LIT)) and (_tokenSet_15.member(self.LA(2))) and (_tokenSet_16.member(self.LA(3))) and (_tokenSet_17.member(self.LA(4))):
                    pass
                    pass
                    s=self.signed_aadlnumeric()
                    while True:
                        if (self.LA(1)==COMMA):
                            pass
                            self.match(COMMA)
                            ss=self.signed_aadlnumeric()
                        else:
                            break
                        
                else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
            elif la1 and la1 in [RPAREN]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
            self.match(RPAREN)
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def string_term(self):    
        retValue = None
        
        sl = None
        pass
        sl = self.LT(1)
        self.match(STRING_LITERAL)
        if not self.inputState.guessing:
            retValue = sl.getText()
        return retValue
    
    def true_false_value(self):    
        
        tv = None
        fv = None
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [TRUE]:
            pass
            tv = self.LT(1)
            self.match(TRUE)
        elif la1 and la1 in [FALSE]:
            pass
            fv = self.LT(1)
            self.match(FALSE)
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def enumeration_term(self):    
        retValue = None
        
        enum_id = None
        pass
        enum_id = self.LT(1)
        self.match(IDENT)
        if not self.inputState.guessing:
            retValue = enum_id.getText()
        return retValue
    
    def aadl_numeric_range(self):    
        
        pass
        s=self.signed_aadlnumeric()
        self.match(DOTDOT)
        ss=self.signed_aadlnumeric()
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [DELTA]:
            pass
            self.match(DELTA)
            sss=self.signed_aadlnumeric()
        elif la1 and la1 in [SEMI,COMMA,RPAREN]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def property_association(self):    
        retValue = None
        
        pass
        if not self.inputState.guessing:
            retValue = None
        pnr=self.property_name_reference()
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [ASSIGN]:
            pass
            self.match(ASSIGN)
        elif la1 and la1 in [ASSIGNPLUS]:
            pass
            self.match(ASSIGNPLUS)
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [CONSTANT]:
            pass
            self.match(CONSTANT)
        elif la1 and la1 in [IDENT,THREAD,PROCESS,SYSTEM,SUBPROGRAM,DATA,PROCESSOR,MEMORY,BUS,DEVICE,LPAREN,PLUS,MINUS,NUMERIC_LIT,REFERENCE,ACCESS,VALUE,TRUE,FALSE,NOT,STRING_LITERAL]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [ACCESS]:
            pass
            self.match(ACCESS)
        elif la1 and la1 in [IDENT,THREAD,PROCESS,SYSTEM,SUBPROGRAM,DATA,PROCESSOR,MEMORY,BUS,DEVICE,LPAREN,PLUS,MINUS,NUMERIC_LIT,REFERENCE,VALUE,TRUE,FALSE,NOT,STRING_LITERAL]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        p=self.pe_or_list()
        if not self.inputState.guessing:
            retValue = p
        if (self.LA(1)==IN) and (self.LA(2)==BINDING):
            pass
            self.in_binding()
        elif (self.LA(1)==SEMI or self.LA(1)==IN) and (_tokenSet_18.member(self.LA(2))):
            pass
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IN]:
            pass
            self.in_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
        return retValue
    
    def contained_property_association(self):    
        retValue = None
        
        pass
        if not self.inputState.guessing:
            retValue = None
        p1=self.property_name_reference()
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [ASSIGN]:
            pass
            self.match(ASSIGN)
        elif la1 and la1 in [ASSIGNPLUS]:
            pass
            self.match(ASSIGNPLUS)
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [CONSTANT]:
            pass
            self.match(CONSTANT)
        elif la1 and la1 in [IDENT,THREAD,PROCESS,SYSTEM,SUBPROGRAM,DATA,PROCESSOR,MEMORY,BUS,DEVICE,LPAREN,PLUS,MINUS,NUMERIC_LIT,REFERENCE,VALUE,TRUE,FALSE,NOT,STRING_LITERAL]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        p2=self.pe_or_list()
        if not self.inputState.guessing:
            retValue = AadlContainedPropertyAssociation(p1, p2)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [APPLIES]:
            pass
            self.applies_to()
        elif la1 and la1 in [SEMI,IN]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        if (self.LA(1)==IN) and (self.LA(2)==BINDING):
            pass
            self.in_binding()
        elif (self.LA(1)==SEMI or self.LA(1)==IN) and (_tokenSet_19.member(self.LA(2))):
            pass
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IN]:
            pass
            self.in_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
        return retValue
    
    def property_association_no_modes(self):    
        retValue = None
        
        pass
        if not self.inputState.guessing:
            retValue = None
        pnr=self.property_name_reference()
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [ASSIGN]:
            pass
            self.match(ASSIGN)
        elif la1 and la1 in [ASSIGNPLUS]:
            pass
            self.match(ASSIGNPLUS)
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [CONSTANT]:
            pass
            self.match(CONSTANT)
        elif la1 and la1 in [IDENT,THREAD,PROCESS,SYSTEM,SUBPROGRAM,DATA,PROCESSOR,MEMORY,BUS,DEVICE,LPAREN,PLUS,MINUS,NUMERIC_LIT,REFERENCE,ACCESS,VALUE,TRUE,FALSE,NOT,STRING_LITERAL]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [ACCESS]:
            pass
            self.match(ACCESS)
        elif la1 and la1 in [IDENT,THREAD,PROCESS,SYSTEM,SUBPROGRAM,DATA,PROCESSOR,MEMORY,BUS,DEVICE,LPAREN,PLUS,MINUS,NUMERIC_LIT,REFERENCE,VALUE,TRUE,FALSE,NOT,STRING_LITERAL]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        p=self.pe_or_list()
        if not self.inputState.guessing:
            retValue = AadlPropertyAssociationNoModes(pnr, p)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IN]:
            pass
            self.in_binding()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
        return retValue
    
    def curlyPropertyAssociations(self):    
        
        pass
        self.match(LCURLY)
        _cnt466= 0
        while True:
            if (self.LA(1)==IDENT):
                pass
                pa=self.property_association()
            else:
                break
            
            _cnt466 += 1
        if _cnt466 < 1:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        self.match(RCURLY)
    
    def curlyPropertyAssociations_no_modes(self):    
        tupleOfProperties = None
        
        pass
        if not self.inputState.guessing:
            tupleOfProperties = []
        self.match(LCURLY)
        _cnt469= 0
        while True:
            if (self.LA(1)==IDENT):
                pass
                panm=self.property_association_no_modes()
                if not self.inputState.guessing:
                    tupleOfProperties.append(panm)
            else:
                break
            
            _cnt469 += 1
        if _cnt469 < 1:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        self.match(RCURLY)
        return tupleOfProperties
    
    def property_name_reference(self):    
        retValue = None
        
        psid = None
        pid = None
        pass
        if not self.inputState.guessing:
            retValue = None
        if (self.LA(1)==IDENT) and (self.LA(2)==DOUBLECOLON):
            pass
            psid = self.LT(1)
            self.match(IDENT)
            self.match(DOUBLECOLON)
        elif (self.LA(1)==IDENT) and (self.LA(2)==RPAREN or self.LA(2)==ASSIGN or self.LA(2)==ASSIGNPLUS):
            pass
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
        pid = self.LT(1)
        self.match(IDENT)
        if not self.inputState.guessing:
            retValue = pid.getText()
        return retValue
    
    def pe_or_list(self):    
        retValue = None
        
        synPredMatched501 = False
        if (self.LA(1)==LPAREN) and (_tokenSet_20.member(self.LA(2))) and (_tokenSet_21.member(self.LA(3))) and (_tokenSet_22.member(self.LA(4))):
            _m501 = self.mark()
            synPredMatched501 = True
            self.inputState.guessing += 1
            try:
                pass
                self.match(LPAREN)
                pe1=self.property_expression()
                self.match(COMMA)
            except antlr.RecognitionException as pe:
                synPredMatched501 = False
            self.rewind(_m501)
            self.inputState.guessing -= 1
        if synPredMatched501:
            pass
            if not self.inputState.guessing:
                retValue = None
            pass
            self.match(LPAREN)
            pe2=self.property_expression()
            _cnt504= 0
            while True:
                if (self.LA(1)==COMMA):
                    pass
                    self.match(COMMA)
                    pe3=self.property_expression()
                else:
                    break
                
                _cnt504 += 1
            if _cnt504 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            self.match(RPAREN)
        elif (self.LA(1)==LPAREN) and (_tokenSet_23.member(self.LA(2))) and (_tokenSet_24.member(self.LA(3))) and (_tokenSet_25.member(self.LA(4))):
            pass
            pass
            self.match(LPAREN)
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [IDENT,THREAD,PROCESS,SYSTEM,SUBPROGRAM,DATA,PROCESSOR,MEMORY,BUS,DEVICE,PLUS,MINUS,NUMERIC_LIT,REFERENCE,STRING_LITERAL]:
                pass
                a=self.allbutbool()
                if not self.inputState.guessing:
                    if a != None: retValue = a
            elif la1 and la1 in [RPAREN]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
            self.match(RPAREN)
        elif (_tokenSet_26.member(self.LA(1))):
            pass
            pass
            a=self.allbutbool()
            if not self.inputState.guessing:
                if a != None: retValue = a
        elif (_tokenSet_27.member(self.LA(1))) and (_tokenSet_28.member(self.LA(2))) and (_tokenSet_29.member(self.LA(3))) and (_tokenSet_30.member(self.LA(4))):
            pass
            synPredMatched510 = False
            if (self.LA(1)==VALUE) and (self.LA(2)==LPAREN) and (self.LA(3)==IDENT) and (self.LA(4)==DOUBLECOLON or self.LA(4)==RPAREN):
                _m510 = self.mark()
                synPredMatched510 = True
                self.inputState.guessing += 1
                try:
                    pass
                    self.property_name_constant_reference()
                    self.match(DOTDOT)
                except antlr.RecognitionException as pe:
                    synPredMatched510 = False
                self.rewind(_m510)
                self.inputState.guessing -= 1
            if synPredMatched510:
                pass
                pass
                self.property_name_constant_reference()
                self.num_range()
            elif (_tokenSet_27.member(self.LA(1))) and (_tokenSet_28.member(self.LA(2))) and (_tokenSet_29.member(self.LA(3))) and (_tokenSet_30.member(self.LA(4))):
                pass
                pass
                self.logical_or()
            else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
        return retValue
    
    def in_binding(self):    
        
        pass
        self.match(IN)
        self.match(BINDING)
        self.match(LPAREN)
        cr=self.classifier_reference()
        while True:
            if (self.LA(1)==COMMA):
                pass
                self.match(COMMA)
                cr=self.classifier_reference()
            else:
                break
            
        self.match(RPAREN)
    
    def applies_to(self):    
        
        cid = None
        mid = None
        pass
        self.match(APPLIES)
        self.match(TO)
        cid = self.LT(1)
        self.match(IDENT)
        while True:
            if (self.LA(1)==DOT):
                pass
                self.match(DOT)
                mid = self.LT(1)
                self.match(IDENT)
            else:
                break
            
    
    def allbutbool(self):    
        retValue = None
        
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFERENCE]:
            pass
            if not self.inputState.guessing:
                retValue = None
            self.reference_term()
        elif la1 and la1 in [IDENT]:
            pass
            e=self.enumeration_term()
            if not self.inputState.guessing:
                retValue = e
        elif la1 and la1 in [STRING_LITERAL]:
            pass
            s=self.string_term()
            if not self.inputState.guessing:
                retValue = s
        elif la1 and la1 in [THREAD,PROCESS,SYSTEM,SUBPROGRAM,DATA,PROCESSOR,MEMORY,BUS,DEVICE]:
            pass
            c=self.component_classifier_term()
            if not self.inputState.guessing:
                retValue = c
        elif la1 and la1 in [PLUS,MINUS,NUMERIC_LIT]:
            pass
            n=self.numeric_or_range_term()
            if not self.inputState.guessing:
                retValue = n
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        return retValue
    
    def num_range(self):    
        
        pass
        self.match(DOTDOT)
        self.signed_aadlnumeric_or_constant()
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [DELTA]:
            pass
            self.match(DELTA)
            self.signed_aadlnumeric_or_constant()
        elif la1 and la1 in [SEMI,COMMA,RPAREN,APPLIES,IN]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def logical_or(self):    
        
        pass
        self.logical_and()
        while True:
            if (self.LA(1)==OR):
                pass
                self.match(OR)
                self.logical_and()
            else:
                break
            
    
    def reference_term(self):    
        
        subcomponentid = None
        subcomponentidmore = None
        pass
        self.match(REFERENCE)
        subcomponentid = self.LT(1)
        self.match(IDENT)
        while True:
            if (self.LA(1)==DOT):
                pass
                self.match(DOT)
                subcomponentidmore = self.LT(1)
                self.match(IDENT)
            else:
                break
            
    
    def component_classifier_term(self):    
        result = None
        
        pass
        if not self.inputState.guessing:
            result = None
        c=self.component_category()
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            cr=self.classifier_reference()
            if not self.inputState.guessing:
                result = cr
        elif la1 and la1 in [SEMI,COMMA,RPAREN,APPLIES,IN]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        return result
    
    def numeric_or_range_term(self):    
        retValue = None
        
        synPredMatched527 = False
        if (self.LA(1)==PLUS or self.LA(1)==MINUS) and (self.LA(2)==VALUE) and (self.LA(3)==LPAREN) and (self.LA(4)==IDENT):
            _m527 = self.mark()
            synPredMatched527 = True
            self.inputState.guessing += 1
            try:
                pass
                self.signed_constant()
                self.match(DOTDOT)
            except antlr.RecognitionException as pe:
                synPredMatched527 = False
            self.rewind(_m527)
            self.inputState.guessing -= 1
        if synPredMatched527:
            pass
            if not self.inputState.guessing:
                retValue = None
            pass
            self.signed_constant()
            self.num_range()
        elif ((self.LA(1) >= PLUS and self.LA(1) <= NUMERIC_LIT)) and (_tokenSet_31.member(self.LA(2))) and (_tokenSet_32.member(self.LA(3))) and (_tokenSet_33.member(self.LA(4))):
            pass
            pass
            s=self.signed_aadlnumeric_or_signed_constant()
            if not self.inputState.guessing:
                retValue = s
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [DOTDOT]:
                pass
                self.num_range()
            elif la1 and la1 in [SEMI,COMMA,RPAREN,APPLIES,IN]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
        return retValue
    
    def logical_and(self):    
        
        pass
        self.logical_unary()
        while True:
            if (self.LA(1)==AND):
                pass
                self.match(AND)
                self.logical_unary()
            else:
                break
            
    
    def logical_unary(self):    
        
        tv = None
        fv = None
        nott = None
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [TRUE]:
            pass
            tv = self.LT(1)
            self.match(TRUE)
        elif la1 and la1 in [FALSE]:
            pass
            fv = self.LT(1)
            self.match(FALSE)
        elif la1 and la1 in [LPAREN]:
            pass
            self.match(LPAREN)
            self.logical_or()
            self.match(RPAREN)
        elif la1 and la1 in [NOT]:
            pass
            nott = self.LT(1)
            self.match(NOT)
            self.logical_unary()
        elif la1 and la1 in [VALUE]:
            pass
            self.property_term()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def property_term(self):    
        
        pass
        self.property_name_constant_reference()
    
    def signed_constant(self):    
        
        pass
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PLUS]:
            pass
            self.match(PLUS)
        elif la1 and la1 in [MINUS]:
            pass
            self.match(MINUS)
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.property_name_constant_reference()
    
    def subprogram_call_sequence(self):    
        
        id = None
        pass
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            id = self.LT(1)
            self.match(IDENT)
            self.match(COLON)
        elif la1 and la1 in [LCURLY]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(LCURLY)
        _cnt550= 0
        while True:
            if (self.LA(1)==IDENT):
                pass
                self.subprogram_call()
            else:
                break
            
            _cnt550 += 1
        if _cnt550 < 1:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        self.match(RCURLY)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IN]:
            pass
            self.in_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
    
    def subprogram_call(self):    
        
        defcallid = None
        pass
        defcallid = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        self.match(SUBPROGRAM)
        self.called_subprogram()
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            self.curlyPropertyAssociations()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
    
    def called_subprogram(self):    
        
        pass
        cr=self.classifier_reference()
    
    def mode(self):    
        
        id = None
        pass
        id = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [INITIAL]:
            pass
            self.match(INITIAL)
        elif la1 and la1 in [REFINED,MODE]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [REFINED]:
            pass
            self.match(REFINED)
            self.match(TO)
        elif la1 and la1 in [MODE]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(MODE)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            self.curlyPropertyAssociations()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
    
    def mode_transition(self):    
        
        id = None
        moreid = None
        destination_mode = None
        pass
        id = self.LT(1)
        self.match(IDENT)
        while True:
            if (self.LA(1)==COMMA):
                pass
                self.match(COMMA)
                moreid = self.LT(1)
                self.match(IDENT)
            else:
                break
            
        self.match(LTRANS)
        up1=self.unique_port_identifier()
        while True:
            if (self.LA(1)==COMMA):
                pass
                self.match(COMMA)
                up2=self.unique_port_identifier()
            else:
                break
            
        self.match(RTRANS)
        destination_mode = self.LT(1)
        self.match(IDENT)
        self.match(SEMI)
    
    def unique_port_identifier(self):    
        retValue = None
        
        compid = None
        portid = None
        soleportid = None
        if (self.LA(1)==IDENT) and (self.LA(2)==DOT):
            pass
            compid = self.LT(1)
            self.match(IDENT)
            self.match(DOT)
            portid = self.LT(1)
            self.match(IDENT)
            if not self.inputState.guessing:
                retValue = UniquePortIdentifier(compid.getText(), portid.getText())
        elif (self.LA(1)==IDENT) and (_tokenSet_34.member(self.LA(2))):
            pass
            soleportid = self.LT(1)
            self.match(IDENT)
            if not self.inputState.guessing:
                retValue = UniquePortIdentifier(None, soleportid.getText())
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
        return retValue
    
    def in_modes_and_transitions(self):    
        
        pass
        self.match(IN)
        self.match(MODES)
        self.match(LPAREN)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT,LPAREN]:
            pass
            pass
            self.mode_or_transition()
            while True:
                if (self.LA(1)==COMMA):
                    pass
                    self.match(COMMA)
                    self.mode_or_transition()
                else:
                    break
                
        elif la1 and la1 in [NONE]:
            pass
            self.match(NONE)
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(RPAREN)
    
    def mode_or_transition(self):    
        
        mode_id = None
        old_mode_id = None
        new_mode_id = None
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            mode_id = self.LT(1)
            self.match(IDENT)
        elif la1 and la1 in [LPAREN]:
            pass
            self.match(LPAREN)
            old_mode_id = self.LT(1)
            self.match(IDENT)
            self.match(ARROW)
            new_mode_id = self.LT(1)
            self.match(IDENT)
            self.match(RPAREN)
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def port_type(self):    
        port = None
        
        if (self.LA(1)==EVENT) and (self.LA(2)==DATA):
            pass
            if not self.inputState.guessing:
                portType = None
            pass
            self.match(EVENT)
            self.match(DATA)
            self.match(PORT)
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [IDENT]:
                pass
                c=self.classifier_reference()
                if not self.inputState.guessing:
                    port = AadlEventDataPort("", c)
            elif la1 and la1 in [SEMI,LCURLY]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
        elif (self.LA(1)==DATA):
            pass
            pass
            self.match(DATA)
            self.match(PORT)
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [IDENT]:
                pass
                c=self.classifier_reference()
                if not self.inputState.guessing:
                    port = AadlPort("", c)
            elif la1 and la1 in [SEMI,LCURLY]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
        elif (self.LA(1)==EVENT) and (self.LA(2)==PORT):
            pass
            pass
            self.match(EVENT)
            self.match(PORT)
            if not self.inputState.guessing:
                port = AadlEventPort("", None)
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
        return port
    
    def unique_subprogram_reference(self):    
        
        pid = None
        tid = None
        iid = None
        pass
        while True:
            if (self.LA(1)==IDENT) and (self.LA(2)==DOUBLECOLON):
                pass
                pid = self.LT(1)
                self.match(IDENT)
                self.match(DOUBLECOLON)
            else:
                break
            
        tid = self.LT(1)
        self.match(IDENT)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [DOT]:
            pass
            self.match(DOT)
            iid = self.LT(1)
            self.match(IDENT)
        elif la1 and la1 in [SEMI,LCURLY]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def connection(self):    
        retValue = None
        
        id = None
        pass
        if not self.inputState.guessing:
            retValue = None
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            id = self.LT(1)
            self.match(IDENT)
            self.match(COLON)
        elif la1 and la1 in [DATA,BUS,PORT,EVENT,PARAMETER]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PORT]:
            pass
            p=self.port_group_connection()
            if not self.inputState.guessing:
                retValue = p
        elif la1 and la1 in [PARAMETER]:
            pass
            pc=self.parameter_connection()
            if not self.inputState.guessing:
                retValue = pc
        elif la1 and la1 in [BUS]:
            pass
            b=self.bus_access_connection()
            if not self.inputState.guessing:
                retValue = b
        else:
            if (self.LA(1)==DATA) and (self.LA(2)==PORT):
                pass
                d=self.data_connection()
                if not self.inputState.guessing:
                    retValue = d
            elif (self.LA(1)==EVENT) and (self.LA(2)==DATA):
                pass
                e=self.event_data_connection()
                if not self.inputState.guessing:
                    retValue = e
            elif (self.LA(1)==EVENT) and (self.LA(2)==PORT):
                pass
                ev=self.event_connection()
                if not self.inputState.guessing:
                    retValue = ev
            elif (self.LA(1)==DATA) and (self.LA(2)==ACCESS):
                pass
                da=self.data_access_connection()
                if not self.inputState.guessing:
                    retValue = da
            else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            self.curlyPropertyAssociations()
        elif la1 and la1 in [SEMI,IN]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IN]:
            pass
            self.in_modes_and_transitions()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
        return retValue
    
    def connection_refinement(self):    
        retValue = None
        
        id = None
        pass
        if not self.inputState.guessing:
            retValue = UniquePortIdentifier(None, None) # Don't handle these yet
        id = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        self.match(REFINED)
        self.match(TO)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [PORT]:
            pass
            self.match(PORT)
            self.match(GROUP)
        elif la1 and la1 in [PARAMETER]:
            pass
            self.match(PARAMETER)
        elif la1 and la1 in [BUS]:
            pass
            self.match(BUS)
            self.match(ACCESS)
        else:
            if (self.LA(1)==EVENT) and (self.LA(2)==DATA):
                pass
                self.match(EVENT)
                self.match(DATA)
                self.match(PORT)
            elif (self.LA(1)==EVENT) and (self.LA(2)==PORT):
                pass
                self.match(EVENT)
                self.match(PORT)
            elif (self.LA(1)==DATA) and (self.LA(2)==PORT):
                pass
                self.match(DATA)
                self.match(PORT)
            elif (self.LA(1)==DATA) and (self.LA(2)==ACCESS):
                pass
                self.match(DATA)
                self.match(ACCESS)
            else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            pass
            self.curlyPropertyAssociations()
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [IN]:
                pass
                self.in_modes_and_transitions()
            elif la1 and la1 in [SEMI]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
        elif la1 and la1 in [IN]:
            pass
            self.in_modes_and_transitions()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
        return retValue
    
    def data_connection(self):    
        retValue = None
        
        pass
        self.match(DATA)
        self.match(PORT)
        u1=self.unique_port_identifier()
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [ARROW]:
            pass
            self.match(ARROW)
        elif la1 and la1 in [DARROW]:
            pass
            self.match(DARROW)
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        u2=self.unique_port_identifier()
        if not self.inputState.guessing:
            retValue = Connection(u1, u2)
        return retValue
    
    def event_data_connection(self):    
        retValue = None
        
        pass
        self.match(EVENT)
        self.match(DATA)
        self.match(PORT)
        u1=self.unique_port_identifier()
        self.match(ARROW)
        u2=self.unique_port_identifier()
        if not self.inputState.guessing:
            retValue = Connection(u1, u2)
        return retValue
    
    def event_connection(self):    
        retValue = None
        
        pass
        self.match(EVENT)
        self.match(PORT)
        u1=self.unique_port_identifier()
        self.match(ARROW)
        u2=self.unique_port_identifier()
        if not self.inputState.guessing:
            retValue = Connection(u1, u2)
        return retValue
    
    def port_group_connection(self):    
        retValue = None
        
        pass
        self.match(PORT)
        self.match(GROUP)
        u1=self.unique_port_group_identifier()
        self.match(ARROW)
        u2=self.unique_port_group_identifier()
        if not self.inputState.guessing:
            retValue = Connection(u1, u2)
        return retValue
    
    def parameter_connection(self):    
        retValue = None
        
        pass
        self.match(PARAMETER)
        u1=self.unique_port_identifier()
        self.match(ARROW)
        u2=self.unique_port_identifier()
        if not self.inputState.guessing:
            retValue = Connection(u1, u2)
        return retValue
    
    def bus_access_connection(self):    
        retValue = None
        
        pass
        self.match(BUS)
        self.match(ACCESS)
        u1=self.unique_port_identifier()
        self.match(ARROW)
        u2=self.unique_port_identifier()
        if not self.inputState.guessing:
            retValue = Connection(u1, u2)
        return retValue
    
    def data_access_connection(self):    
        retValue = None
        
        pass
        self.match(DATA)
        self.match(ACCESS)
        u1=self.unique_port_identifier()
        self.match(ARROW)
        u2=self.unique_port_identifier()
        if not self.inputState.guessing:
            retValue = Connection(u1, u2)
        return retValue
    
    def unique_port_group_identifier(self):    
        retValue = None
        
        compid = None
        portid = None
        soleportid = None
        if (self.LA(1)==IDENT) and (self.LA(2)==DOT):
            pass
            compid = self.LT(1)
            self.match(IDENT)
            self.match(DOT)
            portid = self.LT(1)
            self.match(IDENT)
            if not self.inputState.guessing:
                retValue = UniquePortIdentifier(compid.getText(), portid.getText())
        elif (self.LA(1)==IDENT) and (_tokenSet_35.member(self.LA(2))):
            pass
            soleportid = self.LT(1)
            self.match(IDENT)
            if not self.inputState.guessing:
                retValue = UniquePortIdentifier(None, portid.getText())
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
        return retValue
    
    def data_access_connection_decl(self):    
        
        id = None
        pass
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            id = self.LT(1)
            self.match(IDENT)
            self.match(COLON)
        elif la1 and la1 in [DATA]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        dac=self.data_access_connection()
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            self.curlyPropertyAssociations()
        elif la1 and la1 in [SEMI,IN]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IN]:
            pass
            self.in_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
    
    def data_access_connection_refinement_decl(self):    
        
        id = None
        pass
        id = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        self.match(REFINED)
        self.match(TO)
        self.match(DATA)
        self.match(ACCESS)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            pass
            self.curlyPropertyAssociations()
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [IN]:
                pass
                self.in_modes()
            elif la1 and la1 in [SEMI]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
        elif la1 and la1 in [IN]:
            pass
            self.in_modes()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
    
    def bus_access_connection_decl(self):    
        
        id = None
        pass
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IDENT]:
            pass
            id = self.LT(1)
            self.match(IDENT)
            self.match(COLON)
        elif la1 and la1 in [BUS]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        bac=self.bus_access_connection()
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            self.curlyPropertyAssociations()
        elif la1 and la1 in [SEMI,IN]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IN]:
            pass
            self.in_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
    
    def bus_access_connection_refinement_decl(self):    
        
        id = None
        pass
        id = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        self.match(REFINED)
        self.match(TO)
        self.match(BUS)
        self.match(ACCESS)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            pass
            self.curlyPropertyAssociations()
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [IN]:
                pass
                self.in_modes()
            elif la1 and la1 in [SEMI]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
        elif la1 and la1 in [IN]:
            pass
            self.in_modes()
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
    
    def flow_spec(self):    
        
        defining_identifier = None
        pass
        defining_identifier = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        if (self.LA(1)==FLOW) and (self.LA(2)==SOURCE):
            pass
            self.flow_source_spec()
        elif (self.LA(1)==FLOW) and (self.LA(2)==SINK):
            pass
            self.flow_sink_spec()
        elif (self.LA(1)==FLOW) and (self.LA(2)==PATH):
            pass
            self.flow_path_spec()
        elif (self.LA(1)==REFINED):
            pass
            pass
            self.match(REFINED)
            self.match(TO)
            if (self.LA(1)==FLOW) and (self.LA(2)==SOURCE):
                pass
                self.flow_source_spec_refinement()
            elif (self.LA(1)==FLOW) and (self.LA(2)==SINK):
                pass
                self.flow_sink_spec_refinement()
            elif (self.LA(1)==FLOW) and (self.LA(2)==PATH):
                pass
                self.flow_path_spec_refinement()
            else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
        self.match(SEMI)
    
    def flow_source_spec(self):    
        
        pass
        self.match(FLOW)
        self.match(SOURCE)
        self.flow_feature_identifier()
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            cpa=self.curlyPropertyAssociations_no_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def flow_sink_spec(self):    
        
        pass
        self.match(FLOW)
        self.match(SINK)
        self.flow_feature_identifier()
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            cpa=self.curlyPropertyAssociations_no_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def flow_path_spec(self):    
        
        pass
        self.match(FLOW)
        self.match(PATH)
        self.flow_feature_identifier()
        self.match(ARROW)
        self.flow_feature_identifier()
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            cpa=self.curlyPropertyAssociations_no_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def flow_source_spec_refinement(self):    
        
        pass
        self.match(FLOW)
        self.match(SOURCE)
        cpa=self.curlyPropertyAssociations_no_modes()
    
    def flow_sink_spec_refinement(self):    
        
        pass
        self.match(FLOW)
        self.match(SINK)
        cpa=self.curlyPropertyAssociations_no_modes()
    
    def flow_path_spec_refinement(self):    
        
        pass
        self.match(FLOW)
        self.match(PATH)
        cpa=self.curlyPropertyAssociations_no_modes()
    
    def flow_feature_identifier(self):    
        
        compid = None
        portid = None
        soleportid = None
        if (self.LA(1)==IDENT) and (self.LA(2)==DOT):
            pass
            compid = self.LT(1)
            self.match(IDENT)
            self.match(DOT)
            portid = self.LT(1)
            self.match(IDENT)
        elif (self.LA(1)==IDENT) and (_tokenSet_35.member(self.LA(2))):
            pass
            soleportid = self.LT(1)
            self.match(IDENT)
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
    
    def flow_sequence(self):    
        
        defining_identifier = None
        pass
        defining_identifier = self.LT(1)
        self.match(IDENT)
        self.match(COLON)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [END]:
            pass
            self.end_to_end_flow()
        elif la1 and la1 in [REFINED]:
            pass
            pass
            self.match(REFINED)
            self.match(TO)
            if (self.LA(1)==FLOW) and (self.LA(2)==SOURCE):
                pass
                self.flow_source_implementation_refinement()
            elif (self.LA(1)==FLOW) and (self.LA(2)==SINK):
                pass
                self.flow_sink_implementation_refinement()
            elif (self.LA(1)==FLOW) and (self.LA(2)==PATH):
                pass
                self.flow_path_implementation_refinement()
            elif (self.LA(1)==END):
                pass
                self.end_to_end_flow_refinement()
            else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        else:
            if (self.LA(1)==FLOW) and (self.LA(2)==SOURCE):
                pass
                self.flow_source_implementation()
            elif (self.LA(1)==FLOW) and (self.LA(2)==SINK):
                pass
                self.flow_sink_implementation()
            elif (self.LA(1)==FLOW) and (self.LA(2)==PATH):
                pass
                self.flow_path_implementation()
            else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        self.match(SEMI)
    
    def flow_source_implementation(self):    
        
        pass
        self.match(FLOW)
        self.match(SOURCE)
        while True:
            if (self.LA(1)==IDENT) and (self.LA(2)==DOT) and (self.LA(3)==IDENT) and (self.LA(4)==ARROW):
                pass
                self.subcomponent_flow_identifier()
                self.match(ARROW)
                self.connection_identifier()
                self.match(ARROW)
            else:
                break
            
        self.flow_feature_identifier()
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            self.curlyPropertyAssociations()
        elif la1 and la1 in [SEMI,IN]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IN]:
            pass
            self.in_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def flow_sink_implementation(self):    
        
        pass
        self.match(FLOW)
        self.match(SINK)
        self.flow_feature_identifier()
        while True:
            if (self.LA(1)==ARROW):
                pass
                self.match(ARROW)
                self.connection_identifier()
                self.match(ARROW)
                self.subcomponent_flow_identifier()
            else:
                break
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            self.curlyPropertyAssociations()
        elif la1 and la1 in [SEMI,IN]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IN]:
            pass
            self.in_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def flow_path_implementation(self):    
        
        pass
        self.match(FLOW)
        self.match(PATH)
        self.flow_feature_identifier()
        self.match(ARROW)
        if (self.LA(1)==IDENT) and (self.LA(2)==ARROW):
            pass
            self.connection_identifier()
            self.match(ARROW)
            _cnt719= 0
            while True:
                if (self.LA(1)==IDENT) and (self.LA(2)==DOT) and (self.LA(3)==IDENT) and (self.LA(4)==ARROW):
                    pass
                    self.subcomponent_flow_identifier()
                    self.match(ARROW)
                    self.connection_identifier()
                    self.match(ARROW)
                else:
                    break
                
                _cnt719 += 1
            if _cnt719 < 1:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        elif (self.LA(1)==IDENT) and (_tokenSet_36.member(self.LA(2))):
            pass
        else:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        
        self.flow_feature_identifier()
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            self.curlyPropertyAssociations()
        elif la1 and la1 in [SEMI,IN]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IN]:
            pass
            self.in_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def end_to_end_flow(self):    
        
        pass
        self.match(END)
        self.match(TO)
        self.match(END)
        self.match(FLOW)
        self.subcomponent_flow_identifier()
        _cnt734= 0
        while True:
            if (self.LA(1)==ARROW):
                pass
                self.match(ARROW)
                self.connection_identifier()
                self.match(ARROW)
                self.subcomponent_flow_identifier()
            else:
                break
            
            _cnt734 += 1
        if _cnt734 < 1:
            raise antlr.NoViableAltException(self.LT(1), self.getFilename())
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            self.curlyPropertyAssociations()
        elif la1 and la1 in [SEMI,IN]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [IN]:
            pass
            self.in_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def flow_source_implementation_refinement(self):    
        
        pass
        self.match(FLOW)
        self.match(SOURCE)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            self.curlyPropertyAssociations()
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [IN]:
                pass
                self.in_modes()
            elif la1 and la1 in [SEMI]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
        elif la1 and la1 in [IN]:
            pass
            self.in_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def flow_sink_implementation_refinement(self):    
        
        pass
        self.match(FLOW)
        self.match(SINK)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            self.curlyPropertyAssociations()
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [IN]:
                pass
                self.in_modes()
            elif la1 and la1 in [SEMI]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
        elif la1 and la1 in [IN]:
            pass
            self.in_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def flow_path_implementation_refinement(self):    
        
        pass
        self.match(FLOW)
        self.match(PATH)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            self.curlyPropertyAssociations()
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [IN]:
                pass
                self.in_modes()
            elif la1 and la1 in [SEMI]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
        elif la1 and la1 in [IN]:
            pass
            self.in_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def end_to_end_flow_refinement(self):    
        
        pass
        self.match(END)
        self.match(TO)
        self.match(END)
        self.match(FLOW)
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in [LCURLY]:
            pass
            self.curlyPropertyAssociations()
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [IN]:
                pass
                self.in_modes()
            elif la1 and la1 in [SEMI]:
                pass
            else:
                    raise antlr.NoViableAltException(self.LT(1), self.getFilename())
                
        elif la1 and la1 in [IN]:
            pass
            self.in_modes()
        elif la1 and la1 in [SEMI]:
            pass
        else:
                raise antlr.NoViableAltException(self.LT(1), self.getFilename())
            
    
    def subcomponent_flow_identifier(self):    
        
        subcompid = None
        flowid = None
        pass
        subcompid = self.LT(1)
        self.match(IDENT)
        self.match(DOT)
        flowid = self.LT(1)
        self.match(IDENT)
    
    def connection_identifier(self):    
        
        connid = None
        pass
        connid = self.LT(1)
        self.match(IDENT)
    

_tokenNames = [
    "<0>", 
    "EOF", 
    "<2>", 
    "NULL_TREE_LOOKAHEAD", 
    "\"package\"", 
    "\"end\"", 
    "SEMI", 
    "\"public\"", 
    "\"private\"", 
    "IDENT", 
    "DOUBLECOLON", 
    "\"none\"", 
    "\"thread\"", 
    "\"extends\"", 
    "\"group\"", 
    "\"process\"", 
    "\"system\"", 
    "\"subprogram\"", 
    "\"data\"", 
    "\"processor\"", 
    "\"memory\"", 
    "\"bus\"", 
    "\"device\"", 
    "DOT", 
    "\"implementation\"", 
    "\"features\"", 
    "COLON", 
    "\"refined\"", 
    "\"to\"", 
    "\"provides\"", 
    "\"requires\"", 
    "\"refines\"", 
    "\"type\"", 
    "\"subcomponents\"", 
    "\"annex\"", 
    "ANNEX_TEXT", 
    "\"property\"", 
    "\"set\"", 
    "\"is\"", 
    "\"aadlboolean\"", 
    "\"aadlstring\"", 
    "\"enumeration\"", 
    "LPAREN", 
    "COMMA", 
    "RPAREN", 
    "\"units\"", 
    "ASSIGN", 
    "STAR", 
    "\"aadlreal\"", 
    "\"aadlinteger\"", 
    "DOTDOT", 
    "PLUS", 
    "MINUS", 
    "NUMERIC_LIT", 
    "\"range\"", 
    "\"of\"", 
    "\"classifier\"", 
    "\"reference\"", 
    "\"connections\"", 
    "\"server\"", 
    "\"access\"", 
    "\"inherit\"", 
    "\"applies\"", 
    "\"all\"", 
    "\"mode\"", 
    "\"port\"", 
    "\"event\"", 
    "\"flow\"", 
    "\"parameter\"", 
    "\"list\"", 
    "\"constant\"", 
    "\"delta\"", 
    "\"properties\"", 
    "LCURLY", 
    "RCURLY", 
    "ASSIGNPLUS", 
    "\"value\"", 
    "\"in\"", 
    "\"binding\"", 
    "\"or\"", 
    "\"and\"", 
    "\"true\"", 
    "\"false\"", 
    "NOT", 
    "STRING_LITERAL", 
    "\"calls\"", 
    "\"modes\"", 
    "\"initial\"", 
    "LTRANS", 
    "RTRANS", 
    "ARROW", 
    "\"out\"", 
    "\"inverse\"", 
    "DARROW", 
    "\"flows\"", 
    "\"source\"", 
    "\"sink\"", 
    "\"path\"", 
    "AADLSPEC", 
    "\"not\"", 
    "\"transitions\"", 
    "HASH", 
    "DIGIT", 
    "EXPONENT", 
    "INT_EXPONENT", 
    "EXTENDED_DIGIT", 
    "BASED_INTEGER", 
    "BASE", 
    "ESC", 
    "HEX_DIGIT", 
    "WS", 
    "SL_COMMENT"
]
    

### generate bit set
def mk_tokenSet_0(): 
    ### var1
    data = [ 85907705872, 2, 0, 0]
    return data
_tokenSet_0 = antlr.BitSet(mk_tokenSet_0())

### generate bit set
def mk_tokenSet_1(): 
    ### var1
    data = [ 17188229120, 2, 0, 0]
    return data
_tokenSet_1 = antlr.BitSet(mk_tokenSet_1())

### generate bit set
def mk_tokenSet_2(): 
    ### var1
    data = [ 576, 528, 0, 0]
    return data
_tokenSet_2 = antlr.BitSet(mk_tokenSet_2())

### generate bit set
def mk_tokenSet_3(): 
    ### var1
    data = [ 2359808, 22, 0, 0]
    return data
_tokenSet_3 = antlr.BitSet(mk_tokenSet_3())

### generate bit set
def mk_tokenSet_4(): 
    ### var1
    data = [ 1152921504674234880, 2, 0, 0]
    return data
_tokenSet_4 = antlr.BitSet(mk_tokenSet_4())

### generate bit set
def mk_tokenSet_5(): 
    ### var1
    data = [ 10748416, 67108886, 0, 0]
    return data
_tokenSet_5 = antlr.BitSet(mk_tokenSet_5())

### generate bit set
def mk_tokenSet_6(): 
    ### var1
    data = [ 576, 8704, 0, 0]
    return data
_tokenSet_6 = antlr.BitSet(mk_tokenSet_6())

### generate bit set
def mk_tokenSet_7(): 
    ### var1
    data = [ 4621924670705238592, 0]
    return data
_tokenSet_7 = antlr.BitSet(mk_tokenSet_7())

### generate bit set
def mk_tokenSet_8(): 
    ### var1
    data = [ 4620719605961196096, 8320, 0, 0]
    return data
_tokenSet_8 = antlr.BitSet(mk_tokenSet_8())

### generate bit set
def mk_tokenSet_9(): 
    ### var1
    data = [ 4621845505868038720, 8192, 0, 0]
    return data
_tokenSet_9 = antlr.BitSet(mk_tokenSet_9())

### generate bit set
def mk_tokenSet_10(): 
    ### var1
    data = [ 4611712406706455104, 8192, 0, 0]
    return data
_tokenSet_10 = antlr.BitSet(mk_tokenSet_10())

### generate bit set
def mk_tokenSet_11(): 
    ### var1
    data = [ 16888498602639872, 0]
    return data
_tokenSet_11 = antlr.BitSet(mk_tokenSet_11())

### generate bit set
def mk_tokenSet_12(): 
    ### var1
    data = [ 16888498602639936, 128, 0, 0]
    return data
_tokenSet_12 = antlr.BitSet(mk_tokenSet_12())

### generate bit set
def mk_tokenSet_13(): 
    ### var1
    data = [ 67109472, 0]
    return data
_tokenSet_13 = antlr.BitSet(mk_tokenSet_13())

### generate bit set
def mk_tokenSet_14(): 
    ### var1
    data = [ 16914886881706496, 128, 0, 0]
    return data
_tokenSet_14 = antlr.BitSet(mk_tokenSet_14())

### generate bit set
def mk_tokenSet_15(): 
    ### var1
    data = [ 9033587533808128, 0]
    return data
_tokenSet_15 = antlr.BitSet(mk_tokenSet_15())

### generate bit set
def mk_tokenSet_16(): 
    ### var1
    data = [ 15788986974863936, 0]
    return data
_tokenSet_16 = antlr.BitSet(mk_tokenSet_16())

### generate bit set
def mk_tokenSet_17(): 
    ### var1
    data = [ 15788986974863968, 0]
    return data
_tokenSet_17 = antlr.BitSet(mk_tokenSet_17())

### generate bit set
def mk_tokenSet_18(): 
    ### var1
    data = [ 800, 4195328, 0, 0]
    return data
_tokenSet_18 = antlr.BitSet(mk_tokenSet_18())

### generate bit set
def mk_tokenSet_19(): 
    ### var1
    data = [ 17179869728, 4195328, 0, 0]
    return data
_tokenSet_19 = antlr.BitSet(mk_tokenSet_19())

### generate bit set
def mk_tokenSet_20(): 
    ### var1
    data = [ 159882184826524160, 1970176, 0, 0]
    return data
_tokenSet_20 = antlr.BitSet(mk_tokenSet_20())

### generate bit set
def mk_tokenSet_21(): 
    ### var1
    data = [ 10146293301133824, 1019904, 0, 0]
    return data
_tokenSet_21 = antlr.BitSet(mk_tokenSet_21())

### generate bit set
def mk_tokenSet_22(): 
    ### var1
    data = [ 161034473020823040, 2068480, 0, 0]
    return data
_tokenSet_22 = antlr.BitSet(mk_tokenSet_22())

### generate bit set
def mk_tokenSet_23(): 
    ### var1
    data = [ 159895378966057472, 1048576, 0, 0]
    return data
_tokenSet_23 = antlr.BitSet(mk_tokenSet_23())

### generate bit set
def mk_tokenSet_24(): 
    ### var1
    data = [ 4621836709775032896, 12288, 0, 0]
    return data
_tokenSet_24 = antlr.BitSet(mk_tokenSet_24())

### generate bit set
def mk_tokenSet_25(): 
    ### var1
    data = [ 4628596524719277920, 4224000, 0, 0]
    return data
_tokenSet_25 = antlr.BitSet(mk_tokenSet_25())

### generate bit set
def mk_tokenSet_26(): 
    ### var1
    data = [ 159877786780013056, 1048576, 0, 0]
    return data
_tokenSet_26 = antlr.BitSet(mk_tokenSet_26())

### generate bit set
def mk_tokenSet_27(): 
    ### var1
    data = [ 4398046511104, 921600, 0, 0]
    return data
_tokenSet_27 = antlr.BitSet(mk_tokenSet_27())

### generate bit set
def mk_tokenSet_28(): 
    ### var1
    data = [ 4611690416473899072, 1028096, 0, 0]
    return data
_tokenSet_28 = antlr.BitSet(mk_tokenSet_28())

### generate bit set
def mk_tokenSet_29(): 
    ### var1
    data = [ 4611708026108248928, 5239808, 0, 0]
    return data
_tokenSet_29 = antlr.BitSet(mk_tokenSet_29())

### generate bit set
def mk_tokenSet_30(): 
    ### var1
    data = [ 4611778394860787552, 5241858, 0, 0]
    return data
_tokenSet_30 = antlr.BitSet(mk_tokenSet_30())

### generate bit set
def mk_tokenSet_31(): 
    ### var1
    data = [ 4621845505868038720, 12288, 0, 0]
    return data
_tokenSet_31 = antlr.BitSet(mk_tokenSet_31())

### generate bit set
def mk_tokenSet_32(): 
    ### var1
    data = [ 4772720508888126304, 6190080, 0, 0]
    return data
_tokenSet_32 = antlr.BitSet(mk_tokenSet_32())

### generate bit set
def mk_tokenSet_33(): 
    ### var1
    data = [ 4772790877632321376, 6290562, 0, 0]
    return data
_tokenSet_33 = antlr.BitSet(mk_tokenSet_33())

### generate bit set
def mk_tokenSet_34(): 
    ### var1
    data = [ 8796093022272, 637542912, 0, 0]
    return data
_tokenSet_34 = antlr.BitSet(mk_tokenSet_34())

### generate bit set
def mk_tokenSet_35(): 
    ### var1
    data = [ 64, 67117568, 0, 0]
    return data
_tokenSet_35 = antlr.BitSet(mk_tokenSet_35())

### generate bit set
def mk_tokenSet_36(): 
    ### var1
    data = [ 8388672, 8704, 0, 0]
    return data
_tokenSet_36 = antlr.BitSet(mk_tokenSet_36())
    
