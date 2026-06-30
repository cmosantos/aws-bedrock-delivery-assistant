.PHONY: validate test demo build deploy delete

validate:
	sam validate --lint

test:
	python -m unittest discover -s tests -v

demo:
	python scripts/local_demo.py

build:
	sam build

deploy:
	sam deploy --guided

delete:
	sam delete
