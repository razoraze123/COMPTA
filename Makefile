.PHONY: lint test check

lint:
	flake8 MOTEUR/compta/achats

test:
	QT_QPA_PLATFORM=offscreen PYTHONPATH=. pytest -q

check: lint test
