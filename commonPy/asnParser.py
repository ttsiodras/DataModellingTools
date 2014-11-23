#!/usr/bin/env python
#
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
'''
ASN.1 Parser

This module parses ASN.1 grammars and creates an abstract syntax tree (AST)
inside configMT.inputCodeAST, for use with the code generators.
'''
import os
import sys
import copy
import tempfile
import re

import configMT
import utility

from asnAST import *
import xmlASTtoAsnAST


g_asnFilename = ""

g_filename = ''
g_inputAsnAST = []
g_leafTypeDict = {}
g_names = {}
g_metatypes = {}

g_typesOfFile = {}
g_astOfFile = {}

g_symbolicConstants = {}

g_checkedSoFarForKeywords = {}

g_invalidKeywords = [
    "active", "adding", "all", "alternative", "and", "any", "as", "atleast", "axioms", "block", "call", "channel", "comment", "connect", "connection", "constant", "constants", "create", "dcl", "decision", "default", "else", "endalternative", "endblock", "endchannel", "endconnection", "enddecision", "endgenerator", "endmacro", "endnewtype", "endoperator", "endpackage", "endprocedure", "endprocess", "endrefinement", "endselect", "endservice", "endstate", "endsubstructure", "endsyntype", "endsystem", "env", "error", "export", "exported", "external", "fi", "finalized", "for", "fpar", "from", "gate", "generator", "if", "import", "imported", "in", "inherits", "input", "interface", "join", "literal", "literals", "macro", "macrodefinition", "macroid", "map", "mod", "nameclass", "newtype", "nextstate", "nodelay", "noequality", "none", "not", "now", "offspring", "operator", "operators", "or", "ordering", "out", "output", "package", "parent", "priority", "procedure", "process", "provided", "redefined", "referenced", "refinement", "rem", "remote", "reset", "return", "returns", "revealed", "reverse", "save", "select", "self", "sender", "service", "set", "signal", "signallist", "signalroute", "signalset", "spelling", "start", "state", "stop", "struct", "substructure", "synonym", "syntype", "system", "task", "then", "this", "timer", "to", "type", "use", "via", "view", "viewed", "virtual", "with", "xor", "end", "i", "j", "auto", "const",
    # From Nicolas Gillet/Astrium for SCADE
    "abstract", "activate", "and", "assume", "automaton", "bool", "case", "char", "clock", "const", "default", "div", "do", "else", "elsif", "emit", "end", "enum", "every", "false", "fby", "final", "flatten", "fold", "foldi", "foldw", "foldwi", "function", "guarantee", "group", "if", "imported", "initial", "int", "is", "last", "let", "make", "map", "mapfold", "mapi", "mapw", "mapwi", "match", "merge", "mod", "node", "not", "numeric", "of", "onreset", "open", "or", "package", "parameter", "pre", "private", "probe", "public", "real", "restart", "resume", "returns", "reverse", "sensor", "sig", "specialize", "state", "synchro", "tel", "then", "times", "transpose", "true", "type", "unless", "until", "var", "when", "where", "with", "xor",
    # From Maxime - ESA GNC Team
    "open", "close", "flag"
]

tokens = (
    'DEFINITIONS',
    'APPLICATION',
    'AUTOMATIC',
    'IMPLICIT',
    'EXPLICIT',
    'TAGS',
    'BEGIN',
    'IMPORTS',
    'EXPORTS',
    'FROM',
    'ALL',
    'CHOICE',
    'SEQUENCE',
    'SET',
    'OF',
    'END',
    'OPTIONAL',
    'INTEGER',
    'REAL',
    'OCTET',
    #    'BIT',
    'STRING',
    'BOOLEAN',
    'TRUE',
    'FALSE',
    'ASCIISTRING',
    'NUMBERSTRING',
    'VISIBLESTRING',
    'PRINTABLESTRING',
    'UTF8STRING',
    'ENUMERATED',
    'SEMI',
    'LPAREN',
    'RPAREN',
    'LBRACKET',
    'RBRACKET',
    'BLOCK_END',
    'BLOCK_BEGIN',
    'DEF',
    'NAME',
    'COMMA',
    'INTVALUE',
    'REALVALUE',
    'DEFAULT',
    'SIZE',
    'DOTDOT',
    'DOTDOTDOT',
    'WITH',
    'COMPONENTS',
    'MANTISSA',
    'BASE',
    'EXPONENT'
)

lotokens = [tkn.lower() for tkn in tokens]


def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")/2
    #print "New line, met ", t.value.count("\n"), "newlines, so now at line", t.lineno


t_DEFINITIONS =   r'DEFINITIONS'
t_APPLICATION =   r'APPLICATION'
t_TAGS =          r'TAGS'
t_BEGIN =         r'BEGIN'
t_EXPORTS =       r'EXPORTS'
t_IMPORTS =       r'IMPORTS'
t_ALL =           r'ALL'
t_FROM =          r'FROM'
t_CHOICE =        r'CHOICE'
t_SEQUENCE =      r'SEQUENCE'
t_SET =           r'SET'
t_OF =            r'OF'
t_END =           r'END'
t_OPTIONAL =      r'OPTIONAL'
t_BOOLEAN =       r'BOOLEAN'
t_INTEGER =       r'INTEGER'
t_REAL =          r'REAL'
t_OCTET =         r'OCTET'
#t_BIT =           r'BIT'
t_STRING =        r'STRING'
t_UTF8STRING =    r'UTF8String'
t_ASCIISTRING =   r'AsciiString'
t_NUMBERSTRING =  r'NumberString'
t_VISIBLESTRING = r'VisibleString'
t_PRINTABLESTRING = r'PrintableString'
t_ENUMERATED =    r'ENUMERATED'
t_AUTOMATIC =     r'AUTOMATIC'
t_IMPLICIT =      r'IMPLICIT'
t_SIZE =          r'SIZE'
t_TRUE =          r'TRUE'
t_FALSE =         r'FALSE'
t_DEFAULT =       r'DEFAULT'
t_WITH =          r'WITH'
t_COMPONENTS =    r'COMPONENTS'
t_MANTISSA =      r'mantissa'
t_BASE =          r'base'
t_EXPONENT =      r'exponent'

