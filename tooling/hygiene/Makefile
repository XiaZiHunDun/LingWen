PYTHON ?= python3

.PHONY: all check clean

all: check

check:
	@rc=0; \
	for script in check_repo_state.py check_file_size.py check_brand_consistency.py check_import_linter.py; do \
		echo "▶ Running $$script"; \
		$(PYTHON) $$script || rc=$$?; \
	done; \
	exit $$rc

clean:
	find . -type d \( -name '__pycache__' -o -name '.mypy_cache' -o -name '.pytest_cache' -o -name '.ruff_cache' -o -name '*.egg-info' \) -prune -exec rm -rf {} +
