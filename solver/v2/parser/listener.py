from antlr4 import *

from generated.PrerequisitesParser import PrerequisitesParser


class PrerequisitesListener(ParseTreeListener):
    def __init__(self):
        self.options = []

    def enterAndExpr(self, ctx: PrerequisitesParser.AndExprContext):
        print("enter and")
        courses = [
            c.getText()
            for c in ctx.getChildren()
            if isinstance(c, PrerequisitesParser.CourseContext)
        ]

        for option in self.options:
            option.extend(courses)
        if not self.options:
            self.options = courses

    def exitAndExpr(self, ctx: PrerequisitesParser.AndExprContext):
        print("exit and")

    def enterOrExpr(self, ctx: PrerequisitesParser.OrExprContext):
        print("enter or")
        courses = [
            c.getText()
            for c in ctx.getChildren()
            if isinstance(c, PrerequisitesParser.CourseContext)
        ]

        for course in courses:
            self.options.append([course])

    def exitOrExpr(self, ctx: PrerequisitesParser.OrExprContext):
        print("exit or")
