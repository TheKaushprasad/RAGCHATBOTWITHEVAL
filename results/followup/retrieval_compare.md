# Retrieval comparison: `evals_followup.json`

14 answerable cases · `openai:text-embedding-3-small` · mode `vector` · 20 candidates reranked to top 5 · rewrite `openai:gpt-4.1-mini` · labels judged by `gpt-4.1-mini` (evals_followup_qrels.json)

| query | reranker | hit rate@5 | MRR@5 |
|---|---|---|---|
| original | none | 14/14 = 100% | 0.685 |
| original | llm | 14/14 = 100% | 1.000 |
| original | bge | 12/14 = 86% | 0.768 |
| rewritten | none | 14/14 = 100% | 0.911 |
| rewritten | llm | 14/14 = 100% | 1.000 |
| rewritten | bge | 14/14 = 100% | 0.917 |

- Relevant passage anywhere in the top 20 (original query): 14/14 = 100% (the most any reranker can reach)
- Relevant passage anywhere in the top 20 (rewritten query): 14/14 = 100% (the most any reranker can reach)
- Cases where the judge found no relevant passage at all: 0
