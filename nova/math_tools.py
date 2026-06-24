from __future__ import annotations

import re

from sympy import Eq, factor, solve, sympify
from sympy.parsing.sympy_parser import convert_xor, implicit_multiplication_application, parse_expr, standard_transformations

TRANSFORMS = standard_transformations + (implicit_multiplication_application, convert_xor)


def _clean(text: str) -> str:
    return (
        text.replace("plus", "+")
        .replace("minus", "-")
        .replace("times", "*")
        .replace("multiplied by", "*")
        .replace("divided by", "/")
        .replace("x squared", "x**2")
        .replace("equals", "=")
    )


def do_math(expression: str) -> str:
    expression = _clean(expression.strip())
    if not expression:
        return "Tell me a math expression after the word math."
    try:
        result = sympify(expression).evalf()
        if result == int(result):
            result = int(result)
        return f"The answer is {result}."
    except Exception:
        return "I could not solve that math problem yet. Try something like math 5 + 7 or math sqrt(81)."


def do_solve(expression: str) -> str:
    expression = _clean(expression.strip())
    try:
        if "=" in expression:
            left, right = expression.split("=", 1)
            problem = Eq(parse_expr(left, transformations=TRANSFORMS), parse_expr(right, transformations=TRANSFORMS))
        else:
            problem = parse_expr(expression, transformations=TRANSFORMS)
        answers = solve(problem)
        return f"The solution is {answers}."
    except Exception:
        return "I could not solve that equation yet. Try solve x**2 - 5*x + 6 = 0."


def maybe_natural_math(command: str) -> str | None:
    lower = command.lower().strip("?")
    if lower.startswith("what is "):
        expr = re.sub(r"^what is ", "", lower)
        return do_math(expr)
    return None

