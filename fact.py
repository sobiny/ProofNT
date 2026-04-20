from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from expr import Expr


class Fact:
    """
    所有“数学事实”的基类。

    例如：
    - Integer(n)
    - Even(n)
    - Divides(3, n^2+1)
    - Congruent(a, b, m)

    注意：
    表达式 Expr 表示“对象”
    事实 Fact 表示“关于对象的命题”
    """

    def canonical(self) -> "Fact":
        """
        返回该事实的规范形式。

        例如：
        - Congruent(a,b,m) 和 Congruent(b,a,m) 可以统一
        - Coprime(a,b) 和 Coprime(b,a) 可以统一
        """
        return self

    def args(self) -> Tuple:
        """
        返回事实的参数，供 key() / 打印 / 比较使用。
        """
        return ()

    def key(self) -> tuple:
        """
        生成唯一 key，用来做去重和比较。

        注意这里是基于 canonical() 后的结果做的。
        """
        c = self.canonical()
        return (c.__class__.__name__,) + tuple(str(x) for x in c.args())

    def __hash__(self) -> int:
        return hash(self.key())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Fact):
            return False
        return self.key() == other.key()


@dataclass(frozen=True)
class Integer(Fact):
    """
    表示某个表达式是整数。
    """
    x: Expr

    def args(self) -> Tuple:
        return (self.x.canonical(),)

    def __str__(self) -> str:
        return f"Integer({self.x})"


@dataclass(frozen=True)
class Even(Fact):
    """
    表示某个表达式是偶数。
    """
    x: Expr

    def args(self) -> Tuple:
        return (self.x.canonical(),)

    def __str__(self) -> str:
        return f"Even({self.x})"


@dataclass(frozen=True)
class Odd(Fact):
    """
    表示某个表达式是奇数。
    """
    x: Expr

    def args(self) -> Tuple:
        return (self.x.canonical(),)

    def __str__(self) -> str:
        return f"Odd({self.x})"


@dataclass(frozen=True)
class Equal(Fact):
    """
    表示两个表达式相等。
    """
    left: Expr
    right: Expr

    def canonical(self) -> Fact:
        """
        Equal(a,b) 与 Equal(b,a) 统一。
        """
        a = self.left.canonical()
        b = self.right.canonical()
        if str(a) <= str(b):
            return Equal(a, b)
        return Equal(b, a)

    def args(self) -> Tuple:
        c = self.canonical()
        return (c.left, c.right)

    def __str__(self) -> str:
        return f"{self.left} = {self.right}"


@dataclass(frozen=True)
class Divides(Fact):
    """
    表示 divisor | target
    """
    divisor: Expr
    target: Expr

    def canonical(self) -> Fact:
        return Divides(self.divisor.canonical(), self.target.canonical())

    def args(self) -> Tuple:
        c = self.canonical()
        return (c.divisor, c.target)

    def __str__(self) -> str:
        return f"{self.divisor} | {self.target}"


@dataclass(frozen=True)
class Congruent(Fact):
    """
    表示 left ≡ right (mod modulus)
    """
    left: Expr
    right: Expr
    modulus: Expr

    def canonical(self) -> Fact:
        """
        同余左右可以交换：
        a ≡ b (mod m) 与 b ≡ a (mod m) 等价
        """
        a = self.left.canonical()
        b = self.right.canonical()
        m = self.modulus.canonical()
        if str(a) <= str(b):
            return Congruent(a, b, m)
        return Congruent(b, a, m)

    def args(self) -> Tuple:
        c = self.canonical()
        return (c.left, c.right, c.modulus)

    def __str__(self) -> str:
        return f"{self.left} ≡ {self.right} (mod {self.modulus})"


@dataclass(frozen=True)
class Coprime(Fact):
    """
    表示两个表达式互素。
    """
    left: Expr
    right: Expr

    def canonical(self) -> Fact:
        a = self.left.canonical()
        b = self.right.canonical()
        if str(a) <= str(b):
            return Coprime(a, b)
        return Coprime(b, a)

    def args(self) -> Tuple:
        c = self.canonical()
        return (c.left, c.right)

    def __str__(self) -> str:
        return f"Coprime({self.left}, {self.right})"


@dataclass(frozen=True)
class GCD(Fact):
    """
    表示 gcd(left, right) = value
    """
    left: Expr
    right: Expr
    value: Expr

    def canonical(self) -> Fact:
        a = self.left.canonical()
        b = self.right.canonical()
        d = self.value.canonical()
        if str(a) <= str(b):
            return GCD(a, b, d)
        return GCD(b, a, d)

    def args(self) -> Tuple:
        c = self.canonical()
        return (c.left, c.right, c.value)

    def __str__(self) -> str:
        return f"gcd({self.left}, {self.right}) = {self.value}"


@dataclass(frozen=True)
class Contradiction(Fact):
    """
    表示已经推出矛盾。
    后面做反证题时会很有用。
    """
    reason: str = ""

    def args(self) -> Tuple:
        return (self.reason,)

    def __str__(self) -> str:
        if self.reason:
            return f"Contradiction({self.reason})"
        return "Contradiction"