from __future__ import annotations
from collections import defaultdict
from typing import Any, Iterable, Optional, overload, Tuple, Union

VarValPair = Tuple[Any, Any]


class FactSet:
    facts: dict[Any, set[Any]]

    def __init__(
        self,
        facts: Union[FactSet, dict[Any, set[Any]], Iterable[VarValPair], None] = None,
    ) -> None:
        self.facts = defaultdict(set)
        if facts is None:
            return
        if isinstance(facts, (FactSet, dict)):
            self.union(facts)
        else:
            self.add(facts)

    def __repr__(self) -> str:
        return f"FactSet({repr(dict(self.facts))})"

    def __getitem__(self, key: Any) -> set[Any]:
        return self.facts.get(key, set())

    def __eq__(self, other: Optional[FactSet]) -> bool:
        if other is None:
            return False
        return self.facts == other.facts

    def __len__(self) -> int:
        return len(self.facts)

    def __iter__(self):
        return iter(self.facts.items())

    @property
    def variables(self) -> list[Any]:
        return [key for key, values in self.facts.items() if len(values) > 0]

    @property
    def n_facts(self) -> int:
        return sum([len(values) for _, values in self])

    @overload
    def add(self, var: Any, val: Any) -> None:
        """Add a new fact to the FactSet"""
        ...

    @overload
    def add(self, facts_iterable: Iterable[VarValPair]) -> None:
        """Add a list of facts to the FactSet"""
        ...

    def add(
        self,
        facts_iterable_or_var: Union[Any, Iterable[VarValPair]],
        val: Optional[Any] = None,
    ) -> None:
        if val is None:
            facts_iterable = facts_iterable_or_var
            for var, val in facts_iterable:
                self.add(var, val)
        else:
            var = facts_iterable_or_var
            self.facts[var].add(val)

    @overload
    def union(self, other_facts: FactSet | dict[Any, set[Any]]) -> None:
        """Take the in-place union of the FactSet with the specified additional facts"""
        ...

    @overload
    def union(self, var: Any, values: set[Any]) -> None:
        """Add the specified variable values to the FactSet"""
        ...

    def union(
        self,
        other_facts_or_var: FactSet | dict[Any, set[Any]] | Any,
        values: set[Any] | None = None,
    ) -> None:
        if values is None:
            other_facts = other_facts_or_var
            if isinstance(other_facts, FactSet):
                other_facts = other_facts.facts
            for var, values in other_facts.items():
                self.union(var, values)
        else:
            var = other_facts_or_var
            self.facts[var] = self.facts[var].union(values)

    @overload
    def difference(self, other_facts: FactSet | dict) -> None:
        """Remove all facts from this FactSet that appear in the other FactSet."""
        ...

    @overload
    def difference(self, var: Any, values: set[Any]) -> None:
        """Remove the specified variable values from the FactSet if present."""
        ...

    def difference(
        self,
        other_facts_or_var: FactSet | Any,
        values: set[Any] | None = None,
    ) -> None:
        if values is None:
            other_facts = other_facts_or_var
            if isinstance(other_facts, FactSet):
                other_facts = other_facts.facts
            for var, values in other_facts.items():
                self.difference(var, values)
        else:
            var = other_facts_or_var
            if var in self.variables:
                self.facts[var] = self.facts[var].difference(values)
                if not self.facts[var]:
                    del self.facts[var]

    def __contains__(self, item: VarValPair | FactSet) -> bool:
        """Check if a (var, val) pair is an element of the FactSet, or if another
        FactSet is a subset of this one"""
        if isinstance(item, FactSet):
            other_facts = item
            for var, values in other_facts:
                if any([(var, val) not in self for val in values]):
                    return False
            return True
        else:
            var, val = item
            if var not in self.facts:
                return False
            values = self.facts[var]
            return val in values
