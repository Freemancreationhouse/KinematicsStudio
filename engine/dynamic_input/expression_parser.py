from __future__ import annotations

import ast
import operator
from dataclasses import dataclass
from typing import Callable


class DynamicInputExpressionError(ValueError):
    """Raised when a dynamic input expression cannot be evaluated safely."""


@dataclass(frozen=True)
class ExpressionResult:
    """Result produced by the expression parser."""

    expression: str
    value: float


class ExpressionParser:
    """Safe arithmetic expression parser for dynamic CAD input."""

    _binary_operators: dict[type[ast.operator], Callable[[float, float], float]] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
    }
    _unary_operators: dict[type[ast.unaryop], Callable[[float], float]] = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    def parse(self, expression: str | int | float) -> ExpressionResult:
        """Evaluate a numeric expression using safe arithmetic only."""

        if isinstance(expression, (int, float)):
            return ExpressionResult(str(expression), float(expression))

        text = str(expression).strip()
        if not text:
            raise DynamicInputExpressionError("Expression is empty.")

        try:
            tree = ast.parse(text, mode="eval")
        except SyntaxError as exc:
            raise DynamicInputExpressionError(str(exc)) from exc

        value = self._evaluate(tree.body)
        return ExpressionResult(text, value)

    def _evaluate(self, node: ast.AST) -> float:
        """Evaluate one validated expression AST node."""

        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)

        if isinstance(node, ast.BinOp):
            operation = self._binary_operators.get(type(node.op))
            if operation is None:
                raise DynamicInputExpressionError("Unsupported operator.")
            right = self._evaluate(node.right)
            if isinstance(node.op, ast.Div) and right == 0.0:
                raise DynamicInputExpressionError("Division by zero.")
            return operation(self._evaluate(node.left), right)

        if isinstance(node, ast.UnaryOp):
            operation = self._unary_operators.get(type(node.op))
            if operation is None:
                raise DynamicInputExpressionError("Unsupported unary operator.")
            return operation(self._evaluate(node.operand))

        raise DynamicInputExpressionError("Unsupported expression.")
