from antlr4 import *
from generated.PrerequisitesParser import PrerequisitesParser
from generated.PrerequisitesLexer import PrerequisitesLexer


def test(expression: str, expected: list[list[str]]):
    tmp = InputStream(expression)
    lexer = PrerequisitesLexer(tmp)
    stream = CommonTokenStream(lexer)
    parser = PrerequisitesParser(stream)

    dnf = parser.expression().result

    if dnf != expected:
        print("\n❌")
    else:
        print("\n✅")

    print("got     ", dnf)
    print("expected", expected)


def main():
    expression = "E or ((A or B) and (C or D))"
    expected = [["E"], ["A", "C"], ["A", "D"], ["B", "C"], ["B", "D"]]
    test(expression, expected)

    expression = "A or B"
    test(expression, [["A"], ["B"]])

    expression = "(A or B) and C"
    test(expression, [["A", "C"], ["B", "C"]])

    expression = "A or B or C or D"
    test(expression, [["A"], ["B"], ["C"], ["D"]])

    expression = "(A or B or C or D) and E"
    test(expression, [["A", "E"], ["B", "E"], ["C", "E"], ["D", "E"]])

    expression = "A and B and C and D"
    test(expression, [["A", "B", "C", "D"]])

    expression = "(A and B and C and D) or E"
    test(expression, [["A", "B", "C", "D"], ["E"]])


if __name__ == "__main__":
    main()
