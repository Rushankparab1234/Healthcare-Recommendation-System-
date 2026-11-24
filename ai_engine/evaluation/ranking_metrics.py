import math
from collections.abc import Iterable


def precision_at_k(recommended: Iterable[str], relevant: set[str], k: int) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    top_k = list(recommended)[:k]
    return sum(item in relevant for item in top_k) / k


def recall_at_k(recommended: Iterable[str], relevant: set[str], k: int) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    if not relevant:
        return 0.0
    top_k = list(recommended)[:k]
    return sum(item in relevant for item in top_k) / len(relevant)


def ndcg_at_k(recommended: Iterable[str], relevant: set[str], k: int) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    top_k = list(recommended)[:k]
    dcg = sum(
        (1.0 if item in relevant else 0.0) / math.log2(rank + 2)
        for rank, item in enumerate(top_k)
    )
    ideal_count = min(len(relevant), k)
    ideal_dcg = sum(1.0 / math.log2(rank + 2) for rank in range(ideal_count))
    return dcg / ideal_dcg if ideal_dcg else 0.0


def map_at_k(recommended: Iterable[str], relevant: set[str], k: int) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    if not relevant:
        return 0.0
    top_k = list(recommended)[:k]
    hits = 0
    total_precision = 0.0
    for rank, item in enumerate(top_k, start=1):
        if item in relevant:
            hits += 1
            total_precision += hits / rank
    return total_precision / min(len(relevant), k)


def coverage_at_k(rankings: Iterable[Iterable[str]], catalog_size: int, k: int) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    if catalog_size <= 0:
        return 0.0
    covered = {item for ranking in rankings for item in list(ranking)[:k]}
    return len(covered) / catalog_size
