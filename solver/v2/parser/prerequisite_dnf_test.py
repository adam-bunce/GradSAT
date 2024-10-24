import logging
from antlr4 import *
from generated.PrerequisitesParser import PrerequisitesParser
from generated.PrerequisitesLexer import PrerequisitesLexer
from listener import PrerequisitesListener

_logger = logging.getLogger(__name__)


def listener(expression: str):
    tmp = InputStream(expression)
    lexer = PrerequisitesLexer(tmp)
    stream = CommonTokenStream(lexer)
    parser = PrerequisitesParser(stream)
    tree = parser.expression()
    if parser.getNumberOfSyntaxErrors() > 0:
        _logger.error(
            "%d syntax errors parsing input", parser.getNumberOfSyntaxErrors()
        )

    else:
        walker = ParseTreeWalker()
        listener = PrerequisitesListener()
        walker.walk(listener, tree)
        return list(listener.options)


if __name__ == "__main__":

    cases = [
        [
            "MATH1020U and MATH2050U AND MATH3050U",
            [["MATH1020U", "MATH2050U", "MATH3050U"]],
        ],
        ["MATH1020U or MATH2050U", [["MATH1020U"], ["MATH2050U"]]],
        [
            "(MATH1000U or MATH3000U) and MATH4000U",
            [["MATH1000U", "MATH4000U"], ["MATH3000U", "MATH4000U"]],
        ],
    ]
    for case in cases:
        print("got", listener(case[0]), "\nexp", case[1])
        print("--------------")
