from expr import Var, Const, Add, Mul, Sub
from fact import Congruent, Divides, Coprime, Even
from proof_graph import ProofGraph
from rule_engine import RuleEngine
from builtin_rules import SAFE_RULES, EXPANSION_RULES
from formatter_nt import print_all_facts, print_trace


def run_demo(
    title: str,
    graph: ProofGraph,
    rules,
    goals: list,
    max_rounds: int = 10,
    verbose: bool = False,
):
    """
    一个统一的 demo 运行函数。

    参数：
    - title: demo 标题
    - graph: 已经写入初始条件的证明图
    - rules: 当前 demo 要启用的规则列表
    - goals: 需要检查 / 回溯的目标列表
    - max_rounds: 最多推理多少轮
    - verbose: 是否打印调试信息

    说明：
    - 对安全规则，max_rounds 可以大一点
    - 对扩展规则，通常设成 1 就够了
    """
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    engine = RuleEngine(rules)
    engine.saturate(graph, max_rounds=max_rounds, verbose=verbose)

    print_all_facts(graph)
    print()

    for goal in goals:
        print_trace(graph, goal)
        print()


def demo_1_congruence_to_divides():
    """
    Demo 1：
    已知 a ≡ b (mod m)
    推出 m | (a - b)
    """
    a = Var("a")
    b = Var("b")
    m = Var("m")

    graph = ProofGraph()
    graph.add_fact(
        Congruent(a, b, m),
        rule_name="assumption",
        note="题目已知条件：a ≡ b (mod m)。",
    )

    goal = Divides(m, Sub(a, b).canonical())

    run_demo(
        title="Demo 1：由同余推出整除",
        graph=graph,
        rules=SAFE_RULES,
        goals=[goal],
        max_rounds=10,
    )


def demo_2_coprime_to_gcd_to_divides():
    """
    Demo 2：
    已知 Coprime(a, b)
    推出 gcd(a, b)=1，再推出 1|a 和 1|b
    """
    a = Var("a")
    b = Var("b")

    graph = ProofGraph()
    graph.add_fact(
        Coprime(a, b),
        rule_name="assumption",
        note="题目已知条件：a 与 b 互素。",
    )

    goal1 = Divides(Const(1), a)
    goal2 = Divides(Const(1), b)

    run_demo(
        title="Demo 2：由互素推出 gcd=1，再推出整除",
        graph=graph,
        rules=SAFE_RULES,
        goals=[goal1, goal2],
        max_rounds=10,
    )


def demo_3_even_to_divides():
    """
    Demo 3：
    已知 Even(x)
    推出 2 | x
    """
    x = Var("x")

    graph = ProofGraph()
    graph.add_fact(
        Even(x),
        rule_name="assumption",
        note="题目已知条件：x 是偶数。",
    )

    goal = Divides(Const(2), x)

    run_demo(
        title="Demo 3：由偶数推出被 2 整除",
        graph=graph,
        rules=SAFE_RULES,
        goals=[goal],
        max_rounds=10,
    )


def demo_4_congruence_add():
    """
    Demo 4：
    已知 a ≡ b (mod m), c ≡ d (mod m)
    推出 a+c ≡ b+d (mod m)

    这里只验证“一步规则”是否能推出，
    所以只跑 1 轮。
    """
    a = Var("a")
    b = Var("b")
    c = Var("c")
    d = Var("d")
    m = Var("m")

    graph = ProofGraph()
    graph.add_fact(Congruent(a, b, m), rule_name="assumption", note="已知第一组同余。")
    graph.add_fact(Congruent(c, d, m), rule_name="assumption", note="已知第二组同余。")

    goal = Congruent(
        Add(a, c).canonical(),
        Add(b, d).canonical(),
        m,
    )

    rules = SAFE_RULES + [EXPANSION_RULES["congruence_add"]]

    run_demo(
        title="Demo 4：同余的加法相容性",
        graph=graph,
        rules=rules,
        goals=[goal],
        max_rounds=1,
    )


def demo_5_congruence_sub():
    """
    Demo 5：
    已知 a ≡ b (mod m), c ≡ d (mod m)
    推出 a-c ≡ b-d (mod m)

    同样只验证一步规则，所以只跑 1 轮。
    """
    a = Var("a")
    b = Var("b")
    c = Var("c")
    d = Var("d")
    m = Var("m")

    graph = ProofGraph()
    graph.add_fact(Congruent(a, b, m), rule_name="assumption", note="已知第一组同余。")
    graph.add_fact(Congruent(c, d, m), rule_name="assumption", note="已知第二组同余。")

    goal = Congruent(
        Sub(a, c).canonical(),
        Sub(b, d).canonical(),
        m,
    )

    rules = SAFE_RULES + [EXPANSION_RULES["congruence_sub"]]

    run_demo(
        title="Demo 5：同余的减法相容性",
        graph=graph,
        rules=rules,
        goals=[goal],
        max_rounds=1,
    )


