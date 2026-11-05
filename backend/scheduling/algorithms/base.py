"""The interface every generation algorithm implements."""
import random
from dataclasses import dataclass
from typing import Protocol

from scheduling.model import Problem, Solution


class SolveFn(Protocol):
    def __call__(self, problem: Problem, rng: random.Random, time_limit_s: float | None) -> Solution: ...


@dataclass(frozen=True)
class Algorithm:
    name: str
    version: int
    solve: SolveFn
    deterministic: bool  # deterministic algorithms run once, the others once per seed
    description: str

    @property
    def key(self) -> str:
        return f"{self.name}@{self.version}"
