from ai_engine.evaluation.ranking_metrics import (
    coverage_at_k,
    map_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


def test_ranking_metrics_on_known_relevance():
    ranking = ["a", "x", "b", "c"]
    relevant = {"a", "b"}
    assert precision_at_k(ranking, relevant, 4) == 0.5
    assert recall_at_k(ranking, relevant, 4) == 1.0
    assert 0 < ndcg_at_k(ranking, relevant, 4) <= 1
    assert 0 < map_at_k(ranking, relevant, 4) <= 1


def test_coverage_counts_unique_recommended_items():
    assert coverage_at_k([["a", "b"], ["b", "c"]], catalog_size=4, k=2) == 0.75
