from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


class Expr:
    """
    所有数学表达式的基类。

    设计思想：
    - 我们希望把数论里的表达式统一表示成“树”
    - 例如 n^2 - 1 会表示成 Sub(Pow(Var("n"), Const(2)), Const(1))
    - 后续的规则匹配、规范化、打印，都会基于这些对象进行

    注意：
    - 这里暂时不做很复杂的代数化简
    - 只做一些最基础、最安全的 canonical 处理
    """

    def children(self) -> Tuple["Expr", ...]:
        """
        返回当前表达式的子节点。
        叶子节点（变量、常数）没有孩子，所以默认返回空元组。
        """
        return ()

    def canonical(self) -> "Expr":
        """
        返回当前表达式的“规范形式”。

        第一版里，我们只做很轻量的规范化，例如：
        - 常数加法、常数乘法直接算掉
        - a + 0 -> a
        - a * 1 -> a
        - a * 0 -> 0
        - a - a -> 0
        - a^1 -> a
        - a^0 -> 1

        更复杂的化简以后再做。
        """
        return self

    def __add__(self, other: "Expr") -> "Expr":
        return Add(self, other).canonical()

    def __sub__(self, other: "Expr") -> "Expr":
        return Sub(self, other).canonical()

    def __mul__(self, other: "Expr") -> "Expr":
        return Mul(self, other).canonical()

    def __pow__(self, power: "Expr") -> "Expr":
        return Pow(self, power).canonical()


@dataclass(frozen=True)
class Var(Expr):
    """
    变量，例如 n, a, b, x
    """
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Const(Expr):
    """
    整数常数，例如 0, 1, 2, -3
    """
    value: int

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Add(Expr):
    """
    加法节点：left + right
    """
    left: Expr
    right: Expr

    def children(self) -> Tuple[Expr, Expr]:
        return (self.left, self.right)

    def canonical(self) -> Expr:
        """
        对加法做最基础的规范化。

        当前做的事情：
        1. 递归规范化左右子项
        2. 如果两边都是常数，则直接算出结果
        3. 展平嵌套加法，例如 (a + (b + c)) -> [a, b, c]
        4. 排序，尽量保证 a+b 与 b+a 的表示统一
        5. 重建表达式树
        """
        a = self.left.canonical()
        b = self.right.canonical()

        # 常数 + 常数，直接算掉
        if isinstance(a, Const) and isinstance(b, Const):
            return Const(a.value + b.value)

        # 0 + x 或 x + 0
        if isinstance(a, Const) and a.value == 0:
            return b
        if isinstance(b, Const) and b.value == 0:
            return a

        # 把嵌套加法扁平化，方便统一排序
        terms = flatten_add(a) + flatten_add(b)
        terms = sorted(terms, key=expr_sort_key)

        if not terms:
            return Const(0)
        if len(terms) == 1:
            return terms[0]

        # 重新折叠成左结合树
        cur = terms[0]
        for t in terms[1:]:
            cur = Add(cur, t)
        return cur

    def __str__(self) -> str:
        return f"({self.left} + {self.right})"


@dataclass(frozen=True)
class Sub(Expr):
    """
    减法节点：left - right
    """
    left: Expr
    right: Expr

    def children(self) -> Tuple[Expr, Expr]:
        return (self.left, self.right)

    def canonical(self) -> Expr:
        """
        对减法做最基础的规范化。

        当前只做：
        - 常数相减
        - a - a = 0
        - a - 0 = a

        注意：
        我们目前不把减法强行改写成加负数，
        因为这样会让第一版代码更容易看懂。
        """
        a = self.left.canonical()
        b = self.right.canonical()

        if isinstance(a, Const) and isinstance(b, Const):
            return Const(a.value - b.value)

        if a == b:
            return Const(0)

        if isinstance(b, Const) and b.value == 0:
            return a

        return Sub(a, b)

    def __str__(self) -> str:
        return f"({self.left} - {self.right})"


@dataclass(frozen=True)
class Mul(Expr):
    """
    乘法节点：left * right
    """
    left: Expr
    right: Expr

    def children(self) -> Tuple[Expr, Expr]:
        return (self.left, self.right)

    def canonical(self) -> Expr:
        """
        对乘法做最基础规范化。

        当前做：
        1. 常数乘法直接算
        2. x*0 -> 0
        3. x*1 -> x
        4. 扁平化嵌套乘法
        5. 排序，统一交换律下的表示
        """
        a = self.left.canonical()
        b = self.right.canonical()

        if isinstance(a, Const) and isinstance(b, Const):
            return Const(a.value * b.value)

        # 乘以 0
        if isinstance(a, Const) and a.value == 0:
            return Const(0)
        if isinstance(b, Const) and b.value == 0:
            return Const(0)

        # 乘以 1
        if isinstance(a, Const) and a.value == 1:
            return b
        if isinstance(b, Const) and b.value == 1:
            return a

        terms = flatten_mul(a) + flatten_mul(b)
        terms = sorted(terms, key=expr_sort_key)

        if not terms:
            return Const(1)
        if len(terms) == 1:
            return terms[0]

        cur = terms[0]
        for t in terms[1:]:
            cur = Mul(cur, t)
        return cur

    def __str__(self) -> str:
        return f"({self.left} * {self.right})"


@dataclass(frozen=True)
class Pow(Expr):
    """
    幂节点：base ^ exp
    """
    base: Expr
    exp: Expr

    def children(self) -> Tuple[Expr, Expr]:
        return (self.base, self.exp)

    def canonical(self) -> Expr:
        """
        对幂做最基础规范化。

        当前做：
        - a^0 = 1
        - a^1 = a
        - 常数的非负整数次幂直接算掉
        """
        a = self.base.canonical()
        b = self.exp.canonical()

        if isinstance(b, Const):
            if b.value == 0:
                return Const(1)
            if b.value == 1:
                return a

        if isinstance(a, Const) and isinstance(b, Const) and b.value >= 0:
            return Const(a.value ** b.value)

        return Pow(a, b)

    def __str__(self) -> str:
        return f"({self.base}^{self.exp})"


def flatten_add(expr: Expr) -> list[Expr]:
    """
    把加法树拍平。

    例如：
    (a + (b + c)) -> [a, b, c]
    """
    if isinstance(expr, Add):
        return flatten_add(expr.left) + flatten_add(expr.right)
    return [expr]


def flatten_mul(expr: Expr) -> list[Expr]:
    """
    把乘法树拍平。

    例如：
    (a * (b * c)) -> [a, b, c]
    """
    if isinstance(expr, Mul):
        return flatten_mul(expr.left) + flatten_mul(expr.right)
    return [expr]


def expr_sort_key(expr: Expr) -> tuple:
    """
    用于给表达式排序。

    为什么要排序？
    因为加法和乘法满足交换律，
    我们希望尽量让 a+b 与 b+a 变成同一个内部表示，
    这样事实去重会简单很多。

    第一版里先偷懒，按：
    (类名, 字符串表示)
    排序。
    """
    return (expr.__class__.__name__, str(expr))