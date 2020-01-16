### $ANTLR 2.7.7 (20160127): "aadl.g" -> "AadlLexer.py"$
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
### preamble action >>> 

### preamble action <<< 
### >>>The Literals<<<
literals = {}
literals[u"type"] = 32
literals[u"inverse"] = 94
literals[u"constant"] = 70
literals[u"connections"] = 58
literals[u"public"] = 7
literals[u"list"] = 69
literals[u"initial"] = 89
literals[u"applies"] = 62
literals[u"end"] = 5
literals[u"aadlboolean"] = 39
literals[u"flows"] = 96
literals[u"memory"] = 20
literals[u"aadlstring"] = 40
literals[u"flow"] = 67
literals[u"system"] = 16
literals[u"implementation"] = 24
literals[u"to"] = 28
literals[u"and"] = 82
literals[u"not"] = 101
literals[u"package"] = 4
literals[u"inherit"] = 61
literals[u"aadlreal"] = 48
literals[u"source"] = 97
literals[u"reference"] = 57
literals[u"provides"] = 29
literals[u"server"] = 59
literals[u"sink"] = 98
literals[u"event"] = 66
literals[u"range"] = 54
literals[u"enumeration"] = 41
literals[u"calls"] = 87
literals[u"out"] = 93
literals[u"set"] = 37
literals[u"parameter"] = 68
literals[u"of"] = 55
literals[u"is"] = 38
literals[u"aadlinteger"] = 49
literals[u"or"] = 81
literals[u"access"] = 60
literals[u"none"] = 11
literals[u"features"] = 25
literals[u"data"] = 18
literals[u"all"] = 63
literals[u"thread"] = 12
literals[u"path"] = 99
literals[u"properties"] = 72
literals[u"units"] = 45
literals[u"bus"] = 21
literals[u"binding"] = 78
literals[u"extends"] = 13
literals[u"private"] = 8
literals[u"port"] = 65
literals[u"requires"] = 30
literals[u"refines"] = 31
literals[u"false"] = 84
literals[u"processor"] = 19
literals[u"device"] = 22
literals[u"property"] = 36
literals[u"annex"] = 34
literals[u"classifier"] = 56
literals[u"transitions"] = 102
literals[u"process"] = 15
literals[u"value"] = 76
literals[u"modes"] = 88
literals[u"in"] = 77
literals[u"delta"] = 71
literals[u"mode"] = 64
literals[u"true"] = 83
literals[u"group"] = 14
literals[u"refined"] = 27
literals[u"subprogram"] = 17
literals[u"subcomponents"] = 33


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
LBRACKET = 79
RBRACKET = 80
OR = 81
AND = 82
TRUE = 83
FALSE = 84
NOT = 85
STRING_LITERAL = 86
CALLS = 87
MODES = 88
INITIAL = 89
LTRANS = 90
RTRANS = 91
ARROW = 92
OUT = 93
INVERSE = 94
DARROW = 95
FLOWS = 96
SOURCE = 97
SINK = 98
PATH = 99
AADLSPEC = 100
NOTT = 101
TRANSITIONS = 102
HASH = 103
DIGIT = 104
EXPONENT = 105
INT_EXPONENT = 106
EXTENDED_DIGIT = 107
BASED_INTEGER = 108
BASE = 109
ESC = 110
HEX_DIGIT = 111
WS = 112
SL_COMMENT = 113

