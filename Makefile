PY_SRC:=$(wildcard dmt/asn2dataModel.py dmt/aadl2glueC.py dmt/smp2asn.py dmt/*mappers/[a-zA-Z]*py dmt/commonPy/[a-zA-Z]*py)
PY_SRC:=$(filter-out dmt/B_mappers/antlr.main.py dmt/A_mappers/Stubs.py, ${PY_SRC})

all:	flake8 pylint mypy

flake8:
	@echo Performing syntax checks via flake8...
	@flake8 ${PY_SRC} || exit 1

pylint:
	@echo Performing static analysis via pylint...
	@pylint --disable=I --rcfile=pylint.cfg ${PY_SRC}  | sed -n '/^Report/q;p'

mypy:
	@echo Performing type analysis via mypy...
	@mypy --check-untyped-defs ${PY_SRC} || exit 1

.PHONY:	flake8 pylint mypy
