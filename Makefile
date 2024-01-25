#.PHONY: all build venv

#all: build

venv:
	python3 -m venv venv
	./venv/bin/pip3 install --upgrade pip setuptools
	./venv/bin/pip3 install twine wheel pytest freezegun

build: venv
	rm -rf dist/* build/*
	./venv/bin/python3 setup.py bdist_wheel
	./venv/bin/pip3 install --force-reinstall dist/*.whl

test: build
	./venv/bin/pytest tests

#push: test
#	twine upload dist/*.whl