t_LPAREN      = r'\('
t_RPAREN      = r'\)'
t_LBRACKET    = r'\['
t_RBRACKET    = r'\]'
t_BLOCK_BEGIN = r'\{'
t_BLOCK_END   = r'\}'
t_DEF         = r'::='
t_COMMA       = r','
t_SEMI        = r';'
t_DOTDOT      = r'\.\.'
t_DOTDOTDOT   = r'\.\.\.'

# Parsing rules

#    'BIT': 'BIT',
reserved = {
    'DEFINITIONS': 'DEFINITIONS',
    'APPLICATION': 'APPLICATION',
    'TAGS': 'TAGS',
    'BEGIN': 'BEGIN',
    'CHOICE': 'CHOICE',
    'SEQUENCE': 'SEQUENCE',
    'SET': 'SET',
    'OF': 'OF',
    'END': 'END',
    'OPTIONAL': 'OPTIONAL',
    'BOOLEAN': 'BOOLEAN',
    'INTEGER': 'INTEGER',
    'REAL': 'REAL',
    'OCTET': 'OCTET',
    'STRING': 'STRING',
    'UTF8String': 'UTF8STRING',
    'AsciiString': 'ASCIISTRING',
    'NumberString': 'NUMBERSTRING',
    'VisibleString': 'VISIBLESTRING',
    'PrintableString': 'PRINTABLESTRING',
    'ENUMERATED': 'ENUMERATED',
    'AUTOMATIC': 'AUTOMATIC',
    'IMPLICIT': 'IMPLICIT',
    'EXPLICIT': 'EXPLICIT',
    'SIZE': 'SIZE',
    'TRUE': 'TRUE',
    'FALSE': 'FALSE',
    'DEFAULT': 'DEFAULT',
    'mantissa': 'MANTISSA',
    'base': 'BASE',
    'exponent': 'EXPONENT',
    'WITH': 'WITH',
    'FROM': 'FROM',
    'IMPORTS': 'IMPORTS',
    'EXPORTS': 'EXPORTS',
    'ALL': 'ALL',
    'COMPONENTS': 'COMPONENTS'
}


def t_NAME(t):
    r'[a-zA-Z_][a-zA-Z0-9_\-]*'
    t.type = reserved.get(t.value, 'NAME')
    return t


def t_REALVALUE(t):
    r'[+-]?[0-9]+\.[0-9]+'
    t.type = 'REALVALUE'
    return t


def t_INTVALUE(t):
    r'[+-]?[0-9]+'
    t.type = 'INTVALUE'
    return t

t_ignore = " \t"


def t_comment(t):
    r'--.*'
    pass


# C or C++ comment (ignore)
def t_ccode_comment(t):
    r'(/\*(.|\n)*?\*/)|(//.*)'
    t.lexer.lineno += t.value.count("\n")/2


def t_error(t):
    sys.stderr.write("Illegal character '%s'\n" % t.value[0])
    t.skip(1)


def p_file(p):
    '''file : NAME definitiveObjs DEFINITIONS AUTOMATIC TAGS DEF BEGIN exportsList importsList typeAssignments END
            | NAME definitiveObjs DEFINITIONS IMPLICIT  TAGS DEF BEGIN exportsList importsList typeAssignments END
            | NAME definitiveObjs DEFINITIONS EXPLICIT  TAGS DEF BEGIN exportsList importsList typeAssignments END'''
    g_inputAsnAST[:] = p[10]
    g_astOfFile[g_filename] = copy.copy(p[10])
    #g_leafTypeDict.clear()
    #g_leafTypeDict.update( VerifyAndFixAST() )


def p_file2(p):
    '''file : NAME definitiveObjs DEFINITIONS DEF BEGIN exportsList importsList typeAssignments END'''
    global g_inputAsnAST
    g_inputAsnAST = p[8]
    g_astOfFile[g_filename] = copy.copy(p[8])
    #g_leafTypeDict.clear()
    #g_leafTypeDict.update( VerifyAndFixAST() )


def p_exports(p):
    '''exportsList :
                   | EXPORTS ALL SEMI
                   | EXPORTS NAME typeList SEMI'''
    pass


def p_typeList(p):
    '''typeList :
                | COMMA NAME typeList'''
    pass


def p_imports(p):
    '''importsList :
                   | IMPORTS NAME typeList FROM NAME definitiveObjs importedTypes SEMI'''
    pass


def p_importedTypes(p):
    '''importedTypes :
                     | NAME typeList FROM NAME definitiveObjs importedTypes'''
    pass


def p_definitiveObjs(p):
    '''definitiveObjs :
                      | BLOCK_BEGIN definitiveObjIds BLOCK_END '''
    pass


def p_definitiveObjIds(p):
    '''definitiveObjIds :
                        | definitiveObjId definitiveObjIds'''
    pass


def p_definitiveObjId(p):
    '''definitiveObjId : NAME
                       | NAME LPAREN INTVALUE RPAREN
                       | INTVALUE'''
    pass


