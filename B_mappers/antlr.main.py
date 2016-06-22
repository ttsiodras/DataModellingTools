#!/usr/bin/env python
from . import AadlLexer
from . import AadlParser
import commonPy.aadlAST
import commonPy.utility
import antlr
import sys


def main():
    if len(sys.argv) > 1:
        L = AadlLexer.Lexer(sys.argv[1])
    else:
        L = AadlLexer.Lexer()
    P = AadlParser.Parser(L)
    P.setFilename(L.getFilename())

    try:
        P.aadl_specification()
    except antlr.ANTLRException as e:
        commonPy.utility.panic("Error: %s\n" % (str(e)))

    SystemsAndImplementations = commonPy.aadlAST.g_subProgramImplementations[:]
    SystemsAndImplementations.extend(commonPy.aadlAST.g_threadImplementations[:])
    SystemsAndImplementations.extend(commonPy.aadlAST.g_processImplementations[:])
    for si in SystemsAndImplementations:
        sp, sp_impl, modelingLanguage, fv_name = si[0], si[1], si[2], si[3]
        sp = commonPy.aadlAST.g_apLevelContainers[sp]
        print(sp._id + "." + sp_impl, "(", modelingLanguage, ") FV_name:", fv_name)
        for param in sp._params:
            print("\t", end=' ')
            if isinstance(param, commonPy.aadlAST.InParam):
                print("IN", end=' ')
            elif isinstance(param, commonPy.aadlAST.OutParam):
                print("OUT", end=' ')
            elif isinstance(param, commonPy.aadlAST.InOutParam):
                print("INOUT", end=' ')
            if isinstance(param._signal, commonPy.aadlAST.Signal):
                print("\t", param._id, ":", param._signal._asnFilename, param._signal._asnNodename, "(", param._sourceElement._encoding, ")")
            else:
                print("\t", param._id, ":", param._signal, "(", param._sourceElement._encoding, ")")
        print()
        if len(sp._connections):
            print("\tConnections:")
            for pair in sp._connections:
                print("\t\tfrom", pair._from._componentId + ':' + pair._from._portId, "to", pair._to._componentId + ':' + pair._to._portId)
            print()

if __name__ == "__main__":
    main()
