.PHONY: build clean test

name = Prerequisites
ANTLR = java -jar antlr-4.13.0-complete.jar -visitor -listener -Dlanguage=Python3

build:
	make clean
	mkdir -p ./generated
	$(ANTLR) -o ./generated/ ./Prerequisites.g4

test:
	make build
	pwd
	python dnf_convertor.py -v

clean:
	rm -rf ./generated