def demo_6_congruence_mul():
    """
    Demo 6：
    已知 a ≡ b (mod m), c ≡ d (mod m)
    推出 ac ≡ bd (mod m)

    这里只验证一步规则，所以只跑 1 轮。
    """
    a = Var("a")
    b = Var("b")
    c = Var("c")
    d = Var("d")
    m = Var("m")

    graph = ProofGraph()
    graph.add_fact(Congruent(a, b, m), rule_name="assumption", note="已知第一组同余。")
    graph.add_fact(Congruent(c, d, m), rule_name="assumption", note="已知第二组同余。")

    goal = Congruent(
        Mul(a, c).canonical(),
        Mul(b, d).canonical(),
        m,
    )

    rules = SAFE_RULES + [EXPANSION_RULES["congruence_mul"]]

    run_demo(
        title="Demo 6：同余的乘法相容性",
        graph=graph,
        rules=rules,
        goals=[goal],
        max_rounds=1,
    )


def demo_7_divides_add_sub():
    """
    Demo 7：
    已知 d|a, d|b
    推出 d|(a+b), d|(a-b)

    这里只验证一步规则，所以只跑 1 轮。
    """
    d = Var("d")
    a = Var("a")
    b = Var("b")

    graph = ProofGraph()
    graph.add_fact(Divides(d, a), rule_name="assumption", note="题目已知 d | a。")
    graph.add_fact(Divides(d, b), rule_name="assumption", note="题目已知 d | b。")

    goal1 = Divides(d, Add(a, b).canonical())
    goal2 = Divides(d, Sub(a, b).canonical())

    rules = SAFE_RULES + [
        EXPANSION_RULES["divides_add"],
        EXPANSION_RULES["divides_sub"],
    ]

    run_demo(
        title="Demo 7：整除对加减法的封闭性",
        graph=graph,
        rules=rules,
        goals=[goal1, goal2],
        max_rounds=1,
    )


def demo_8_square_congruence():
    """
    Demo 8：
    已知 a ≡ b (mod m)
    推出 a*a ≡ b*b (mod m)

    这是通过 congruence_mul 与自身配对得到的。
    为了防止继续膨胀，只跑 1 轮。
    """
    a = Var("a")
    b = Var("b")
    m = Var("m")

    graph = ProofGraph()
    graph.add_fact(Congruent(a, b, m), rule_name="assumption", note="题目已知 a ≡ b (mod m)。")

    goal = Congruent(
        Mul(a, a).canonical(),
        Mul(b, b).canonical(),
        m,
    )

    rules = SAFE_RULES + [EXPANSION_RULES["congruence_mul"]]

    run_demo(
        title="Demo 8：由同余推出平方同余",
        graph=graph,
        rules=rules,
        goals=[goal],
        max_rounds=1,
    )


def demo_9_explicit_rule_choice():
    """
    Demo 9：
    演示“按目标精确选规则”。

    当前目标只是：
        a ≡ b (mod m) => m | (a-b)

    所以连 SAFE_RULES 全开都不需要，
    只用一条 congruence_to_divides 就够了。
    """
    a = Var("a")
    b = Var("b")
    m = Var("m")

    graph = ProofGraph()
    graph.add_fact(
        Congruent(a, b, m),
        rule_name="assumption",
        note="题目已知 a ≡ b (mod m)。",
    )

    goal = Divides(m, Sub(a, b).canonical())

    rules = [
        rule for rule in SAFE_RULES
        if rule.name == "congruence_to_divides"
    ]

    run_demo(
        title="Demo 9：按目标精确选择规则",
        graph=graph,
        rules=rules,
        goals=[goal],
        max_rounds=1,
    )


if __name__ == "__main__":
    # 安全规则 demo
    demo_1_congruence_to_divides()
    demo_2_coprime_to_gcd_to_divides()
    demo_3_even_to_divides()

    # 扩展规则 demo（统一只跑 1 轮）
    demo_4_congruence_add()
    demo_5_congruence_sub()
    demo_6_congruence_mul()
    demo_7_divides_add_sub()
    demo_8_square_congruence()

    # 精确选规则 demo
    demo_9_explicit_rule_choice()