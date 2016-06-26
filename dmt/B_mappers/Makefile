all:	makeParser runTest

makeParser: AadlParser.py

AadlParser.py: aadl.g
	rm -f AadlLexer.py AadlParser.py
	runantlr -o . aadl.g || { echo You need to apt-get install antlr ; exit 1 ; }

runTest:
	./antlr.main.py < PierreToyExampleSystem.aadl
