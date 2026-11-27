.PHONY: test test-calculator test-history test-app run run-worker lint clean

PYTHON ?= python3

# Run the complete test suite.
test:
	$(PYTHON) -m unittest discover -s tests -t . -v

# Run the calculator arithmetic tests.
test-runner:
	$(PYTHON) -m unittest -v test_runner.py

test-calculator:
	$(PYTHON) -m unittest -v test_calculator.TestCalculator

# Run the history and persistence tests.
test-history:
	$(PYTHON) -m unittest -v test_calculator.TestHistory

# Run the interactive application tests.
test-app:
	$(PYTHON) -m unittest -v test_calculator.TestCalculatorApp

# Start the calculator application.
run:
	$(PYTHON) main.py

# Start the calculator application with background workers.
run-worker:
	$(PYTHON) main.py --worker

# Lint source, tests, and entrypoint.
lint:
	ruff check src tests main.py

# Remove generated Python cache files.
clean:
	rm -rf __pycache__
