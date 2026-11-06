"""Registry of generation algorithms, all behind the same interface (`base.Algorithm`).

A new version of an algorithm is added next to the previous one (`greedy@1`, `greedy@2`), never
in place of it: the benchmark keeps comparing the whole history.
"""
from scheduling.algorithms import greedy, random_baseline
from scheduling.algorithms.base import Algorithm

ALGORITHMS: dict[str, Algorithm] = {a.key: a for a in (random_baseline.ALGORITHM, greedy.ALGORITHM)}