def p_typeAssignments(p):
    '''typeAssignments :
                       | typeAssignment typeAssignments'''
    if len(p) == 1:
        p[0] = []
    else:
        if p[1] is not None:
            temp = [p[1]]
        else:
            temp = []
        temp.extend(p[2])
        p[0] = temp


def p_typeAssignment1(p):
    '''typeAssignment : NAME DEF optionalApp typeBody'''
    if p[1] in g_names:
        utility.panic("'%s' defined more than once! (met again at (%s,%s))!\n" % (p[1], g_filename, p.lineno(1)))
    g_names[p[1]] = p[4]
    g_typesOfFile.setdefault(g_filename, [])
    g_typesOfFile[g_filename].append(p[1])
    p[0] = p[1]


def p_typeAssignment2(p):
    '''typeAssignment : ASCIISTRING DEF OCTET STRING
                      | NUMBERSTRING DEF OCTET STRING
                      | VISIBLESTRING DEF OCTET STRING
                      | PRINTABLESTRING DEF OCTET STRING'''
    g_names[p[1]] = AsnOctetString(asnFilename=g_asnFilename)
    g_typesOfFile.setdefault(g_filename, [])
    g_typesOfFile[g_filename].append(p[1])
    p[0] = p[1]


def p_typeAssignment3(p):
    '''typeAssignment : NAME INTEGER DEF INTVALUE'''
    try:
        g_symbolicConstants[p[1]] = long(p[4])
    except:
        utility.panic("Symbolic constants can only contain INTEGER value (not '%s') (%s,%s)!\n" % (p[4], g_filename, p.lineno(1)))


def p_optionalApp(p):
    '''optionalApp :
                   | LBRACKET INTVALUE RBRACKET
                   | LBRACKET APPLICATION INTVALUE RBRACKET'''
    pass


def p_typeBody1(p):
    '''typeBody : simpleType
                | complexType'''
    p[0] = p[1]


def p_typeBody2(p):
    '''typeBody : NAME'''
    p[0] = AsnMetaType(asnFilename=g_asnFilename, containedType=p[1])


def p_simpleType(p):
    '''simpleType : booleanType
                  | integerType
                  | realType
                  | stringType'''
    p[0] = p[1]


def p_booleanType(p):
    '''booleanType : BOOLEAN
                   | BOOLEAN DEFAULT boolValue'''
    if len(p)==2:
        p[0] = AsnBool(asnFilename=g_asnFilename, lineno=p.lineno(1))
    else:
        p[0] = AsnBool(asnFilename=g_asnFilename, bDefaultValue=p[3], lineno=p.lineno(1))


def p_boolValue(p):
    '''boolValue : TRUE
                 | FALSE'''
    p[0] = p[1]


def p_integerType(p):
    '''integerType : INTEGER intRange
                   | INTEGER intRange DEFAULT INTVALUE'''
    if len(p)==3:
        p[0] = AsnInt(asnFilename=g_asnFilename, lineno=p.lineno(1), range=p[2])
    else:
        p[0] = AsnInt(asnFilename=g_asnFilename, lineno=p.lineno(1), range=p[2], iDefaultValue=p[4])


def p_intRange(p):
    '''intRange :
                | LPAREN INTVALUE DOTDOT INTVALUE RPAREN'''
    if len(p) == 1:
        p[0] = []
    else:
        p[0] = [long(p[2]), long(p[4])]


def p_realType(p):
    '''realType : REAL optionalRealConstraint
                | REAL optionalRealConstraint DEFAULT REALVALUE'''
    if len(p)==3:
        p[2].update({'lineno': p.lineno(1)})
        p[2].update({'asnFilename': g_asnFilename})
        p[0] = AsnReal(**p[2])
    else:
        p[2].update({'defaultValue': p[4]})
        p[2].update({'lineno': p.lineno(1)})
        p[2].update({'asnFilename': g_asnFilename})
        p[0] = AsnReal(**p[2])


def p_optionalRealConstraint(p):
    '''optionalRealConstraint :
                              | LPAREN INTVALUE DOTDOT INTVALUE RPAREN
                              | LPAREN INTVALUE DOTDOT REALVALUE RPAREN
                              | LPAREN REALVALUE DOTDOT REALVALUE RPAREN
                              | LPAREN WITH COMPONENTS BLOCK_BEGIN realConstraint otherRealConstraints BLOCK_END RPAREN'''
    if len(p)==1:
        p[0] = {}
    elif len(p)==6:
        temp = {'range': [float(p[2]), float(p[4])]}
        p[0] = temp
    else:
        temp = p[5]
        temp.update(p[6])
        p[0] = temp


def p_otherRealConstraints(p):
    '''otherRealConstraints :
                            | COMMA realConstraint otherRealConstraints'''
    if len(p)==1:
        p[0] = {}
    else:
        temp = p[2]
        temp.update(p[3])
        p[0] = temp


def p_realConstraint(p):
    '''realConstraint : MANTISSA rangeSpec
                      | BASE rangeSpec
                      | EXPONENT rangeSpec'''
    p[0] = {p[1]: p[2]}


def p_stringType1(p):
    '''stringType : UTF8STRING optionalLengthConstraint'''
    p[0] = AsnUTF8String(asnFilename=g_asnFilename, lineno=p.lineno(1), range=p[2])


def p_stringType2(p):
    '''stringType : OCTET STRING optionalLengthConstraint'''
    p[0] = AsnOctetString(asnFilename=g_asnFilename, lineno=p.lineno(1), range=p[3])


