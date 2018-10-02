PY_SRC:=$(wildcard dmt/asn2dataModel.py dmt/aadl2glueC.py dmt/smp2asn.py dmt/*mappers/[a-zA-Z]*py dmt/commonPy/[a-zA-Z]*py)
PY_SRC:=$(filter-out dmt/B_mappers/antlr.main.py dmt/A_mappers/Stubs.py, ${PY_SRC})

# Python3.5 includes an older version of typing, which by default has priority over
# the one installed in $HOME/.local via setup.py.
#
# To address this, we find where our pip-installed typing lives:
TYPING_FOLDER:=$(shell pip3 show typing | grep ^Location | sed 's,^.*: ,,')
export PYTHONPATH=${TYPING_FOLDER}

all:	flake8 pylint mypy coverage testDB

flake8:
	@echo Performing syntax checks via flake8...
	@flake8 ${PY_SRC} || exit 1

pylint:
	@echo Performing static analysis via pylint...
	@pylint --disable=I --rcfile=pylint.cfg ${PY_SRC}  | grep -v '^$$' | sed -n '/^Report/q;p'

mypy:
	@echo Performing type analysis via mypy...
	@mypy --disallow-untyped-defs --check-untyped-defs --ignore-missing-imports ${PY_SRC} || exit 1

coverage:
	@echo Performing coverage checks...
	@$(MAKE) -C tests-coverage  || exit 1

testDB:
	@echo Installing DMT for local user...
	@pip3 install .
	@echo Performing database tests...
	@$(MAKE) -C tests-sqlalchemy  || exit 1

.PHONY:	flake8 pylint mypy coverage
