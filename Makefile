.PHONY: install test extract

install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

test:
	.venv/bin/pytest -q

extract:
	.venv/bin/python -m extract.air4thai
