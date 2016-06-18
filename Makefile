PY_SRC:=$(wildcard asn2dataModel.py aadl2glueC.py smp2asn.py *mappers/[a-zA-Z]*py commonPy/[a-zA-Z]*py)

all:	flake8 pylint mypy

flake8:
	flake8 ${PY_SRC} || exit 1

pylint:
	pylint ${PY_SRC} || exit 1

mypy:
	mypy --check-untyped-defs ${PY_SRC} || exit 1

.PHONY:	flake8 pylint mypy