def p_stringType3(p):
    '''stringType : ASCIISTRING optionalLengthConstraint'''
    p[0] = AsnAsciiString(asnFilename=g_asnFilename, lineno=p.lineno(1), range=p[2])


def p_stringType4(p):
    '''stringType : NUMBERSTRING optionalLengthConstraint'''
    p[0] = AsnNumberString(asnFilename=g_asnFilename, lineno=p.lineno(1), range=p[2])


def p_stringType5(p):
    '''stringType : VISIBLESTRING optionalLengthConstraint'''
    p[0] = AsnVisibleString(asnFilename=g_asnFilename, lineno=p.lineno(1), range=p[2])


def p_stringType6(p):
    '''stringType : PRINTABLESTRING optionalLengthConstraint'''
    p[0] = AsnPrintableString(asnFilename=g_asnFilename, lineno=p.lineno(1), range=p[2])

#def p_stringType7(p):
#    '''stringType : BIT STRING optionalLengthConstraint'''
#    p[0] = AsnBitString( lineno=p.lineno(1), range=p[2])


def p_optionalLengthConstraint(p):
    '''optionalLengthConstraint :
                                | LPAREN SIZE rangeSpec RPAREN'''
    if len(p)==1:
        p[0] = []
    else:
        p[0] = p[3]


def p_rangeSpec(p):
    '''rangeSpec : LPAREN INTVALUE RPAREN
                 | LPAREN INTVALUE DOTDOT INTVALUE RPAREN'''
    if len(p)==4:
        p[0] = [long(p[2])]
    else:
        p[0] = [long(p[2]), long(p[4])]


def p_rangeSpecSymbol(p):
    '''rangeSpec : LPAREN NAME RPAREN'''
    if p[2] not in g_symbolicConstants:
        utility.panic("Symbolic constant '%s' not defined here (%s)!\n" % (p[2], p.lineno(1)))
    p[0] = [long(g_symbolicConstants[p[2]])]


def p_rangeSpecSymbol1(p):
    '''rangeSpec : LPAREN NAME DOTDOT INTVALUE RPAREN'''
    if p[2] not in g_symbolicConstants:
        utility.panic("Symbolic constant '%s' not defined here (%s)!\n" % (p[2], p.lineno(1)))
    p[0] = [long(g_symbolicConstants[p[2]]), long(p[4])]


def p_rangeSpecSymbol2(p):
    '''rangeSpec : LPAREN INTVALUE DOTDOT NAME RPAREN'''
    if p[4] not in g_symbolicConstants:
        utility.panic("Symbolic constant '%s' not defined here (%s)!\n" % (p[4], p.lineno(1)))
    p[0] = [long(p[2]), long(g_symbolicConstants[p[4]])]


def p_rangeSpecSymbol3(p):
    '''rangeSpec : LPAREN NAME DOTDOT NAME RPAREN'''
    if p[2] not in g_symbolicConstants:
        utility.panic("Symbolic constant '%s' not defined here (%s)!\n" % (p[2], p.lineno(1)))
    if p[4] not in g_symbolicConstants:
        utility.panic("Symbolic constant '%s' not defined here (%s)!\n" % (p[4], p.lineno(1)))
    p[0] = [long(g_symbolicConstants[p[2]]), long(g_symbolicConstants[p[4]])]


def p_complexType(p):
    '''complexType : sequenceType
                   | sequenceOfType
                   | setType
                   | setOfType
                   | choiceType
                   | enumeratedType'''
    p[0] = p[1]


def p_enumeratedType(p):
    '''enumeratedType : ENUMERATED BLOCK_BEGIN enumMember optionalOtherEnumMembers BLOCK_END optionalDefaultEnum'''
    temp = [p[3]]
    temp.extend(p[4])
    p[0] = AsnEnumerated(asnFilename=g_asnFilename, members=temp, default=p[6], lineno=p.lineno(1))


def p_enumMembers(p):
    '''optionalOtherEnumMembers :
                                | COMMA enumMember optionalOtherEnumMembers'''
    if len(p)==1:
        p[0] = []
    else:
        if p[2] != []:
            temp = [p[2]]
        else:
            temp = []
        temp.extend(p[3])
        p[0] = temp


def p_enumMember(p):
    '''enumMember : NAME optionalNumber'''
    p[0] = [p[1], p[2]]


def p_enumMember2(p):
    '''enumMember : DOTDOTDOT'''
    p[0] = []


def p_optionalNumber(p):
    '''optionalNumber :
                      | LPAREN INTVALUE RPAREN'''
    if len(p)==1:
        p[0] = None
    else:
        p[0] = p[2]


def p_optionalDefaultEnum(p):
    '''optionalDefaultEnum :
                           | DEFAULT NAME'''
    if len(p)==1:
        p[0] = None
    else:
        p[0] = p[2]


def p_sequenceType(p):
    '''sequenceType : SEQUENCE BLOCK_BEGIN member otherMembers BLOCK_END'''
    temp = [p[3]]
    temp.extend(p[4])
    values = [x for x in temp if x is not None and x != []]
    p[0] = AsnSequence(asnFilename=g_asnFilename, members=values, lineno=p.lineno(1))


def p_setType(p):
    '''setType : SET BLOCK_BEGIN member otherMembers BLOCK_END'''
    temp = [p[3]]
    temp.extend(p[4])
    values = [x for x in temp if x is not None and x != []]
    p[0] = AsnSet(asnFilename=g_asnFilename, members=values, lineno=p.lineno(1))


