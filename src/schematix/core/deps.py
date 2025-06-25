# ~/schematix/src/schematix/core/deps.py
from __future__ import annotations
import typing as t, collections as co

if t.TYPE_CHECKING:
    from schematix.core.bases.field import BaseField


class DependencyResolver:
    """Handles topological sorting of field dependencies."""

    def __init__(
        self,
        fields: t.Dict[str, 'BaseField']
    ) -> None:
        """Initialize with field dictionary."""
        self.fields = fields
        self._validatedependencies()

    def _validatedependencies(self) -> None:
        """Validate all dependencies exist"""
        for name, field in self.fields.items():
            if field.conditional:
                for dep in (field.dependencies or []):
                    if dep not in self.fields:
                        raise ValueError(f"Field '{name}' is missing dependency: '{dep}'")

    def _detectcycle(self) -> t.List[str]:
        """Detect and return a cycle in the dependency graph."""
        visited = set()
        stack = set()

        def dfs(node: str, path: t.List[str]) -> t.Optional[t.List[str]]:
            """Depth-First Search"""
            if node in stack:
                # found cycle, return cycle path
                start = path.index(node)
                return path[start:] + [node]

            if node in visited:
                return None

            visited.add(node)
            stack.add(node)
            path.append(node)

            field = self.fields[node]

            if field.conditional:
                for dep in (field.dependencies or []):
                    cycle = dfs(dep, path[:])
                    if cycle:
                        return cycle

            stack.remove(node)
            return None

        for name in self.fields:
            if name not in visited:
                cycle = dfs(name, [])
                if cycle:
                    return cycle

        return ["unknown cycle"]

    def resolveorder(self) -> t.List[str]:
        """Return field names in dependency-safe execution order using topological sorting."""
        # dependency graph
        graph = co.defaultdict(list) # node -> list of nodes that depend
        degree = co.defaultdict(int) # node -> number of dependencies

        # initialize all nodes
        for name in self.fields:
            degree[name] = 0

        # build graph
        for name, field in self.fields.items():
            if field.conditional:
                for dep in (field.dependencies or []):
                    graph[dep].append(name)
                    degree[name] += 1

        # kahns algorithm
        q = co.deque([node for node in degree if degree[node] == 0])
        result = []

        while q:
            current = q.popleft()
            result.append(current)

            # remove edges
            for neighbor in graph[current]:
                degree[neighbor] -= 1
                if degree[neighbor] == 0:
                    q.append(neighbor)

        # check for cycles
        if len(result) != len(self.fields):
            cycle = self._detectcycle()
            raise ValueError(f"Circular dependency detected: {' -> '.join(cycle)}")

        return result
