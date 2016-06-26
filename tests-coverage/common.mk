# Detect name of the coverage tool (package named has changed)

RUN_PYTHON_COVERAGE:=$(shell command -v python3-coverage 2>/dev/null)
RUN_COVERAGE:=$(shell command -v coverage 2>/dev/null)

ifndef RUN_PYTHON_COVERAGE

ifndef RUN_COVERAGE
    $(error "Neither 'python3-coverage' nor 'coverage' are installed.")
else
    COVERAGE:=coverage
endif

else
    COVERAGE:=python3-coverage
endif

