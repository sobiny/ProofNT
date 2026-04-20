from __future__ import annotations

"""
rule_engine.py

这个文件负责“规则引擎”的核心逻辑。

当前版本采用的是最基础的“前向推理”模式：

1. 从当前已知事实出发
2. 对每条规则进行尝试
3. 收集所有候选新事实
4. 去掉已经存在的事实
5. 把真正的新事实加入证明图
6. 重复上述过程，直到：
   - 没有新事实产生，或者
   - 达到最大轮数 max_rounds

这是一种很经典、很适合第一版原型的做法。

-----------------------------------
为什么不用更复杂的搜索？
-----------------------------------
因为你当前最需要验证的是：

- 表达系统是否合理
- 事实系统是否合理
- 规则系统是否能正常产出结论
- 证明图是否能正确记录来源

等这些都稳定以后，再考虑：
- 目标驱动
- 启发式规则选择
- 搜索剪枝
- 表达式深度限制
- 按题型切换策略

-----------------------------------
当前版本的特点
-----------------------------------
优点：
- 代码简单
- 调试方便
- 容易看清每一轮推理发生了什么

缺点：
- 如果规则很多，或规则过于“生成型”，容易膨胀
- 还没有做“只围绕目标证明”的控制
"""

from proof_graph import ProofGraph
from rules import Rule


class RuleEngine:
    """
    规则引擎类。

    它接收一组规则，然后对一个 ProofGraph 做前向推理。

    使用方式大致是：

        engine = RuleEngine(rules)
        engine.saturate(graph, max_rounds=10, verbose=True)

    其中：
    - rules 是你当前想启用的规则列表
    - graph 是当前证明图，里面已经装好了初始条件
    """

    def __init__(self, rules: list[Rule]) -> None:
        """
        初始化规则引擎。

        参数：
        - rules: 当前要启用的规则列表

        说明：
        这里不区分“安全规则”和“扩展规则”，
        因为这个区分是在更上层（比如 test_demo.py 或未来的 goal-driven 层）完成的。
        RuleEngine 只负责老老实实执行“你交给我的规则”。
        """
        self.rules = rules

    def saturate(
        self,
        graph: ProofGraph,
        max_rounds: int = 20,
        verbose: bool = False,
    ) -> None:
        """
        对证明图做“饱和推理”。

        参数：
        - graph: 当前证明图
        - max_rounds: 最多做多少轮推理
        - verbose: 是否打印调试信息

        什么时候停止？
        - 如果某一轮没有新增事实，则立即停止
        - 或者达到最大轮数 max_rounds

        为什么要加 max_rounds？
        因为有些规则会导致表达式不断变复杂，
        如果没有轮数限制，系统可能会非常慢，甚至看起来像“卡死”。

        verbose=True 时会打印：
        - 每轮新增了多少事实
        - 每条新事实由哪条规则得到
        """
        for round_index in range(max_rounds):
            new_count = self._one_round(graph, verbose=verbose)

            if verbose:
                print(f"[规则引擎] 第 {round_index + 1} 轮结束，本轮新增事实数：{new_count}")

            # 如果这一轮没有任何新增事实，就说明当前规则集下已经“推满了”
            if new_count == 0:
                if verbose:
                    print("[规则引擎] 没有新事实产生，停止推理。")
                break

    def _one_round(self, graph: ProofGraph, verbose: bool = False) -> int:
        """
        执行一轮推理。

        返回值：
        - 本轮真正加入证明图的新事实数量

        当前采用“两阶段”做法：

        第一阶段：收集候选事实
        - 遍历所有规则
        - 让每条规则基于当前已有事实生成候选结果
        - 暂时不立刻往 graph 里加

        第二阶段：统一加入
        - 去重
        - 给每个新事实找到父节点编号
        - 写入 graph

        -----------------------------------
        为什么不边生成边加入？
        -----------------------------------
        因为如果“边跑规则边加入事实”，
        同一轮后面的规则就可能看到前面刚生成的新事实，
        这样会让“一轮”的语义变得不清楚。

        当前的设计更稳定：
        - 一轮内只基于“轮开始时已有的事实”做推理
        - 新事实统一放到轮末加入

        这样更好调试，也更容易控制爆炸。
        """
        # 当前轮开始时的全部事实
        facts = graph.all_facts()

        # pending 用来暂存本轮所有候选新事实
        # 里面每项是 (rule_name, derived_item)
        pending = []

        # 用于本轮内部去重
        # 防止不同规则，或者同一规则不同配对方式，
        # 生成完全相同的事实，导致 pending 太臃肿
        pending_keys = set()

        # --------------------------------------------------
        # 第一阶段：遍历规则，收集候选新事实
        # --------------------------------------------------
        for rule in self.rules:
            # rule.func(facts) 返回的是一个可迭代对象，里面每项通常是 DerivedFact
            derived_items = list(rule.func(facts))

            for item in derived_items:
                fact = item.fact.canonical()
                fact_key = fact.key()

                # 如果证明图里已经有这个事实，就不用再收集
                if graph.has_fact(fact):
                    continue

                # 如果本轮 pending 中已经有这个事实，也不用重复收集
                if fact_key in pending_keys:
                    continue

                pending.append((rule.name, item))
                pending_keys.add(fact_key)

        # --------------------------------------------------
        # 第二阶段：把候选事实真正加入 graph
        # --------------------------------------------------
        new_count = 0

        for rule_name, item in pending:
            fact = item.fact.canonical()

            # 再检查一次，防止前面 pending 里不同位置出现逻辑竞争
            if graph.has_fact(fact):
                continue

            # 找出这条新事实对应的父节点 id
            parent_ids = []
            for parent_fact in item.parent_facts:
                pid = graph.get_node_id(parent_fact)
                if pid is not None:
                    parent_ids.append(pid)

            graph.add_fact(
                fact=fact,
                rule_name=rule_name,
                parents=parent_ids,
                note=item.note,
            )
            new_count += 1

            if verbose:
                print(f"  + 新事实：{fact}")
                print(f"    来源规则：{rule_name}")
                if parent_ids:
                    print(f"    父节点：{parent_ids}")
                if item.note:
                    print(f"    说明：{item.note}")

        return new_count