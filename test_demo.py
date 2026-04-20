from expr import Var, Const, Add, Mul, Sub
from fact import Congruent, Divides, Coprime, Even
from proof_graph import ProofGraph
from rule_engine import RuleEngine
from builtin_rules import BUILTIN_RULES
from formatter_nt import print_all_facts, print_trace


def demo_congruence():
    """
    演示 1：
    已知 a ≡ b (mod m)
    推出 m | (a - b)
    """
    a = Var("a")
    b = Var("b")
    m = Var("m")

    graph = ProofGraph()
    graph.add_fact(Congruent(a, b, m), rule_name="assumption", note="题目已知条件。")
    print("start 1")
    engine = RuleEngine(BUILTIN_RULES)
    engine.saturate(graph)

    goal = Divides(m, Sub(a, b).canonical())
    print("start 2")
    print("\n" + "=" * 60)
    print("Demo 1: Congruence -> Divides")
    print("=" * 60)
    print_all_facts(graph)
    print()
    print_trace(graph, goal)


def demo_coprime():
    """
    演示 2：
    已知 a, b 互素
    推出 gcd(a,b)=1，再推出 1|a 和 1|b
    """
    a = Var("a")
    b = Var("b")

    graph = ProofGraph()
    graph.add_fact(Coprime(a, b), rule_name="assumption", note="题目已知 a 与 b 互素。")

    engine = RuleEngine(BUILTIN_RULES)
    engine.saturate(graph)

    goal1 = Divides(Const(1), a)
    goal2 = Divides(Const(1), b)

    print("\n" + "=" * 60)
    print("Demo 2: Coprime -> gcd=1 -> divides")
    print("=" * 60)
    print_all_facts(graph)
    print()
    print_trace(graph, goal1)
    print()
    print_trace(graph, goal2)


def demo_even():
    """
    演示 3：
    已知 x 是偶数
    推出 2|x
    """
    x = Var("x")

    graph = ProofGraph()
    graph.add_fact(Even(x), rule_name="assumption", note="题目已知 x 为偶数。")

    engine = RuleEngine(BUILTIN_RULES)
    engine.saturate(graph)

    goal = Divides(Const(2), x)

    print("\n" + "=" * 60)
    print("Demo 3: Even -> Divides(2, x)")
    print("=" * 60)
    print_all_facts(graph)
    print()
    print_trace(graph, goal)



def demo_congruence_add():
    """
    演示：
        a ≡ b (mod m)
        c ≡ d (mod m)
    推出：
        a + c ≡ b + d (mod m)
    """
    a = Var("a")
    b = Var("b")
    c = Var("c")
    d = Var("d")
    m = Var("m")

    graph = ProofGraph()
    graph.add_fact(Congruent(a, b, m), rule_name="assumption", note="已知第一组同余。")
    graph.add_fact(Congruent(c, d, m), rule_name="assumption", note="已知第二组同余。")

    engine = RuleEngine(BUILTIN_RULES)
    engine.saturate(graph)

    goal = Congruent(Add(a, c).canonical(), Add(b, d).canonical(), m)

    print("\n" + "=" * 60)
    print("Demo: congruence_add")
    print("=" * 60)
    print_all_facts(graph)
    print()
    print_trace(graph, goal)


def demo_congruence_mul():
    """
    演示：
        a ≡ b (mod m)
        c ≡ d (mod m)
    推出：
        ac ≡ bd (mod m)
    """
    a = Var("a")
    b = Var("b")
    c = Var("c")
    d = Var("d")
    m = Var("m")

    graph = ProofGraph()
    graph.add_fact(Congruent(a, b, m), rule_name="assumption")
    graph.add_fact(Congruent(c, d, m), rule_name="assumption")

    engine = RuleEngine(BUILTIN_RULES)
    engine.saturate(graph)

    goal = Congruent(Mul(a, c).canonical(), Mul(b, d).canonical(), m)

    print("\n" + "=" * 60)
    print("Demo: congruence_mul")
    print("=" * 60)
    print_all_facts(graph)
    print()
    print_trace(graph, goal)


def demo_divides_add_sub():
    """
    演示：
        d | a
        d | b
    推出：
        d | (a+b)
        d | (a-b)
    """
    d = Var("d")
    a = Var("a")
    b = Var("b")

    graph = ProofGraph()
    graph.add_fact(Divides(d, a), rule_name="assumption")
    graph.add_fact(Divides(d, b), rule_name="assumption")

    engine = RuleEngine(BUILTIN_RULES)
    engine.saturate(graph)

    goal1 = Divides(d, Add(a, b).canonical())
    goal2 = Divides(d, Sub(a, b).canonical())

    print("\n" + "=" * 60)
    print("Demo: divides_add_sub")
    print("=" * 60)
    print_all_facts(graph)
    print()
    print_trace(graph, goal1)
    print()
    print_trace(graph, goal2)


def demo_square_congruence():
    """
    演示：
        a ≡ b (mod m)
    希望系统推出：
        a*a ≡ b*b (mod m)

    这件事会通过 congruence_mul 自动得到。
    """
    a = Var("a")
    b = Var("b")
    m = Var("m")

    graph = ProofGraph()
    graph.add_fact(Congruent(a, b, m), rule_name="assumption")

    engine = RuleEngine(BUILTIN_RULES)
    engine.saturate(graph)

    goal = Congruent(Mul(a, a).canonical(), Mul(b, b).canonical(), m)

    print("\n" + "=" * 60)
    print("Demo: square congruence")
    print("=" * 60)
    print_all_facts(graph)
    print()
    print_trace(graph, goal)


if __name__ == "__main__":
    print("start")
    demo_congruence()
    demo_coprime()
    demo_even()
    demo_congruence_add()
    demo_congruence_mul()
    demo_divides_add_sub()
    demo_square_congruence()