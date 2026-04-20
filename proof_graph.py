from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from fact import Fact


@dataclass
class ProofNode:
    """
    证明图中的一个节点。

    字段说明：
    - id: 节点编号
    - fact: 这个节点对应的数学事实
    - rule_name: 这个事实由哪条规则得到；若是初始条件，可写 "assumption"
    - parents: 这个事实依赖哪些父节点编号
    - note: 附加说明，方便以后输出更可读的证明
    """
    id: int
    fact: Fact
    rule_name: Optional[str]
    parents: List[int] = field(default_factory=list)
    note: str = ""


class ProofGraph:
    """
    证明图 / 事实库。

    它的作用相当于：
    1. 存储所有已经知道的事实
    2. 支持快速查询某事实是否已经存在
    3. 记录每个事实从哪里来
    4. 最后支持回溯出某个目标事实的依赖链
    """

    def __init__(self) -> None:
        # 下一个节点编号
        self._next_id = 1

        # id -> ProofNode
        self.nodes_by_id: Dict[int, ProofNode] = {}

        # fact.key() -> node_id
        # 用于快速判断某个事实是否已存在
        self.fact_index: Dict[tuple, int] = {}

    def has_fact(self, fact: Fact) -> bool:
        """
        判断当前事实库中是否已经有该事实。
        """
        return fact.canonical().key() in self.fact_index

    def get_node_id(self, fact: Fact) -> Optional[int]:
        """
        获取某个事实对应的节点 id。
        如果不存在，返回 None。
        """
        return self.fact_index.get(fact.canonical().key())

    def add_fact(
        self,
        fact: Fact,
        rule_name: Optional[str],
        parents: list[int] | None = None,
        note: str = "",
    ) -> int:
        """
        向证明图中添加一个新事实。

        如果事实已经存在，则直接返回已有节点 id，不重复添加。
        """
        fact = fact.canonical()
        key = fact.key()

        if key in self.fact_index:
            return self.fact_index[key]

        node_id = self._next_id
        self._next_id += 1

        node = ProofNode(
            id=node_id,
            fact=fact,
            rule_name=rule_name,
            parents=parents or [],
            note=note,
        )
        self.nodes_by_id[node_id] = node
        self.fact_index[key] = node_id
        return node_id

    def all_nodes(self) -> list[ProofNode]:
        """
        按 id 从小到大返回所有节点。
        """
        return [self.nodes_by_id[k] for k in sorted(self.nodes_by_id)]

    def all_facts(self) -> list[Fact]:
        """
        只返回当前所有事实。
        """
        return [node.fact for node in self.all_nodes()]

    def traceback(self, fact: Fact) -> list[ProofNode]:
        """
        回溯某个目标事实的证明链。

        返回的是“该事实所依赖的所有节点”，并按一个可读顺序排列：
        先父节点，再子节点。

        这对输出证明很有用。
        """
        fact = fact.canonical()
        node_id = self.fact_index.get(fact.key())
        if node_id is None:
            return []

        visited = set()
        order = []

        def dfs(nid: int) -> None:
            if nid in visited:
                return
            visited.add(nid)
            node = self.nodes_by_id[nid]
            for p in node.parents:
                dfs(p)
            order.append(node)

        dfs(node_id)
        return order