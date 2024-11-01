import unittest
from dataclasses import dataclass

from antlr4 import *
from generated.PrerequisitesParser import PrerequisitesParser
from generated.PrerequisitesLexer import PrerequisitesLexer


def expr_to_dnf(expression: str) -> list[list[str]]:
    stream = InputStream(expression)
    lexer = PrerequisitesLexer(stream)
    stream = CommonTokenStream(lexer)
    parser = PrerequisitesParser(stream)
    return parser.expression().result


@dataclass
class TestPair:
    expression: str
    expected: list[list[str]]


class TestDNFConversion(unittest.TestCase):
    def test_dnf_conversion(self):
        testcases: list[TestPair] = [
            TestPair("A", [["A"]]),
            TestPair(
                "E or ((A or B) and (C or D))",
                [["E"], ["A", "C"], ["A", "D"], ["B", "C"], ["B", "D"]],
            ),
            TestPair("A or B", [["A"], ["B"]]),
            TestPair("A and B", [["A", "B"]]),
            TestPair("(A or B) and C", [["A", "C"], ["B", "C"]]),
            TestPair("A or B or C or D", [["A"], ["B"], ["C"], ["D"]]),
            TestPair(
                "(A or B or C or D) and E",
                [["A", "E"], ["B", "E"], ["C", "E"], ["D", "E"]],
            ),
            TestPair("A and B and C and D", [["A", "B", "C", "D"]]),
            TestPair("(A and B and C and D) or E", [["A", "B", "C", "D"], ["E"]]),
            TestPair(
                "(A or B) and (C or D) and (E and F)",
                [
                    ["A", "D", "E", "F"],
                    ["A", "C", "E", "F"],
                    ["B", "D", "E", "F"],
                    ["B", "C", "E", "F"],
                ],
            ),
            TestPair(
                "((A or B) and (C or D)) or (E and F)",
                [
                    [
                        "A",
                        "D",
                    ],
                    [
                        "A",
                        "C",
                    ],
                    [
                        "B",
                        "D",
                    ],
                    [
                        "B",
                        "C",
                    ],
                    ["E", "F"],
                ],
            ),
        ]

        for case in testcases:
            actual = expr_to_dnf(case.expression)
            self.assertListEqual(
                sorted(case.expected),
                sorted(actual),
                f"failed test case {case.expected} expected {case.expected}, actual {actual}",
            )


if __name__ == "__main__":
    unittest.main()