class Lexer(antlr.CharScanner) :
    ### user action >>>
    ### user action <<<
    def __init__(self, *argv, **kwargs) :
        antlr.CharScanner.__init__(self, *argv, **kwargs)
        self.caseSensitiveLiterals = False
        self.setCaseSensitive(False)
        self.literals = literals
    
    def nextToken(self):
        while True:
            try: ### try again ..
                while True:
                    _token = None
                    _ttype = INVALID_TYPE
                    self.resetText()
                    try: ## for char stream error handling
                        try: ##for lexical error handling
                            la1 = self.LA(1)
                            if False:
                                pass
                            elif la1 and la1 in u'(':
                                pass
                                self.mLPAREN(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u')':
                                pass
                                self.mRPAREN(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u'[':
                                pass
                                self.mLBRACKET(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u'}':
                                pass
                                self.mRCURLY(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u'*':
                                pass
                                self.mSTAR(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u';':
                                pass
                                self.mSEMI(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u',':
                                pass
                                self.mCOMMA(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u'=':
                                pass
                                self.mASSIGN(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u'#':
                                pass
                                self.mHASH(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u'abcdefghijklmnopqrstuvwxyz':
                                pass
                                self.mIDENT(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u'"':
                                pass
                                self.mSTRING_LITERAL(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u'0123456789':
                                pass
                                self.mNUMERIC_LIT(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u'\t\n\r ':
                                pass
                                self.mWS(True)
                                theRetToken = self._returnToken
                            else:
                                if (self.LA(1)==u'-') and (self.LA(2)==u'>') and (self.LA(3)==u'>'):
                                    pass
                                    self.mDARROW(True)
                                    theRetToken = self._returnToken
                                elif (self.LA(1)==u'.') and (self.LA(2)==u'.'):
                                    pass
                                    self.mDOTDOT(True)
                                    theRetToken = self._returnToken
                                elif (self.LA(1)==u'+') and (self.LA(2)==u'='):
                                    pass
                                    self.mASSIGNPLUS(True)
                                    theRetToken = self._returnToken
                                elif (self.LA(1)==u':') and (self.LA(2)==u':'):
                                    pass
                                    self.mDOUBLECOLON(True)
                                    theRetToken = self._returnToken
                                elif (self.LA(1)==u'-') and (self.LA(2)==u'['):
                                    pass
                                    self.mLTRANS(True)
                                    theRetToken = self._returnToken
                                elif (self.LA(1)==u']') and (self.LA(2)==u'-'):
                                    pass
                                    self.mRTRANS(True)
                                    theRetToken = self._returnToken
                                elif (self.LA(1)==u'-') and (self.LA(2)==u'>') and (True):
                                    pass
                                    self.mARROW(True)
                                    theRetToken = self._returnToken
                                elif (self.LA(1)==u'{') and (self.LA(2)==u'*'):
                                    pass
                                    self.mANNEX_TEXT(True)
                                    theRetToken = self._returnToken
                                elif (self.LA(1)==u'-') and (self.LA(2)==u'-'):
                                    pass
                                    self.mSL_COMMENT(True)
                                    theRetToken = self._returnToken
                                elif (self.LA(1)==u'{') and (True):
                                    pass
                                    self.mLCURLY(True)
                                    theRetToken = self._returnToken
                                elif (self.LA(1)==u']') and (True):
                                    pass
                                    self.mRBRACKET(True)
                                    theRetToken = self._returnToken
                                elif (self.LA(1)==u':') and (True):
                                    pass
                                    self.mCOLON(True)
                                    theRetToken = self._returnToken
                                elif (self.LA(1)==u'+') and (True):
                                    pass
                                    self.mPLUS(True)
                                    theRetToken = self._returnToken
                                elif (self.LA(1)==u'-') and (True):
                                    pass
                                    self.mMINUS(True)
                                    theRetToken = self._returnToken
                                elif (self.LA(1)==u'.') and (True):
                                    pass
                                    self.mDOT(True)
                                    theRetToken = self._returnToken
                                else:
                                    self.default(self.LA(1))
                                
                            if not self._returnToken:
                                raise antlr.TryAgain ### found SKIP token
                            ### option { testLiterals=true } 
                            self.testForLiteral(self._returnToken)
                            ### return token to caller
                            return self._returnToken
                        ### handle lexical errors ....
                        except antlr.RecognitionException, e:
                            self.reportError(e)
                            self.consume()
                    ### handle char stream errors ...
                    except antlr.CharStreamException,cse:
                        if isinstance(cse, antlr.CharStreamIOException):
                            raise antlr.TokenStreamIOException(cse.io)
                        else:
                            raise antlr.TokenStreamException(str(cse))
            except antlr.TryAgain:
                pass
        
    def mLPAREN(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = LPAREN
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match('(')
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mRPAREN(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = RPAREN
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match(')')
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mLCURLY(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = LCURLY
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match('{')
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mLBRACKET(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = LBRACKET
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match('[')
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mRBRACKET(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = RBRACKET
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match(']')
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mRCURLY(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = RCURLY
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match('}')
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mCOLON(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = COLON
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match(':')
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mPLUS(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = PLUS
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match('+')
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mMINUS(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = MINUS
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match('-')
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mSTAR(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = STAR
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match('*')
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mSEMI(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = SEMI
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match(';')
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mCOMMA(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = COMMA
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match(',')
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mDOT(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = DOT
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match('.')
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mDOTDOT(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = DOTDOT
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match("..")
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mASSIGN(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = ASSIGN
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match("=>")
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mASSIGNPLUS(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = ASSIGNPLUS
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match("+=>")
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mDOUBLECOLON(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = DOUBLECOLON
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match("::")
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mLTRANS(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = LTRANS
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match("-[")
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mRTRANS(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = RTRANS
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match("]->")
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mARROW(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = ARROW
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match("->")
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mDARROW(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = DARROW
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match("->>")
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mHASH(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = HASH
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match('#')
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mIDENT(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = IDENT
        _saveIndex = 0
        try:      ## for error handling
            pass
            pass
            self.matchRange(u'a', u'z')
            while True:
                if (_tokenSet_1.member(self.LA(1))):
                    pass
                    la1 = self.LA(1)
                    if False:
                        pass
                    elif la1 and la1 in u'_':
                        pass
                        self.match('_')
                    elif la1 and la1 in u'0123456789abcdefghijklmnopqrstuvwxyz':
                        pass
                    else:
                            self.raise_NoViableAlt(self.LA(1))
                        
                    la1 = self.LA(1)
                    if False:
                        pass
                    elif la1 and la1 in u'abcdefghijklmnopqrstuvwxyz':
                        pass
                        self.matchRange(u'a', u'z')
                    elif la1 and la1 in u'0123456789':
                        pass
                        self.matchRange(u'0', u'9')
                    else:
                            self.raise_NoViableAlt(self.LA(1))
                        
                else:
                    break
                
        
        except antlr.RecognitionException, ex:
            self.reportError(ex);
            self.consume();
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mSTRING_LITERAL(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = STRING_LITERAL
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match('"')
            while True:
                if (self.LA(1)==u'\\'):
                    pass
                    self.mESC(False)
                elif (_tokenSet_2.member(self.LA(1))):
                    pass
                    self.match(_tokenSet_2)
                else:
                    break
                
            self.match('"')
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mESC(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = ESC
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match('\\')
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in u'n':
                pass
                self.match('n')
            elif la1 and la1 in u'r':
                pass
                self.match('r')
            elif la1 and la1 in u't':
                pass
                self.match('t')
            elif la1 and la1 in u'b':
                pass
                self.match('b')
            elif la1 and la1 in u'f':
                pass
                self.match('f')
            elif la1 and la1 in u'"':
                pass
                self.match('"')
            elif la1 and la1 in u'\'':
                pass
                self.match('\'')
            elif la1 and la1 in u'\\':
                pass
                self.match('\\')
            elif la1 and la1 in u'u':
                pass
                _cnt823= 0
                while True:
                    if (self.LA(1)==u'u'):
                        pass
                        self.match('u')
                    else:
                        break
                    
                    _cnt823 += 1
                if _cnt823 < 1:
                    self.raise_NoViableAlt(self.LA(1))
                self.mHEX_DIGIT(False)
                self.mHEX_DIGIT(False)
                self.mHEX_DIGIT(False)
                self.mHEX_DIGIT(False)
            elif la1 and la1 in u'0123':
                pass
                self.matchRange(u'0', u'3')
                if ((self.LA(1) >= u'0' and self.LA(1) <= u'7')) and ((self.LA(2) >= u'\u0000' and self.LA(2) <= u'\ufffe')) and (True):
                    pass
                    self.matchRange(u'0', u'7')
                    if ((self.LA(1) >= u'0' and self.LA(1) <= u'7')) and ((self.LA(2) >= u'\u0000' and self.LA(2) <= u'\ufffe')) and (True):
                        pass
                        self.matchRange(u'0', u'7')
                    elif ((self.LA(1) >= u'\u0000' and self.LA(1) <= u'\ufffe')) and (True) and (True):
                        pass
                    else:
                        self.raise_NoViableAlt(self.LA(1))
                    
                elif ((self.LA(1) >= u'\u0000' and self.LA(1) <= u'\ufffe')) and (True) and (True):
                    pass
                else:
                    self.raise_NoViableAlt(self.LA(1))
                
            elif la1 and la1 in u'4567':
                pass
                self.matchRange(u'4', u'7')
                if ((self.LA(1) >= u'0' and self.LA(1) <= u'7')) and ((self.LA(2) >= u'\u0000' and self.LA(2) <= u'\ufffe')) and (True):
                    pass
                    self.matchRange(u'0', u'7')
                elif ((self.LA(1) >= u'\u0000' and self.LA(1) <= u'\ufffe')) and (True) and (True):
                    pass
                else:
                    self.raise_NoViableAlt(self.LA(1))
                
            else:
                    self.raise_NoViableAlt(self.LA(1))
                
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_3)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mNUMERIC_LIT(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = NUMERIC_LIT
        _saveIndex = 0
        try:      ## for error handling
            pass
            _cnt781= 0
            while True:
                if ((self.LA(1) >= u'0' and self.LA(1) <= u'9')):
                    pass
                    self.mDIGIT(False)
                else:
                    break
                
                _cnt781 += 1
            if _cnt781 < 1:
                self.raise_NoViableAlt(self.LA(1))
            if (self.LA(1)==u'#'):
                pass
                pass
                self.match('#')
                self.mBASED_INTEGER(False)
                self.match('#')
                if (self.LA(1)==u'e'):
                    pass
                    self.mINT_EXPONENT(False)
                else: ## <m4>
                        pass
                    
            else: ## <m4>
                    pass
                    while True:
                        if (self.LA(1)==u'_'):
                            pass
                            self.match('_')
                            _cnt787= 0
                            while True:
                                if ((self.LA(1) >= u'0' and self.LA(1) <= u'9')):
                                    pass
                                    self.mDIGIT(False)
                                else:
                                    break
                                
                                _cnt787 += 1
                            if _cnt787 < 1:
                                self.raise_NoViableAlt(self.LA(1))
                        else:
                            break
                        
                    if ((self.LA(1)==u'.') and ( LA(2)!='.' )):
                        pass
                        pass
                        self.match('.')
                        _cnt792= 0
                        while True:
                            if ((self.LA(1) >= u'0' and self.LA(1) <= u'9')):
                                pass
                                self.mDIGIT(False)
                            else:
                                break
                            
                            _cnt792 += 1
                        if _cnt792 < 1:
                            self.raise_NoViableAlt(self.LA(1))
                        while True:
                            if (self.LA(1)==u'_'):
                                pass
                                self.match('_')
                                _cnt795= 0
                                while True:
                                    if ((self.LA(1) >= u'0' and self.LA(1) <= u'9')):
                                        pass
                                        self.mDIGIT(False)
                                    else:
                                        break
                                    
                                    _cnt795 += 1
                                if _cnt795 < 1:
                                    self.raise_NoViableAlt(self.LA(1))
                            else:
                                break
                            
                        if (self.LA(1)==u'e'):
                            pass
                            self.mEXPONENT(False)
                        else: ## <m4>
                                pass
                            
                    else: ## <m4>
                            pass
                            if (self.LA(1)==u'e'):
                                pass
                                self.mINT_EXPONENT(False)
                            else: ## <m4>
                                    pass
                                
                        
                
        
        except antlr.RecognitionException, ex:
            self.reportError(ex);
            self.consume();
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mDIGIT(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = DIGIT
        _saveIndex = 0
        try:      ## for error handling
            pass
            pass
            self.matchRange(u'0', u'9')
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_4)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mBASED_INTEGER(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = BASED_INTEGER
        _saveIndex = 0
        try:      ## for error handling
            pass
            pass
            self.mEXTENDED_DIGIT(False)
            while True:
                if (_tokenSet_5.member(self.LA(1))):
                    pass
                    la1 = self.LA(1)
                    if False:
                        pass
                    elif la1 and la1 in u'_':
                        pass
                        self.match('_')
                    elif la1 and la1 in u'0123456789abcdef':
                        pass
                    else:
                            self.raise_NoViableAlt(self.LA(1))
                        
                    self.mEXTENDED_DIGIT(False)
                else:
                    break
                
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_6)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mINT_EXPONENT(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = INT_EXPONENT
        _saveIndex = 0
        try:      ## for error handling
            pass
            pass
            self.match('e')
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in u'+':
                pass
                self.match('+')
            elif la1 and la1 in u'0123456789':
                pass
            else:
                    self.raise_NoViableAlt(self.LA(1))
                
            _cnt810= 0
            while True:
                if ((self.LA(1) >= u'0' and self.LA(1) <= u'9')):
                    pass
                    self.mDIGIT(False)
                else:
                    break
                
                _cnt810 += 1
            if _cnt810 < 1:
                self.raise_NoViableAlt(self.LA(1))
        
        except antlr.RecognitionException, ex:
            self.reportError(ex);
            self.consume();
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mEXPONENT(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = EXPONENT
        _saveIndex = 0
        try:      ## for error handling
            pass
            pass
            self.match('e')
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in u'+':
                pass
                self.match('+')
            elif la1 and la1 in u'-':
                pass
                self.match('-')
            elif la1 and la1 in u'0123456789':
                pass
            else:
                    self.raise_NoViableAlt(self.LA(1))
                
            _cnt805= 0
            while True:
                if ((self.LA(1) >= u'0' and self.LA(1) <= u'9')):
                    pass
                    self.mDIGIT(False)
                else:
                    break
                
                _cnt805 += 1
            if _cnt805 < 1:
                self.raise_NoViableAlt(self.LA(1))
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mEXTENDED_DIGIT(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = EXTENDED_DIGIT
        _saveIndex = 0
        try:      ## for error handling
            pass
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in u'0123456789':
                pass
                self.mDIGIT(False)
            elif la1 and la1 in u'abcdef':
                pass
                self.matchRange(u'a', u'f')
            else:
                    self.raise_NoViableAlt(self.LA(1))
                
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_7)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mBASE(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = BASE
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.mDIGIT(False)
            if ((self.LA(1) >= u'0' and self.LA(1) <= u'9')):
                pass
                self.mDIGIT(False)
            else: ## <m4>
                    pass
                
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mHEX_DIGIT(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = HEX_DIGIT
        _saveIndex = 0
        try:      ## for error handling
            pass
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in u'0123456789':
                pass
                self.matchRange(u'0', u'9')
            elif la1 and la1 in u'abcdef':
                pass
                self.matchRange(u'a', u'f')
            else:
                    self.raise_NoViableAlt(self.LA(1))
                
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_3)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mWS(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = WS
        _saveIndex = 0
        try:      ## for error handling
            pass
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in u' ':
                pass
                self.match(' ')
            elif la1 and la1 in u'\n':
                pass
                self.match('\n')
                self.newline();
            elif la1 and la1 in u'\t':
                pass
                self.match('\t')
                self.tab();
            else:
                if (self.LA(1)==u'\r') and (self.LA(2)==u'\n'):
                    pass
                    self.match('\r')
                    self.match('\n')
                    self.newline();
                elif (self.LA(1)==u'\r') and (True):
                    pass
                    self.match('\r')
                    self.newline();
                else:
                    self.raise_NoViableAlt(self.LA(1))
                
            _ttype = Token.SKIP;
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mANNEX_TEXT(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = ANNEX_TEXT
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match("{**")
            while True:
                if ((self.LA(1)==u'*') and ((self.LA(2) >= u'\u0000' and self.LA(2) <= u'\ufffe')) and ((self.LA(3) >= u'\u0000' and self.LA(3) <= u'\ufffe')) and ( LA(2)!='*' or LA(3) != '}' )):
                    pass
                    self.match('*')
                elif (self.LA(1)==u'\r') and (self.LA(2)==u'\n') and ((self.LA(3) >= u'\u0000' and self.LA(3) <= u'\ufffe')):
                    pass
                    self.match('\r')
                    self.match('\n')
                    newline();
                elif (self.LA(1)==u'\r') and ((self.LA(2) >= u'\u0000' and self.LA(2) <= u'\ufffe')) and ((self.LA(3) >= u'\u0000' and self.LA(3) <= u'\ufffe')):
                    pass
                    self.match('\r')
                    newline();
                elif (self.LA(1)==u'\n'):
                    pass
                    self.match('\n')
                    newline();
                elif (_tokenSet_8.member(self.LA(1))):
                    pass
                    self.match(_tokenSet_8)
                else:
                    break
                
            self.match("**}")
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    def mSL_COMMENT(self, _createToken):    
        _ttype = 0
        _token = None
        _begin = self.text.length()
        _ttype = SL_COMMENT
        _saveIndex = 0
        try:      ## for error handling
            pass
            self.match("--")
            while True:
                if (_tokenSet_9.member(self.LA(1))):
                    pass
                    self.match(_tokenSet_9)
                else:
                    break
                
            _ttype = Token.SKIP;
        
        except antlr.RecognitionException, ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)
        
        self.set_return_token(_createToken, _token, _ttype, _begin)
    
    

### generate bit set
def mk_tokenSet_0(): 
    data = [0L] * 1025 ### init list
    return data
_tokenSet_0 = antlr.BitSet(mk_tokenSet_0())

### generate bit set
def mk_tokenSet_1(): 
    data = [0L] * 1025 ### init list
    data[0] =287948901175001088L
    data[1] =576460745860972544L
    return data
_tokenSet_1 = antlr.BitSet(mk_tokenSet_1())

### generate bit set
def mk_tokenSet_2(): 
    data = [0L] * 2048 ### init list
    data[0] =-17179869185L
    data[1] =-268435457L
    for x in xrange(2, 1023):
        data[x] = -1L
    data[1023] =9223372036854775807L
    return data
_tokenSet_2 = antlr.BitSet(mk_tokenSet_2())

### generate bit set
def mk_tokenSet_3(): 
    data = [0L] * 2048 ### init list
    for x in xrange(0, 1023):
        data[x] = -1L
    data[1023] =9223372036854775807L
    return data
_tokenSet_3 = antlr.BitSet(mk_tokenSet_3())

### generate bit set
def mk_tokenSet_4(): 
    data = [0L] * 1025 ### init list
    data[0] =288019304278917120L
    data[1] =543313362944L
    return data
_tokenSet_4 = antlr.BitSet(mk_tokenSet_4())

### generate bit set
def mk_tokenSet_5(): 
    data = [0L] * 1025 ### init list
    data[0] =287948901175001088L
    data[1] =543313362944L
    return data
_tokenSet_5 = antlr.BitSet(mk_tokenSet_5())

### generate bit set
def mk_tokenSet_6(): 
    data = [0L] * 1025 ### init list
    data[0] =34359738368L
    return data
_tokenSet_6 = antlr.BitSet(mk_tokenSet_6())

### generate bit set
def mk_tokenSet_7(): 
    data = [0L] * 1025 ### init list
    data[0] =287948935534739456L
    data[1] =543313362944L
    return data
_tokenSet_7 = antlr.BitSet(mk_tokenSet_7())

### generate bit set
def mk_tokenSet_8(): 
    data = [0L] * 2048 ### init list
    data[0] =-4398046520321L
    for x in xrange(1, 1023):
        data[x] = -1L
    data[1023] =9223372036854775807L
    return data
_tokenSet_8 = antlr.BitSet(mk_tokenSet_8())

### generate bit set
def mk_tokenSet_9(): 
    data = [0L] * 2048 ### init list
    data[0] =-9217L
    for x in xrange(1, 1023):
        data[x] = -1L
    data[1023] =9223372036854775807L
    return data
_tokenSet_9 = antlr.BitSet(mk_tokenSet_9())
    
### __main__ header action >>> 
if __name__ == '__main__' :
    import sys
    import antlr
    import AadlLexer
    
    ### create lexer - shall read from stdin
    try:
        for token in AadlLexer.Lexer():
            print token
            
    except antlr.TokenStreamException, e:
        print "error: exception caught while lexing: ", e
### __main__ header action <<< 
