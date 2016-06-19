PY_SRC:=$(wildcard asn2dataModel.py aadl2glueC.py smp2asn.py *mappers/[a-zA-Z]*py commonPy/[a-zA-Z]*py)
PY_SRC:=$(filter-out B_mappers/antlr.main.py, ${PY_SRC})

all:	flake8 pylint mypy

flake8:
	flake8 ${PY_SRC} || exit 1

pylint:
	for i in ${PY_SRC} ; do pylint $$i || { echo $$i ; exit 1; } ; done

mypy:
	mypy --check-untyped-defs ${PY_SRC} || exit 1

.PHONY:	flake8 pylint mypy
