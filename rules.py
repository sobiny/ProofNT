from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from fact import Fact


@dataclass
class DerivedFact:
    """
    一条规则应用后得到的一个候选新事实。

    字段说明：
    - fact: 推出来的新事实
    - parent_facts: 它依赖哪些旧事实
    - note: 一句备注，便于解释
    """
    fact: Fact
    parent_facts: list[Fact]
    note: str = ""


# 规则函数类型：
# 输入：当前全部事实 list[Fact]
# 输出：若干 DerivedFact
RuleFunc = Callable[[list[Fact]], Iterable[DerivedFact]]


@dataclass
class Rule:
    """
    一条推理规则。

    - name: 规则名
    - func: 实际执行逻辑
    - generated: 是否属于“生成型规则”
      以后可用它来区分：
      - 基础闭包规则（自动跑）
      - 搜索型规则（需要启发式控制）
    - weight: 规则代价，后面搜索时可用
    """
    name: str
    func: RuleFunc
    generated: bool = False
    weight: int = 1