PYTHON ?= python3

.PHONY: all check clean

all: check

check:
	$(PYTHON) check_repo_state.py
	$(PYTHON) check_file_size.py

clean:
	rm -rf __pycache__ .pytest_cache tests/__pycache__
