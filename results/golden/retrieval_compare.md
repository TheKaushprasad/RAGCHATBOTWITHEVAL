# Retrieval comparison: `evals_golden.json`

96 answerable cases · `openai:text-embedding-3-small` · mode `vector` · 20 candidates reranked to top 5 · rewrite `openai:gpt-4.1-mini` · labels judged by `gpt-4.1-mini` (evals_golden_qrels.json)

| query | reranker | hit rate@5 | MRR@5 |
|---|---|---|---|
| original | none | 94/96 = 98% | 0.885 |
| original | llm | 95/96 = 99% | 0.984 |
| original | bge | 93/96 = 97% | 0.906 |

- Relevant passage anywhere in the top 20 (original query): 96/96 = 100% (the most any reranker can reach)
- Cases where the judge found no relevant passage at all: 0
