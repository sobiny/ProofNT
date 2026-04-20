from __future__ import annotations

"""
这个文件放“第一批内置规则”。

当前目标：
1. 让系统具备最基础的同余推理能力
2. 让系统具备最基础的整除推理能力
3. 保持规则尽量“安全”，避免搜索空间爆炸太快

重要说明：
- 这里大部分规则都是“确定性规则”
- 也就是：给定前提后，结论数量比较有限
- 我们暂时尽量不写那种会无限生成新式子的规则
  例如 d|a => d|(a*t) 这种会导致严重膨胀，先不加
"""

from expr import Add, Mul, Sub, Const
from fact import Congruent, Coprime, Divides, Even, GCD, Equal
from rules import DerivedFact, Rule


# ============================================================
# 一、同余规则
# ============================================================

def rule_congruence_symmetric(facts):
    """
    规则：
        a ≡ b (mod m)  =>  b ≡ a (mod m)

    注意：
    - 由于我们的 Congruent.canonical() 已经把左右做了排序，
      所以这条规则在很多情况下不会真的新增事实。
    - 但保留它是有价值的：
      1. 逻辑上完整
      2. 如果以后修改 canonical 设计，这条规则仍然正确
    """
    for f in facts:
        if isinstance(f, Congruent):
            yield DerivedFact(
                fact=Congruent(f.right, f.left, f.modulus),
                parent_facts=[f],
                note="同余关系具有对称性。",
            )


def rule_congruence_to_divides(facts):
    """
    规则：
        a ≡ b (mod m)  =>  m | (a - b)

    这是“同余定义”最常用的一个方向。
    """
    for f in facts:
        if isinstance(f, Congruent):
            yield DerivedFact(
                fact=Divides(f.modulus, Sub(f.left, f.right).canonical()),
                parent_facts=[f],
                note="由同余定义可得模数整除两边之差。",
            )


def rule_divides_to_congruence_zero(facts):
    """
    规则：
        m | x  =>  x ≡ 0 (mod m)

    这是整除到同余的一个非常常见的转化。
    它能让“整除问题”和“同余问题”互相联通。
    """
    for f in facts:
        if isinstance(f, Divides):
            yield DerivedFact(
                fact=Congruent(f.target, Const(0), f.divisor),
                parent_facts=[f],
                note="若 m 整除 x，则 x 模 m 同余于 0。",
            )


def rule_congruence_transitive(facts):
    """
    规则：
        a ≡ b (mod m), b ≡ c (mod m)  =>  a ≡ c (mod m)

    实现方式：
    - 双层循环枚举两条同余事实
    - 要求模数相同
    - 再检查中间项是否衔接

    注意：
    - 因为 canonical() 会自动对称化，
      所以这里只需做最自然的匹配即可
    """
    congruences = [f for f in facts if isinstance(f, Congruent)]

    for f1 in congruences:
        for f2 in congruences:
            # 模数必须相同
            if f1.modulus.canonical() != f2.modulus.canonical():
                continue

            # f1: a ≡ b (mod m)
            # f2: b ≡ c (mod m)
            # 推出 a ≡ c (mod m)
            if f1.right.canonical() == f2.left.canonical():
                yield DerivedFact(
                    fact=Congruent(f1.left, f2.right, f1.modulus),
                    parent_facts=[f1, f2],
                    note="由同余的传递性得到新同余关系。",
                )


def rule_congruence_add(facts):
    """
    规则：
        a ≡ b (mod m), c ≡ d (mod m)
        =>
        a + c ≡ b + d (mod m)

    这是同余最基础的“加法相容性”。
    """
    congruences = [f for f in facts if isinstance(f, Congruent)]

    for f1 in congruences:
        for f2 in congruences:
            if f1.modulus.canonical() != f2.modulus.canonical():
                continue

            left_expr = Add(f1.left, f2.left).canonical()
            right_expr = Add(f1.right, f2.right).canonical()

            yield DerivedFact(
                fact=Congruent(left_expr, right_expr, f1.modulus),
                parent_facts=[f1, f2],
                note="同余在加法下保持。",
            )


def rule_congruence_sub(facts):
    """
    规则：
        a ≡ b (mod m), c ≡ d (mod m)
        =>
        a - c ≡ b - d (mod m)

    这条规则对很多整除 / 同余题都很常用。
    """
    congruences = [f for f in facts if isinstance(f, Congruent)]

    for f1 in congruences:
        for f2 in congruences:
            if f1.modulus.canonical() != f2.modulus.canonical():
                continue

            left_expr = Sub(f1.left, f2.left).canonical()
            right_expr = Sub(f1.right, f2.right).canonical()

            yield DerivedFact(
                fact=Congruent(left_expr, right_expr, f1.modulus),
                parent_facts=[f1, f2],
                note="同余在减法下保持。",
            )


def rule_congruence_mul(facts):
    """
    规则：
        a ≡ b (mod m), c ≡ d (mod m)
        =>
        ac ≡ bd (mod m)

    这是同余在乘法下的相容性。
    它对于证明 a^2 ≡ b^2、a^k ≡ b^k 非常重要。
    """
    congruences = [f for f in facts if isinstance(f, Congruent)]

    for f1 in congruences:
        for f2 in congruences:
            if f1.modulus.canonical() != f2.modulus.canonical():
                continue

            left_expr = Mul(f1.left, f2.left).canonical()
            right_expr = Mul(f1.right, f2.right).canonical()

            yield DerivedFact(
                fact=Congruent(left_expr, right_expr, f1.modulus),
                parent_facts=[f1, f2],
                note="同余在乘法下保持。",
            )


def rule_equal_to_congruence(facts):
    """
    规则：
        a = b  =>  a ≡ b (mod m)

    注意：
    - 严格说这条规则需要给定一个模 m 才能成立
    - 所以“裸等式 -> 同余”本身不是确定性规则
    - 第一版不应该直接无条件加入

    因此这里先保留注释，不实际启用。
    """
    return
    yield  # 占位，保证这是个生成器函数


# ============================================================
# 二、整除规则
# ============================================================

def rule_divides_reflexive(facts):
    """
    规则：
        x | x

    注意：
    - 这条规则如果对“所有表达式”都无条件生成，会膨胀得很厉害
    - 所以这里只对“已经出现过的 Divides(a,b) 里的 a 和 b”
      或其他事实里显式出现的表达式，暂时不自动加

    第一版先不启用，避免太多平凡事实。
    """
    return
    yield


def rule_divides_transitive(facts):
    """
    规则：
        a | b, b | c  =>  a | c

    这是整除关系非常基础的传递性。
    """
    divides_facts = [f for f in facts if isinstance(f, Divides)]

    for f1 in divides_facts:
        for f2 in divides_facts:
            # f1: a | b
            # f2: b | c
            if f1.target.canonical() == f2.divisor.canonical():
                yield DerivedFact(
                    fact=Divides(f1.divisor, f2.target),
                    parent_facts=[f1, f2],
                    note="由整除的传递性得到新整除关系。",
                )


def rule_divides_add(facts):
    """
    规则：
        d | a, d | b  =>  d | (a + b)

    这是整除对加法的封闭性。
    """
    divides_facts = [f for f in facts if isinstance(f, Divides)]

    for f1 in divides_facts:
        for f2 in divides_facts:
            # 要求公用同一个除数 d
            if f1.divisor.canonical() != f2.divisor.canonical():
                continue

            expr = Add(f1.target, f2.target).canonical()

            yield DerivedFact(
                fact=Divides(f1.divisor, expr),
                parent_facts=[f1, f2],
                note="若同一数分别整除两数，则也整除它们的和。",
            )


def rule_divides_sub(facts):
    """
    规则：
        d | a, d | b  =>  d | (a - b)

    这是整除对减法的封闭性。
    """
    divides_facts = [f for f in facts if isinstance(f, Divides)]

    for f1 in divides_facts:
        for f2 in divides_facts:
            if f1.divisor.canonical() != f2.divisor.canonical():
                continue

            expr = Sub(f1.target, f2.target).canonical()

            yield DerivedFact(
                fact=Divides(f1.divisor, expr),
                parent_facts=[f1, f2],
                note="若同一数分别整除两数，则也整除它们的差。",
            )


def rule_divides_zero(facts):
    """
    规则：
        对于已出现过的 d，可以生成 d | 0

    数学上这是永真命题。
    但它不适合无脑对所有表达式都生成。

    这里采取一个温和策略：
    - 只要某个 d 已经在 Divides(d, something) 中出现过
    - 就允许生成 d | 0

    这样能帮助一些减法、同余转化的闭包。
    """
    seen_divisors = []

    for f in facts:
        if isinstance(f, Divides):
            if f.divisor not in seen_divisors:
                seen_divisors.append(f.divisor)

    for d in seen_divisors:
        yield DerivedFact(
            fact=Divides(d, Const(0)),
            parent_facts=[],
            note="任意整数都整除 0。",
        )


# ============================================================
# 三、gcd / parity 基础规则
# ============================================================

def rule_coprime_to_gcd(facts):
    """
    规则：
        Coprime(a, b)  =>  gcd(a, b) = 1
    """
    for f in facts:
        if isinstance(f, Coprime):
            yield DerivedFact(
                fact=GCD(f.left, f.right, Const(1)),
                parent_facts=[f],
                note="互素意味着最大公因数为 1。",
            )


def rule_gcd_implies_divides_left(facts):
    """
    规则：
        gcd(a, b) = d  =>  d | a
    """
    for f in facts:
        if isinstance(f, GCD):
            yield DerivedFact(
                fact=Divides(f.value, f.left),
                parent_facts=[f],
                note="最大公因数必整除第一个数。",
            )


def rule_gcd_implies_divides_right(facts):
    """
    规则：
        gcd(a, b) = d  =>  d | b
    """
    for f in facts:
        if isinstance(f, GCD):
            yield DerivedFact(
                fact=Divides(f.value, f.right),
                parent_facts=[f],
                note="最大公因数必整除第二个数。",
            )


def rule_even_implies_divides_2(facts):
    """
    规则：
        Even(x)  =>  2 | x
    """
    for f in facts:
        if isinstance(f, Even):
            yield DerivedFact(
                fact=Divides(Const(2), f.x),
                parent_facts=[f],
                note="偶数可被 2 整除。",
            )


# ============================================================
# 四、规则总表
# ============================================================

BUILTIN_RULES = [
    # ---------- 同余 ----------
    Rule(name="congruence_symmetric", func=rule_congruence_symmetric),
    Rule(name="congruence_to_divides", func=rule_congruence_to_divides),
    Rule(name="divides_to_congruence_zero", func=rule_divides_to_congruence_zero),
    Rule(name="congruence_transitive", func=rule_congruence_transitive),
    Rule(name="congruence_add", func=rule_congruence_add),
    Rule(name="congruence_sub", func=rule_congruence_sub),
    Rule(name="congruence_mul", func=rule_congruence_mul),

    # ---------- 整除 ----------
    Rule(name="divides_transitive", func=rule_divides_transitive),
    Rule(name="divides_add", func=rule_divides_add),
    Rule(name="divides_sub", func=rule_divides_sub),
    Rule(name="divides_zero", func=rule_divides_zero),

    # ---------- gcd / parity ----------
    Rule(name="coprime_to_gcd", func=rule_coprime_to_gcd),
    Rule(name="gcd_implies_divides_left", func=rule_gcd_implies_divides_left),
    Rule(name="gcd_implies_divides_right", func=rule_gcd_implies_divides_right),
    Rule(name="even_implies_divides_2", func=rule_even_implies_divides_2),
]