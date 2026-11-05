.PHONY: test test-calculator test-history test-app run clean

PYTHON ?= python3

# Run the complete test suite.
test:
	$(PYTHON) -m unittest -v test_calculator.py

# Run the calculator arithmetic tests.
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
	$(PYTHON) calculator.py

# Remove generated Python cache files.
clean:
	rm -rf __pycache__
