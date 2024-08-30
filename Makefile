.PHONY: install run test clean

install:
	pip install -r requirements.txt
	pip install -e .

run:
	python examples/basic/app.py

test:
	pytest tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete