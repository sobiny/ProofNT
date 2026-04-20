from __future__ import annotations

"""
builtin_rules.py

这个文件放项目的第一批内置规则。

当前设计思路：
1. 把规则分成“安全规则”和“扩展规则”
2. 安全规则可以默认自动跑
3. 扩展规则必须受限制：
   - 限制表达式复杂度
   - 在 demo 里限制推理轮数
否则很容易导致表达式无限膨胀
"""

from expr import Add, Mul, Sub, Const
from fact import Congruent, Coprime, Divides, Even, GCD
from rules import DerivedFact, Rule


# ============================================================
# 一、表达式复杂度辅助函数
# ============================================================

def expr_size(expr) -> int:
    """
    计算表达式的“大小”（节点总数）。

    例如：
    - a 的大小约为 1
    - a+b 的大小约为 3
    - (a+b)+c 的大小会更大

    用途：
    - 限制扩展规则不要生成越来越巨大的表达式
    """
    return 1 + sum(expr_size(ch) for ch in expr.children())


def expr_depth(expr) -> int:
    """
    计算表达式深度。

    叶子节点（变量、常数）深度记为 1。
    """
    children = expr.children()
    if not children:
        return 1
    return 1 + max(expr_depth(ch) for ch in children)


def is_simple_expr(expr, max_size: int = 3, max_depth: int = 2) -> bool:
    """
    判断一个表达式是否算“简单”。

    这是给扩展规则用的门槛：
    只有比较简单的表达式才允许继续参加扩展规则，
    避免系统把自己生成的大式子再拿去继续扩展。
    """
    return expr_size(expr) <= max_size and expr_depth(expr) <= max_depth


# ============================================================
# 二、同余相关规则
# ============================================================

def rule_congruence_to_divides(facts):
    """
    规则：
        a ≡ b (mod m)  =>  m | (a - b)

    这是同余定义最基础、最常用的方向。
    属于安全规则。
    """
    for f in facts:
        if isinstance(f, Congruent):
            yield DerivedFact(
                fact=Divides(f.modulus, Sub(f.left, f.right).canonical()),
                parent_facts=[f],
                note="由同余定义可得：模数整除两边之差。",
            )


def rule_congruence_add(facts):
    """
    规则：
        a ≡ b (mod m), c ≡ d (mod m)
        =>
        a + c ≡ b + d (mod m)

    这是扩展规则，因此必须限制复杂度。
    """
    congruences = [f for f in facts if isinstance(f, Congruent)]

    MAX_INPUT_SIZE = 3
    MAX_INPUT_DEPTH = 2
    MAX_OUTPUT_SIZE = 7
    MAX_OUTPUT_DEPTH = 4

    for f1 in congruences:
        for f2 in congruences:
            if f1.modulus.canonical() != f2.modulus.canonical():
                continue

            # 只允许较简单的输入参与
            if not is_simple_expr(f1.left, MAX_INPUT_SIZE, MAX_INPUT_DEPTH):
                continue
            if not is_simple_expr(f1.right, MAX_INPUT_SIZE, MAX_INPUT_DEPTH):
                continue
            if not is_simple_expr(f2.left, MAX_INPUT_SIZE, MAX_INPUT_DEPTH):
                continue
            if not is_simple_expr(f2.right, MAX_INPUT_SIZE, MAX_INPUT_DEPTH):
                continue

            left_expr = Add(f1.left, f2.left).canonical()
            right_expr = Add(f1.right, f2.right).canonical()

            # 输出复杂度限制
            if expr_size(left_expr) > MAX_OUTPUT_SIZE or expr_depth(left_expr) > MAX_OUTPUT_DEPTH:
                continue
            if expr_size(right_expr) > MAX_OUTPUT_SIZE or expr_depth(right_expr) > MAX_OUTPUT_DEPTH:
                continue

            yield DerivedFact(
                fact=Congruent(left_expr, right_expr, f1.modulus),
                parent_facts=[f1, f2],
                note="同余在加法下保持不变。",
            )


def rule_congruence_sub(facts):
    """
    规则：
        a ≡ b (mod m), c ≡ d (mod m)
        =>
        a - c ≡ b - d (mod m)

    这是扩展规则，因此必须限制复杂度。
    """
    congruences = [f for f in facts if isinstance(f, Congruent)]

    MAX_INPUT_SIZE = 3
    MAX_INPUT_DEPTH = 2
    MAX_OUTPUT_SIZE = 7
    MAX_OUTPUT_DEPTH = 4

    for f1 in congruences:
        for f2 in congruences:
            if f1.modulus.canonical() != f2.modulus.canonical():
                continue

            if not is_simple_expr(f1.left, MAX_INPUT_SIZE, MAX_INPUT_DEPTH):
                continue
            if not is_simple_expr(f1.right, MAX_INPUT_SIZE, MAX_INPUT_DEPTH):
                continue
            if not is_simple_expr(f2.left, MAX_INPUT_SIZE, MAX_INPUT_DEPTH):
                continue
            if not is_simple_expr(f2.right, MAX_INPUT_SIZE, MAX_INPUT_DEPTH):
                continue

            left_expr = Sub(f1.left, f2.left).canonical()
            right_expr = Sub(f1.right, f2.right).canonical()

            if expr_size(left_expr) > MAX_OUTPUT_SIZE or expr_depth(left_expr) > MAX_OUTPUT_DEPTH:
                continue
            if expr_size(right_expr) > MAX_OUTPUT_SIZE or expr_depth(right_expr) > MAX_OUTPUT_DEPTH:
                continue

            yield DerivedFact(
                fact=Congruent(left_expr, right_expr, f1.modulus),
                parent_facts=[f1, f2],
                note="同余在减法下保持不变。",
            )


