## How to refactor "oldschool" asyncio code
import argparse
import ast
import asyncio
import functools
import os
from asyncio import coroutine

parser = argparse.ArgumentParser("asyncompat")
parser.add_argument("--path", default=__file__)


### TEST SECTION ###

@coroutine
def producer():
    return 123


@asyncio.coroutine
def consumer():
    value = yield from producer()
    return value


def consumer2():
    value = yield from producer()
    return value


### TEST SECTION END ###

def is_coroutine_decorator(node):
    return (isinstance(node, ast.Attribute) and
            isinstance(node.value, ast.Name) and
            hasattr(node.value, "id") and
            node.value.id == "asyncio" and node.attr == "coroutine")


def is_coroutine_decorator_from_module(node, *, imported_asyncio):
    return (isinstance(node, ast.Name) and
            node.id == "coroutine" and
            isinstance(node.ctx, ast.Load) and
            imported_asyncio)


class FunctionDefVisitor(ast.NodeVisitor):
    def __init__(self):
        self.source = None
        self.first_run = True
        self.imported_asyncio = False

    def initiate_visit(self, source):
        self.source = source.splitlines()
        node = ast.parse(source)
        self.visit(node)
        self.first_run = False
        return self.visit(node)

    def visit_Import(self, node):
        for name in node.names:
            if name.name == "asyncio":
                self.imported_asyncio = True

    def visit_FunctionDef(self, node):
        if self.first_run:
            return

        decorators = list(filter(is_coroutine_decorator, node.decorator_list))
        decorators_from_module = list(
            filter(functools.partial(is_coroutine_decorator_from_module, imported_asyncio=self.imported_asyncio),
                   node.decorator_list))
        if decorators:
            print(node.lineno, ":", self.source[node.lineno], "is an oldschool coroutine!")

        elif decorators_from_module:
            print(node.lineno, ":", self.source[node.lineno], "is an oldschool coroutine!")


if __name__ == '__main__':
    v = FunctionDefVisitor()
    args = parser.parse_args()
    path = os.path.isfile(args.path) and os.path.abspath(args.path)
    if not path or not path.endswith(".py"):
        raise ValueError(f"{path} is not a valid path to a python file!")
    with open(path) as f:
        v.initiate_visit(f.read())
