# Recommendation Engine

## Current implementation

The engine performs transparent, CPU-efficient ranking of the seeded demo provider catalogue. It does not predict a condition and does not infer a specialty from symptoms. A specialty must be explicitly selected; candidates with a different specialty are excluded.

The score is:

```text
0.55
+ 0.20 * location_match
+ 0.10 * consultation_match
+ 0.10 * demo_availability_signal
+ 0.05 * stated_preference_match
```

Location is exact/substring matching. A missing location receives a neutral value. A missing consultation preference is neutral. Demo availability is a synthetic ranking signal, not appointment availability. The optional profile preference is currently matched as text against the consultation type. Results include matched attributes, an explanation, and demo-data limitations.

This is a hand-designed weighted ranker, not a trained recommender, collaborative filter, or clinically validated model. Provider eligibility is limited to exact specialty matching in the demo catalogue.

## Reproducible evaluation

Run `python scripts/evaluate_recommendations.py` from the repository root. The script calculates Precision@5, Recall@5, NDCG@5, MAP@5, and catalog coverage for an alphabetical baseline and the hybrid weighted ranker, then writes `data/processed/recommendation_evaluation.json`.

The fixture labels define a synthetic provider as relevant when its location and consultation type match the request. The current report (catalog size 32; four synthetic cases) is:

| Metric | Baseline | Hybrid |
|---|---:|---:|
| Precision@5 | 0.25 | 0.40 |
| Recall@5 | 0.625 | 1.00 |
| NDCG@5 | 0.452 | 1.00 |
| MAP@5 | 0.3792 | 1.00 |
| Coverage@5 | 0.625 | 0.625 |

These are reproducible fixture results only. They are not clinical relevance, patient benefit, safety, real-world provider quality, or a claim of production performance. A future evaluation needs reviewed user-preference data, an appropriate split, uncertainty analysis, and independent validation.
