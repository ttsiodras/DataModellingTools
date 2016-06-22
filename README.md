TASTE Data Modelling Technologies
=================================

Installation
------------

    $ pip install --user -r requirements.txt
    $ make flake8  # optional, check for pep8 compliance
    $ make pylint  # optional, static analysis with pylint
    $ pip install --user .

Contents
--------

- **commonPy** (*library*)

    Contains the basic API for parsing ASN.1 (via invocation of 
    [ASN1SCC](https://github.com/ttsiodras/asn1scc) and simplification
    of the generated XML AST representation to the Python classes
    inside `asnAST.py`.

- **asn2aadlPlus** (*utility*)

    Converts the type declarations inside ASN.1 grammars to AADL
    declarations (used by the Ellidiss GUI to create the final systems)

- **asn2dataModel** (*utility*)

    Reads the ASN.1 specification of the exchanged messages, and generates
    the semantically equivalent Modeling tool/Modeling language declarations
    (e.g.  SCADE/Lustre, Matlab/Simulink statements, etc). 

    The actual mapping logic exists in plugins, called *A mappers*
    (`simulink_A_mapper.py` handles Simulink/RTW, `scade6_A_mapper.py`
    handles SCADE5, `ada_A_mapper.py` generates Ada types,
    `sqlalchemy_A_mapper.py`, generates SQL definitions via SQLAlchemy, etc)

- **aadl2glueC** (*utility*)

    Reads the AADL specification of the system, and then generates the runtime
    bridge-code that will map the message data structures from those generated
    by [ASN1SCC](https://github.com/ttsiodras/asn1scc) to/from those generated
    by the modeling tool used to functionally model the subsystem (e.g. SCADE,
    ObjectGeode, Matlab/Simulink, C, Ada, etc).

