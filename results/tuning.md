# RAG tuning report

Embedding model: `openai:text-embedding-3-small:768` · eval set: 40 answerable + 10 unanswerable questions
Selection rule: hit rate within 2.5% of the best, then fewest context tokens, then highest MRR.

## Chosen config

| chunk tokens | overlap | mode | top-k | hit rate | MRR | context tokens / query | min_similarity | unanswerable filtered pre-LLM |
|---|---|---|---|---|---|---|---|---|
| 350 | 50 | vector | 3 | 98% | 0.850 | 744 | 0.224 | 1/10 |

```env
CHUNK_TOKENS=350
CHUNK_OVERLAP=50
RETRIEVAL_MODE=vector
TOP_K=3
MIN_SIMILARITY=0.224
```

## Retrieval mode × chunking (hit@5)

| chunks | vector hit@5 | keyword hit@5 | hybrid hit@5 | min_similarity | off-topic filtered |
|---|---|---|---|---|---|
| 200/0 | 100% | 92% | 98% | 0.241 | 2/10 |
| 200/50 | 92% | 92% | 95% | 0.228 | 1/10 |
| 350/0 | 95% | 95% | 98% | 0.241 | 2/10 |
| 350/50 | 98% | 95% | 100% | 0.224 | 1/10 |
| 350/100 | 95% | 92% | 98% | 0.238 | 3/10 |
| 500/0 | 100% | 95% | 98% | 0.229 | 2/10 |
| 500/50 | 98% | 95% | 98% | 0.229 | 2/10 |
| 500/100 | 98% | 95% | 98% | 0.229 | 3/10 |
| 800/0 | 98% | 98% | 100% | 0.162 | 2/10 |
| 800/50 | 98% | 98% | 100% | 0.162 | 2/10 |
| 800/100 | 98% | 98% | 100% | 0.162 | 2/10 |

"min_similarity" is the highest top-1 cosine cutoff that still answers every answerable question (minus a
0.03 margin). On-topic unanswerable questions score like answerable ones, so the threshold only filters
clearly off-topic queries; the prompt guard catches the rest (measured by eval_answers.py).

## Best config per mode and k

| mode | k | config | hit_rate | mrr | avg_context_tokens |
|---|---|---|---|---|---|
| vector | 1 | 350/0 | 75% | 0.750 | 272 |
| vector | 3 | 800/0 | 98% | 0.854 | 1827 |
| vector | 5 | 200/0 | 100% | 0.802 | 768 |
| vector | 8 | 800/0 | 100% | 0.858 | 4968 |
| keyword | 1 | 500/0 | 90% | 0.900 | 379 |
| keyword | 3 | 800/0 | 98% | 0.933 | 1778 |
| keyword | 5 | 800/0 | 98% | 0.933 | 2903 |
| keyword | 8 | 800/0 | 100% | 0.938 | 3982 |
| hybrid | 1 | 350/50 | 88% | 0.875 | 266 |
| hybrid | 3 | 350/0 | 98% | 0.900 | 824 |
| hybrid | 5 | 350/50 | 100% | 0.924 | 1256 |
| hybrid | 8 | 350/50 | 100% | 0.924 | 2077 |

## Top 15 configs overall

| chunk_tokens | overlap | mode | k | hit_rate | mrr | avg_context_tokens |
|---|---|---|---|---|---|---|
| 800 | 0 | keyword | 8 | 100% | 0.938 | 3982 |
| 800 | 50 | keyword | 8 | 100% | 0.938 | 3982 |
| 800 | 100 | keyword | 8 | 100% | 0.938 | 3982 |
| 350 | 50 | hybrid | 5 | 100% | 0.924 | 1256 |
| 350 | 50 | hybrid | 8 | 100% | 0.924 | 2077 |
| 350 | 0 | hybrid | 8 | 100% | 0.904 | 2197 |
| 800 | 0 | hybrid | 5 | 100% | 0.902 | 3064 |
| 800 | 50 | hybrid | 5 | 100% | 0.902 | 3064 |
| 800 | 100 | hybrid | 5 | 100% | 0.902 | 3064 |
| 800 | 0 | hybrid | 8 | 100% | 0.902 | 4968 |
| 800 | 50 | hybrid | 8 | 100% | 0.902 | 4968 |
| 800 | 100 | hybrid | 8 | 100% | 0.902 | 4968 |
| 350 | 100 | hybrid | 8 | 100% | 0.884 | 2140 |
| 350 | 0 | keyword | 8 | 100% | 0.883 | 2055 |
| 350 | 50 | keyword | 8 | 100% | 0.882 | 1930 |

Full grid: `results/tuning.csv`. Keyword search here is in-memory BM25; production hybrid search uses
Postgres full-text search (`hybrid_search` in `supabase/schema.sql`), so confirm the winner with `python eval.py`.