def p_sequenceOfType(p):
    '''sequenceOfType : SEQUENCE OF NAME
                      | SEQUENCE SIZE rangeSpec OF NAME
                      | SEQUENCE LPAREN SIZE rangeSpec RPAREN OF NAME '''
    if len(p)==4:
        p[0] = AsnSequenceOf(asnFilename=g_asnFilename, containedType=p[3], lineno=p.lineno(1))
    elif len(p)==6:
        p[0] = AsnSequenceOf(asnFilename=g_asnFilename, containedType=p[5], range=p[3], lineno=p.lineno(1))
    else:
        p[0] = AsnSequenceOf(asnFilename=g_asnFilename, containedType=p[7], range=p[4], lineno=p.lineno(1))


def p_sequenceOfType2(p):
    '''sequenceOfType : SEQUENCE OF simpleType
                      | SEQUENCE SIZE rangeSpec OF simpleType
                      | SEQUENCE LPAREN SIZE rangeSpec RPAREN OF simpleType
                      | SEQUENCE SIZE rangeSpec OF complexType
                      | SEQUENCE LPAREN SIZE rangeSpec RPAREN OF complexType'''
    if len(p)==4:
        p[0] = AsnSequenceOf(asnFilename=g_asnFilename, containedType=p[3], lineno=p.lineno(1))
    elif len(p) == 6:
        p[0] = AsnSequenceOf(asnFilename=g_asnFilename, containedType=p[5], range=p[3], lineno=p.lineno(1))
    else:
        p[0] = AsnSequenceOf(asnFilename=g_asnFilename, containedType=p[7], range=p[4], lineno=p.lineno(1))


def p_setOfType(p):
    '''setOfType : SET OF NAME
                 | SET SIZE rangeSpec OF NAME
                 | SET LPAREN SIZE rangeSpec RPAREN OF NAME '''
    if len(p)==4:
        p[0] = AsnSetOf(asnFilename=g_asnFilename, containedType=p[3], lineno=p.lineno(1))
    elif len(p)==6:
        p[0] = AsnSetOf(asnFilename=g_asnFilename, containedType=p[5], range=p[3], lineno=p.lineno(1))
    else:
        p[0] = AsnSetOf(asnFilename=g_asnFilename, containedType=p[7], range=p[4], lineno=p.lineno(1))


def p_setOfType2(p):
    '''setOfType : SET OF simpleType
                 | SET SIZE rangeSpec OF simpleType
                 | SET LPAREN SIZE rangeSpec RPAREN OF simpleType
                 | SET SIZE rangeSpec OF complexType
                 | SET LPAREN SIZE rangeSpec RPAREN OF complexType'''
    if len(p)==4:
        p[0] = AsnSetOf(asnFilename=g_asnFilename, containedType=p[3], lineno=p.lineno(1))
    elif len(p) == 6:
        p[0] = AsnSetOf(asnFilename=g_asnFilename, containedType=p[5], range=p[3], lineno=p.lineno(1))
    else:
        p[0] = AsnSetOf(asnFilename=g_asnFilename, containedType=p[7], range=p[4], lineno=p.lineno(1))


def p_choiceType(p):
    '''choiceType : CHOICE BLOCK_BEGIN member otherMembers BLOCK_END'''
    if p[3] == []:
        temp = []
    else:
        temp = [p[3]]
    temp.extend(p[4])
    while None in temp:
        temp.remove(None)
    p[0] = AsnChoice(asnFilename=g_asnFilename, members=temp, lineno=p.lineno(1))


def p_otherMembers(p):
    '''otherMembers :
                    | COMMA member otherMembers'''
    if len(p) == 1:
        p[0] = []
    else:
        if p[2] == []:
            temp = []
        else:
            temp = [p[2]]
        temp.extend(p[3])
        p[0] = temp


def p_member1(p):
    '''member : NAME simpleType optionality
              | NAME complexType optionality'''
    temp = [p[1]]
    if len(p)>3 and p[3]:
        p[2]._isOptional = True
    temp.append(p[2])
    p[0] = temp


def p_member2(p):
    '''member : NAME NAME optionality'''
    if p[2] == 'NULL':
        utility.panic("NULL types are not supported (yet) (%s,%s))!\n" % (g_filename, p.lineno(1)))
    else:
        temp = [p[1]]
        mmbr = AsnMetaMember(asnFilename=g_asnFilename, containedType=p[2], lineno=p.lineno(1))
        if len(p)>3 and p[3]:
            mmbr._isOptional = True
        temp.append(mmbr)
        p[0] = temp


def p_member3(p):
    '''member : DOTDOTDOT'''
    pass


def p_optionality(p):
    '''optionality :
                   | OPTIONAL'''
    if len(p) == 1:
        p[0] = False
    else:
        p[0] = True


def p_error(p):
    utility.panic("'%s': AsnParser: Syntax error at '%s', near line %d\n" % (g_filename, p.value, p.lineno))


def KnownType(node, names):
    if isinstance(node, str):
        utility.panic("Referenced type (%s) does not exist!\n" % node)
    if isinstance(node, AsnBasicNode):
        return True
    elif isinstance(node, AsnEnumerated):
        return True
    elif isinstance(node, AsnSequence) or isinstance(node, AsnChoice) or isinstance(node, AsnSet):
        for x in node._members:
            if not KnownType(x[1], names):
                return False
        return True
    elif isinstance(node, AsnMetaMember):
        return KnownType(names.get(node._containedType, node._containedType), names)
    elif isinstance(node, AsnSequenceOf) or isinstance(node, AsnSetOf):
        if isinstance(node._containedType, str):
            return KnownType(names.get(node._containedType, node._containedType), names)
        else:
            return KnownType(node._containedType, names)
    elif isinstance(node, AsnMetaType):
        return KnownType(names.get(node._containedType, node._containedType), names)
    else:
        return utility.panic("Unknown node type (%s)!\n" % str(node))