def rule_congruence_mul(facts):
    """
    规则：
        a ≡ b (mod m), c ≡ d (mod m)
        =>
        ac ≡ bd (mod m)

    这是扩展规则，而且风险最大之一。
    因为同一条事实和自己配对后，很容易产生平方、四次方等膨胀链。
    所以这里要严格限制输入复杂度。
    """
    congruences = [f for f in facts if isinstance(f, Congruent)]

    MAX_INPUT_SIZE = 2
    MAX_INPUT_DEPTH = 1
    MAX_OUTPUT_SIZE = 5
    MAX_OUTPUT_DEPTH = 3

    for f1 in congruences:
        for f2 in congruences:
            if f1.modulus.canonical() != f2.modulus.canonical():
                continue

            if not is_simple_expr(f1.left, MAX_INPUT_SIZE, MAX_INPUT_DEPTH):
                continue
            if not is_simple_expr(f1.right, MAX_INPUT_SIZE, MAX_INPUT_DEPTH):
                continue
            if not is_simple_expr(f2.left, MAX_INPUT_SIZE, MAX_INPUT_DEPTH):
                continue
            if not is_simple_expr(f2.right, MAX_INPUT_SIZE, MAX_INPUT_DEPTH):
                continue

            left_expr = Mul(f1.left, f2.left).canonical()
            right_expr = Mul(f1.right, f2.right).canonical()

            if expr_size(left_expr) > MAX_OUTPUT_SIZE or expr_depth(left_expr) > MAX_OUTPUT_DEPTH:
                continue
            if expr_size(right_expr) > MAX_OUTPUT_SIZE or expr_depth(right_expr) > MAX_OUTPUT_DEPTH:
                continue

            yield DerivedFact(
                fact=Congruent(left_expr, right_expr, f1.modulus),
                parent_facts=[f1, f2],
                note="同余在乘法下保持不变。",
            )


# ============================================================
# 三、整除相关规则
# ============================================================

def rule_divides_transitive(facts):
    """
    规则：
        a | b, b | c  =>  a | c

    这是安全规则。
    """
    divides_facts = [f for f in facts if isinstance(f, Divides)]

    for f1 in divides_facts:
        for f2 in divides_facts:
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

    扩展规则，需要限制复杂度。
    """
    divides_facts = [f for f in facts if isinstance(f, Divides)]

    MAX_TARGET_SIZE = 3
    MAX_TARGET_DEPTH = 2
    MAX_OUTPUT_SIZE = 7
    MAX_OUTPUT_DEPTH = 4

    for f1 in divides_facts:
        for f2 in divides_facts:
            if f1.divisor.canonical() != f2.divisor.canonical():
                continue

            if not is_simple_expr(f1.target, MAX_TARGET_SIZE, MAX_TARGET_DEPTH):
                continue
            if not is_simple_expr(f2.target, MAX_TARGET_SIZE, MAX_TARGET_DEPTH):
                continue

            expr = Add(f1.target, f2.target).canonical()

            if expr_size(expr) > MAX_OUTPUT_SIZE or expr_depth(expr) > MAX_OUTPUT_DEPTH:
                continue

            yield DerivedFact(
                fact=Divides(f1.divisor, expr),
                parent_facts=[f1, f2],
                note="若同一整数分别整除两数，则也整除它们的和。",
            )


def rule_divides_sub(facts):
    """
    规则：
        d | a, d | b  =>  d | (a - b)

    扩展规则，需要限制复杂度。
    """
    divides_facts = [f for f in facts if isinstance(f, Divides)]

    MAX_TARGET_SIZE = 3
    MAX_TARGET_DEPTH = 2
    MAX_OUTPUT_SIZE = 7
    MAX_OUTPUT_DEPTH = 4

    for f1 in divides_facts:
        for f2 in divides_facts:
            if f1.divisor.canonical() != f2.divisor.canonical():
                continue

            if not is_simple_expr(f1.target, MAX_TARGET_SIZE, MAX_TARGET_DEPTH):
                continue
            if not is_simple_expr(f2.target, MAX_TARGET_SIZE, MAX_TARGET_DEPTH):
                continue

            expr = Sub(f1.target, f2.target).canonical()

            if expr_size(expr) > MAX_OUTPUT_SIZE or expr_depth(expr) > MAX_OUTPUT_DEPTH:
                continue

            yield DerivedFact(
                fact=Divides(f1.divisor, expr),
                parent_facts=[f1, f2],
                note="若同一整数分别整除两数，则也整除它们的差。",
            )


# ============================================================
# 四、互素 / 最大公因数 / 奇偶性规则
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
                note="最大公因数一定整除第一个数。",
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
                note="最大公因数一定整除第二个数。",
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
                note="偶数一定能被 2 整除。",
            )


# ============================================================
# 五、规则集合
# ============================================================

SAFE_RULES = [
    Rule(name="congruence_to_divides", func=rule_congruence_to_divides),
    Rule(name="coprime_to_gcd", func=rule_coprime_to_gcd),
    Rule(name="gcd_implies_divides_left", func=rule_gcd_implies_divides_left),
    Rule(name="gcd_implies_divides_right", func=rule_gcd_implies_divides_right),
    Rule(name="even_implies_divides_2", func=rule_even_implies_divides_2),
    Rule(name="divides_transitive", func=rule_divides_transitive),
]

EXPANSION_RULES = {
    "congruence_add": Rule(name="congruence_add", func=rule_congruence_add),
    "congruence_sub": Rule(name="congruence_sub", func=rule_congruence_sub),
    "congruence_mul": Rule(name="congruence_mul", func=rule_congruence_mul),
    "divides_add": Rule(name="divides_add", func=rule_divides_add),
    "divides_sub": Rule(name="divides_sub", func=rule_divides_sub),
}