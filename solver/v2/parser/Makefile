.PHONY: build clean

name = Prerequisites
ANTLR = java -jar antlr-4.13.0-complete.jar -visitor -listener -Dlanguage=Python3

build:
	make clean
	mkdir -p ./generated
	$(ANTLR) -o ./generated/ ./Prerequisites.g4

clean:
	rm -rf ./generated