def CleanNameForAST(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


def VerifyAndFixAST():
    '''\
Check that all types are defined and not missing.
It returns a map providing the leafType of each type.
'''
    unknownTypes = {}
    knownTypes = {}
    equivalents = {}
    while True:
        lastUnknownTypes = copy.copy(unknownTypes)
        lastKnownTypes = copy.copy(knownTypes)
        lastEquivalents = copy.copy(equivalents)
        for nodeTypename in g_names.keys():

            node = g_names[nodeTypename]

            # AsnMetaMembers can only appear inside SEQUENCEs and CHOICEs,
            # not at the top level!
            assert (not isinstance(node, AsnMetaMember))

            #print node
            #print "Knowntypes:"
            #print knownTypes
            #print

            # Type level typedefs are stored in the equivalents dictionary
            if isinstance(node, AsnMetaType):
                # A ::= B
                # A and B are nodeTypename  and  node._containedType
                equivalents.setdefault(node._containedType, [])
                # Add A to the list of types that are equivalent to B
                equivalents[node._containedType].append(nodeTypename)
                # and if we know B's leafType, then we also know A's
                if node._containedType in knownTypes:
                    knownTypes[nodeTypename]=node._containedType
                else:
                    unknownTypes[nodeTypename]=1
            # AsnBasicNode type assignments are also equivalents
            elif isinstance(node, AsnBasicNode):
                # node._leafType is one of BOOLEAN, OCTET STRING, INTEGER, etc
                equivalents.setdefault(node._leafType, [])
                equivalents[node._leafType].append(nodeTypename)
                knownTypes[nodeTypename]=node._leafType
            # AsnEnumerated types are known types - they don't have external refs
            elif isinstance(node, AsnEnumerated):
                # node._leafType is ENUMERATED
                knownTypes[nodeTypename]=node._leafType
            # SEQUENCEs and CHOICEs: check their children for unknown AsnMetaMembers
            elif isinstance(node, AsnSequence) or isinstance(node, AsnChoice) or isinstance(node, AsnSet):
                bFoundUnknown = False
                for x in node._members:
                    if isinstance(x[1], AsnMetaMember) and x[1]._containedType not in knownTypes:
                        bFoundUnknown = True
                        break
                if bFoundUnknown:
                    unknownTypes[nodeTypename]=1
                else:
                    # node._leafType is SEQUENCE or CHOICE
                    knownTypes[nodeTypename]=node._leafType
            # SEQUENCE OFs: check their contained type
            elif isinstance(node, AsnSequenceOf) or isinstance(node, AsnSetOf):
                if node._containedType in knownTypes or isinstance(node._containedType, AsnBasicNode):
                    knownTypes[nodeTypename]=node._leafType
                elif isinstance(node._containedType, AsnComplexNode):
                    knownTypes[nodeTypename]=node._leafType
                else:
                    unknownTypes[nodeTypename]=1

        # We have completed a sweep over all AST entries.
        # now check the knownTypes and unknownTypes information
        # to see if we have figured out (leafType wise) all nodes
        for known in knownTypes.keys():
            # for each of the nodes we know (leafType wise)

            # remove it from the unknownTypes dictionary
            if known in unknownTypes:
                del unknownTypes[known]

            # remove all it's equivalents, too (from the unknownTypes)
            if known in equivalents:
                for alsoKnown in equivalents[known]:
                    if alsoKnown in unknownTypes:
                        del unknownTypes[alsoKnown]

                    # Additionally, follow the chain to the last knownType
                    seed = known
                    while seed in knownTypes:
                        if seed!=knownTypes[seed]:
                            seed=knownTypes[seed]
                        else:
                            break
                    # and update knownTypes dictionary to contain leafType
                    knownTypes[alsoKnown]=seed

        # If this pass has not changed the knownTypes and the unknownTypes and the equivalents, we are done
        if lastEquivalents == equivalents and lastKnownTypes == knownTypes and lastUnknownTypes == unknownTypes:
            break

    if len(unknownTypes) != 0:
        utility.panic('AsnParser: Types remain unknown after symbol fixup:\n%s\n' % unknownTypes.keys())

    # Remove all AsnMetaTypes from the ast
    # by using the g_names lookup on their _containedType
    for nodeTypename in g_names.keys():
        # Min, Max: to cope with ReferenceTypes that redefine their
        # constraints (for now, ASN1SCC provides only INTEGERs)
        Min = Max = None
        node = g_names[nodeTypename]
        if hasattr(node, "_Min") and Min is None:
            Min = node._Min
        if hasattr(node, "_Max") and Max is None:
            Max = node._Max
        originalNode = node
        while isinstance(node, AsnMetaType):
            g_metatypes[nodeTypename] = node._containedType
            node = g_names[node._containedType]
            if hasattr(node, "_Min") and Min is None:
                Min = node._Min
            if hasattr(node, "_Max") and Max is None:
                Max = node._Max
        # To cope with ReferenceTypes that redefine their
        # constraints (for now, ASN1SCC provides only INTEGERs)
        if isinstance(originalNode, AsnMetaType):
            target = copy.copy(node)  # we need to keep the _asnFilename
            target._asnFilename = originalNode._asnFilename
        elif isinstance(node, AsnInt) and Min is not None and Max is not None:
            target = copy.copy(node)  # we need to keep the Min/Max
        else:
            target = node

        g_names[nodeTypename] = target
        if isinstance(node, AsnInt) and Min is not None and Max is not None:
            target._range = [Min, Max]

    for name, node in g_names.items():
        if not KnownType(node, g_names):
            utility.panic("Node %s not resolvable (%s)!\n" % (name, node.Location()))
        for i in ["_Min", "_Max"]:
            cast = float if isinstance(node, AsnReal) else long
            if hasattr(node, i) and getattr(node, i) is not None:
                setattr(node, i, cast(getattr(node, i)))

    knownTypes['INTEGER'] = 'INTEGER'
    knownTypes['REAL'] = 'REAL'
    knownTypes['BOOLEAN'] = 'BOOLEAN'
    knownTypes['OCTET STRING'] = 'OCTET STRING'
    knownTypes['AsciiString'] = 'OCTET STRING'
    knownTypes['NumberString'] = 'OCTET STRING'
    knownTypes['VisibleString'] = 'OCTET STRING'
    knownTypes['PrintableString'] = 'OCTET STRING'
    knownTypes['UTF8String'] = 'OCTET STRING'

    # Find all the SEQUENCE, CHOICE and SEQUENCE OFs
    # and if the contained type is not one of AsnBasicNode, AsnEnumerated, AsnMetaMember,
    # define a name and use it... (for SEQUENCEOFs/SETOFs, allow also 'str')
    internalNo = 1
    addedNewPseudoType = True
    while addedNewPseudoType:
        addedNewPseudoType = False
        listOfTypenames = sorted(g_names.keys())
        for nodeTypename in listOfTypenames:
            node = g_names[nodeTypename]
            if isinstance(node, AsnChoice) or isinstance(node, AsnSequence) or isinstance(node, AsnSet):
                for child in node._members:
                    if not isinstance(child[1], AsnBasicNode) and \
                            not isinstance(child[1], AsnEnumerated) and \
                            not isinstance(child[1], AsnMetaMember):
                        # It will be an internal sequence, choice or sequenceof
                        assert \
                            isinstance(child[1], AsnChoice) or \
                            isinstance(child[1], AsnSequence) or \
                            isinstance(child[1], AsnSet) or \
                            isinstance(child[1], AsnSetOf) or \
                            isinstance(child[1], AsnSequenceOf)
                        internalName = newname = nodeTypename + '_' + CleanNameForAST(child[0])
                        while internalName in g_names:
                            internalName = (newname + "_%d") % internalNo
                            internalNo += 1
                        g_names[internalName] = child[1]
                        child[1]._isArtificial = True
                        g_leafTypeDict[internalName] = child[1]._leafType
                        child[1] = AsnMetaMember(asnFilename=child[1]._asnFilename, containedType=internalName)
                        addedNewPseudoType = True
            elif isinstance(node, AsnSequenceOf) or isinstance(node, AsnSetOf):
                if not isinstance(node._containedType, str) and \
                        not isinstance(node._containedType, AsnBasicNode) and \
                        not isinstance(node._containedType, AsnEnumerated):
                    internalName = newname = nodeTypename + "_elm"
                    while internalName in g_names:
                        internalName = (newname + "_%d") % internalNo
                        internalNo += 1
                    g_names[internalName] = node._containedType
                    node._containedType._isArtificial = True
                    g_leafTypeDict[internalName] = node._containedType._leafType
                    node._containedType = internalName
                    addedNewPseudoType = True

    # return the leafType dictionary
    return knownTypes


def ParseInput(asnFilename, bClearFirst=True, bFixAST=True):
    global g_asnFilename
    g_asnFilename = asnFilename
    try:
        lines = "\n".join(open(asnFilename, 'r').readlines())
    except:
        utility.panic("AsnParser: Can't find file '%s'\n" % asnFilename)

    if bClearFirst:
        global g_names
        g_names = {}
        global g_typesOfFile
        g_typesOfFile = {}
        global g_inputAsnAST
        g_inputAsnAST = []
        global g_leafTypeDict
        g_leafTypeDict = {}

    if not configMT.debugParser:
        import lex
        lex.lex()

        import yacc
        yacc.yacc(debug=0, write_tables=0)
        yacc.parse(lines)
    else:
        import lex
        lexer = lex.lex(debug=1)
        lexer.input(lines)
        lex.runmain()

    if bFixAST:
        g_leafTypeDict.update(VerifyAndFixAST())


def IsInvalidType(name):
    return \
        (name.lower() in g_invalidKeywords) or \
        (name.lower() in lotokens) or \
        any([name.lower().endswith(x) for x in ["-buffer", "-buffer-max"]])


def CheckForInvalidKeywords(node):
    if isinstance(node, str):
        if IsInvalidType(node):
            utility.panic("TASTE disallows certain type names for various reasons.\n'%s' is not allowed" % node)
        node = g_names[node]

    if isinstance(node, AsnBasicNode) or isinstance(node, AsnEnumerated):
        pass
    elif isinstance(node, AsnSequence) or isinstance(node, AsnChoice) or isinstance(node, AsnSet):
        for child in node._members:
            if child[0].lower() in g_invalidKeywords or child[0].lower() in lotokens:
                utility.panic(
                    "TASTE disallows certain field names because they are used in various modelling tools.\n" +
                    "Invalid field name '%s' used in type defined in %s" % (child[0], node.Location()))
            if isinstance(child[1], AsnMetaMember) and child[1]._containedType not in g_checkedSoFarForKeywords:
                if IsInvalidType(child[1]._containedType.lower()):
                    utility.panic(
                        "TASTE disallows certain type names for various reasons.\n" +
                        "Invalid type name '%s' used in type defined in %s" % (child[1]._containedType, node.Location()))
                if child[1]._containedType not in g_checkedSoFarForKeywords:
                    g_checkedSoFarForKeywords[child[1]._containedType]=1
                    CheckForInvalidKeywords(g_names[child[1]._containedType])
            if isinstance(child[1], AsnMetaMember) and child[1]._containedType.lower() == child[0].lower():
                utility.panic(
                    "Ada mappers won't allow SEQUENCE/CHOICE fields with same names as their types.\n" +
                    "Fix declaration at %s" % node.Location())
    elif isinstance(node, AsnSequenceOf) or isinstance(node, AsnSetOf):
        if isinstance(node._containedType, str):
            if IsInvalidType(node._containedType):
                utility.panic(
                    "TASTE disallows certain type names for various reasons.\n" +
                    "Invalid type name '%s' used in type defined in %s" % (node._containedType, node.Location()))
            if node._containedType not in g_checkedSoFarForKeywords:
                g_checkedSoFarForKeywords[node._containedType]=1
                CheckForInvalidKeywords(g_names[node._containedType])


def ParseAsnFileList(listOfFilenames):
    asn1SccPath = os.getenv('ASN1SCC')
    if asn1SccPath is None:
        utility.panic("ASN1SCC environment variable is not set, you must set it.\n")
        sys.stderr.write("WARNING: ASN1SCC environment var unset, using naive ASN.1 parser...\n")
        global g_filename
        g_filename = listOfFilenames[0]
        ParseInput(listOfFilenames[0], True, False)
        for f in listOfFilenames[1:]:
            g_filename = f
            ParseInput(f, False, False)
        g_leafTypeDict.update(VerifyAndFixAST())

        for nodeTypename in g_names.keys():
            if nodeTypename not in g_checkedSoFarForKeywords:
                g_checkedSoFarForKeywords[nodeTypename] = 1
                CheckForInvalidKeywords(nodeTypename)
    else:
        (dummy, xmlAST) = tempfile.mkstemp()
        os.fdopen(dummy).close()
        #spawnResult = os.system("mono \""+asn1SccPath+"\" -ast \""+xmlAST+"\" \"" + "\" \"".join(listOfFilenames) + "\"")
        asn1SccDir = os.path.dirname(os.path.abspath(asn1SccPath))
        mono = "mono " if sys.argv[0].endswith('.py') and sys.platform.startswith('linux') else ""
        spawnResult = os.system(mono + "\""+asn1SccPath+"\" -customStg \""+asn1SccDir+"/xml.stg:"+xmlAST+"\" -customStgAstVerion 4 \"" + "\" \"".join(listOfFilenames) + "\"")
        if spawnResult != 0:
            if 1 == spawnResult/256:
                utility.panic("ASN1SCC reported syntax errors. Aborting...")
            elif 2 == spawnResult/256:
                utility.panic("ASN1SCC reported semantic errors (or mono failed). Aborting...")
            elif 3 == spawnResult/256:
                utility.panic("ASN1SCC reported internal error. Contact Semantix with this input. Aborting...")
            elif 4 == spawnResult/256:
                utility.panic("ASN1SCC reported usage error. Aborting...")
            else:
                utility.panic("ASN1SCC generic error. Contact Semantix with this input. Aborting...")
        xmlASTtoAsnAST.ParseASN1SCC_AST(xmlAST)
        os.unlink(xmlAST)
        g_names.update(xmlASTtoAsnAST.asnParser.g_names)
        g_leafTypeDict.update(xmlASTtoAsnAST.asnParser.g_leafTypeDict)
        g_checkedSoFarForKeywords.update(xmlASTtoAsnAST.asnParser.g_checkedSoFarForKeywords)
        g_typesOfFile.update(xmlASTtoAsnAST.asnParser.g_typesOfFile)

        # We also need to mark the artificial types - 
        # So spawn the custom type output at level 1 (unfiltered)
        # and mark any types not inside it as artificial.
        os.system(mono + "\""+asn1SccPath+"\" -customStg \""+asn1SccDir+"/xml.stg:"+xmlAST+"2\" -customStgAstVerion 1 \"" + "\" \"".join(listOfFilenames) + "\"")
        realTypes = {}
        for line in os.popen("grep  'ExportedType\>' \""+xmlAST+"2\"").readlines():
            line = re.sub(r'^.*Name="', '', line.strip())
            line = re.sub(r'" />$', '', line)
            realTypes[line] = 1
        os.unlink(xmlAST + "2")
        for nodeTypename in g_names.keys():
            if nodeTypename not in realTypes:
                g_names[nodeTypename]._isArtificial = True


def Dump():
    for nodeTypename in sorted(g_names.keys()):
        if g_names[nodeTypename]._isArtificial:
            continue
        print "\n===== From", g_names[nodeTypename]._asnFilename
        print nodeTypename
        print "::", g_names[nodeTypename], g_leafTypeDict[nodeTypename]


def main():
    if "-debug" in sys.argv:
        configMT.debugParser = True
        sys.argv.remove("-debug")
    if len(sys.argv) < 2:
        sys.stderr.write('Usage: %s input.asn [input2.asn] ...\n' % sys.argv[0])
        sys.exit(1)
    for f in sys.argv[1:]:
        if not os.path.isfile(f):
            sys.stderr.write("'%s' is not a file!\n" % f)
            sys.exit(1)

    ParseAsnFileList(sys.argv[1:])
    Dump()

if __name__ == "__main__":
    if "-pdb" in sys.argv:
        sys.argv.remove("-pdb")
        import pdb
        pdb.run('main()')
    else:
        main()
