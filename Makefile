PY_SRC:=$(wildcard asn2dataModel.py aadl2glueC.py smp2asn.py *mappers/[a-zA-Z]*py commonPy/[a-zA-Z]*py)
PY_SRC:=$(filter-out B_mappers/antlr.main.py A_mappers/Stubs.py, ${PY_SRC})

all:	flake8 pylint mypy

flake8:
	@echo Performing syntax checks via flake8...
	@flake8 ${PY_SRC} || exit 1

pylint:
	@echo Performing static analysis via pylint...
	@pylint --disable=I --rcfile=pylint.cfg ${PY_SRC}

mypy:
	@echo Performing type analysis via mypy...
	@mypy --check-untyped-defs ${PY_SRC} || exit 1

.PHONY:	flake8 pylint mypy
