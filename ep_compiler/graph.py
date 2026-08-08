"""DAG cycle detector for .enx and .ei dependency resolution.
Prevents infinite recursion from circular root/order references."""
import os


class CircularReferenceError(Exception):
    """Raised when a circular dependency is detected in .enx or .ei files."""

    def __init__(self, path, chain):
        self.path = path
        self.chain = chain
        chain_str = " \u2192 ".join(chain)
        super().__init__(f"Circular reference detected: {chain_str}")


class CompilationGraph:
    """Tracks visited paths during compilation to detect cycles."""
    def __init__(self):
        self._visited = set()
        self._stack = []

    def enter(self, path):
        """Mark path as entered. Raises CircularReferenceError if already in stack."""
        abspath = os.path.normpath(os.path.abspath(path))
        if abspath in self._stack:
            chain = [str(p) for p in self._stack] + [str(abspath)]
            raise CircularReferenceError(abspath, chain)
        self._visited.add(abspath)
        self._stack.append(abspath)

    def exit(self):
        """Pop the most recent path from the stack."""
        if self._stack:
            self._stack.pop()

    def reset(self):
        """Clear all state for a fresh compilation run."""
        self._visited.clear()
        self._stack.clear()

    @property
    def current_chain(self):
        return [str(p) for p in self._stack]
