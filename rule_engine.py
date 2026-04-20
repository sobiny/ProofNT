from __future__ import annotations

from proof_graph import ProofGraph
from rules import Rule


class RuleEngine:
    """
    规则引擎。

    当前版本是最基础的“前向推理”：
    - 从当前事实出发
    - 反复应用所有规则
    - 直到没有新事实为止
    """

    def __init__(self, rules: list[Rule]) -> None:
        self.rules = rules

    def saturate(self, graph: ProofGraph, max_rounds: int = 20) -> None:
        """
        让证明图做“饱和推理”。

        参数：
        - graph: 当前证明图
        - max_rounds: 最多跑多少轮，防止某些生成规则导致死循环或过度膨胀

        说明：
        一轮的含义是：把当前所有规则都扫一遍。
        如果某一轮没有产生任何新事实，就提前停止。
        """
        for round_index in range(max_rounds):
            new_count = self._one_round(graph)
            if new_count == 0:
                break

    def _one_round(self, graph: ProofGraph) -> int:
        """
        执行一轮规则扫描。

        返回本轮新增事实数量。
        """
        facts = graph.all_facts()
        new_count = 0

        for rule in self.rules:
            derived_items = list(rule.func(facts))

            for item in derived_items:
                if graph.has_fact(item.fact):
                    # 已有事实，不重复添加
                    continue

                # 把 parent_facts 转成 parent_ids
                parent_ids = []
                for pf in item.parent_facts:
                    pid = graph.get_node_id(pf)
                    if pid is not None:
                        parent_ids.append(pid)

                graph.add_fact(
                    fact=item.fact,
                    rule_name=rule.name,
                    parents=parent_ids,
                    note=item.note,
                )
                new_count += 1

        return new_count