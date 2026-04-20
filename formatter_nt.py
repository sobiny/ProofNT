from __future__ import annotations

from fact import Fact
from proof_graph import ProofGraph, ProofNode


def print_all_facts(graph: ProofGraph) -> None:
    """
    打印当前证明图中的所有节点。
    适合调试时看系统到底推出了什么。
    """
    print("=== All facts in proof graph ===")
    for node in graph.all_nodes():
        print(
            f"[{node.id}] {node.fact} "
            f"(rule={node.rule_name}, parents={node.parents})"
        )
        if node.note:
            print(f"     note: {node.note}")


def print_trace(graph: ProofGraph, goal: Fact) -> None:
    """
    打印某个目标事实的回溯证明链。

    如果目标不存在，则提示未找到。
    """
    nodes = graph.traceback(goal)
    if not nodes:
        print(f"Goal not found: {goal}")
        return

    print(f"=== Traceback for goal: {goal} ===")
    for node in nodes:
        print(
            f"[{node.id}] {node.fact} "
            f"<- {node.rule_name if node.rule_name else 'unknown'} "
            f"from {node.parents}"
        )
        if node.note:
            print(f"     note: {node.note}")