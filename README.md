# RAG Chatbot with Evals and Tuning

**Live demo: [ragevaltest.vercel.app](https://ragevaltest.vercel.app)**. Try *"Can I pay with PayPal?"* or *"Is Tidepool SOC 2 certified?"* (the docs don't say, so it should answer "I don't know").

A retrieval-augmented chatbot over PDFs and markdown. Answers come with citations to the source chunks, and the bot says "I don't know" when the documents don't cover the question. Its configuration is chosen by measurement, not guesswork: chunk size, overlap, retrieval mode, top-k and the refusal threshold all come from a tuning sweep scored against a labelled eval set.

| Layer | Choice |
|---|---|
| LLM + embeddings | OpenAI (`gpt-4.1-mini`, `text-embedding-3-small` @ 768 dims) or Google Gemini, set by `PROVIDER` |
| Vector store | Supabase Postgres + pgvector (HNSW), plus Postgres full-text search for hybrid retrieval |
| Backend | FastAPI, deployed as a Vercel Python function |
| Frontend | Vanilla HTML/JS chat UI with clickable citations |
| Evals | Retrieval hit rate / MRR, LLM-judged answer accuracy and faithfulness, citation accuracy, refusal behaviour |

## Architecture

```
                       ingest.py
docs/*.pdf|*.md ──► load ──► chunk (N tokens, M overlap) ──► embed ──► Supabase `documents`
                                                                          ├─ embedding (HNSW)
                                                                          └─ fts tsvector (GIN)

browser ── POST /api/chat ──► rag/pipeline.py
                                ├─ retrieve: vector  → match_documents()
                                │            hybrid  → hybrid_search()  (vector + keyword, Reciprocal Rank Fusion)
                                ├─ guard 1: top similarity < MIN_SIMILARITY → "I don't know" (no LLM call)
                                ├─ LLM with numbered passages; must cite [n]; guard 2: refuse if unsupported
                                └─ {answer, citations, retrieved, grounded}

tune.py         ── in-memory sweep over chunking × retrieval mode × k ──► results/tuning.md + best .env values
eval.py         ── retrieval metrics against the live index           ──► results/retrieval_eval.md
eval_answers.py ── full pipeline + LLM judge                          ──► results/answer_eval.md
```

The API and both evals call the same `rag/pipeline.py`, so the evals measure what users actually get.

## Evaluation

### Dataset: `evals.json` (50 questions)
- **40 answerable.** Each has `expected_sources`, an `expected_substring` that the relevant chunk must contain, and a reference `answer`.
- **10 unanswerable** (`"answerable": false`). These are plausible questions the docs don't cover, such as "Is Tidepool SOC 2 certified?". The correct response is "I don't know".
- **Built to be hard on purpose.** The sample corpus ("Tidepool", a fictional product, so the model can't answer from general knowledge) has 8 docs with confusable facts. For example, `changelog.md` holds outdated values like the old 14-day trial and the old 60 req/min rate limit, and 30-day periods appear in several unrelated features.

### Metrics
| Script | Metric | How it's computed |
|---|---|---|
| `eval.py` | Hit rate@k | Any of the top-k chunks is from an expected source **and** contains the expected substring |
| | MRR@k | 1 / rank of the first relevant chunk |
| | Refusal threshold check | Top-1 similarity of answerable vs unanswerable questions |
| `eval_answers.py` | Answer accuracy | LLM judge compares the answer to the reference (yes = 1, partial = 0.5) |
| | Faithfulness | LLM judge: is every claim supported by the retrieved passages? |
| | Citation accuracy | Deterministic: at least one cited chunk is a relevant chunk |
| | False refusals | "I don't know" on an answerable question |
| | Correct refusals | "I don't know" on an unanswerable question (the rest are hallucinations) |
| | Latency p50/p95 | End-to-end pipeline time |

## Tuning

`tune.py` runs a grid search in memory, with no database round-trips:

- **chunk size** 200 / 350 / 500 / 800 tokens × **overlap** 0 / 50 / 100
- **retrieval mode** vector / keyword (BM25) / hybrid (Reciprocal Rank Fusion)
- **top-k** 1 / 3 / 5 / 8
- **refusal threshold**: for each chunking, the highest cosine cutoff that still answers every answerable question, minus a 0.03 margin. Questions below it get "I don't know" without an LLM call.

**Selection rule.** The sweep keeps every config whose hit rate is within one question of the best. From those it picks the one that sends the fewest context tokens to the LLM, then the highest MRR. A bigger k almost always raises recall but costs tokens and adds noise to the prompt; this rule makes that trade-off explicit.

Embeddings are cached in `.cache/`, so re-running the sweep or adding grid points only embeds new chunks.

## Results

OpenAI `text-embedding-3-small` (768 dims) + `gpt-4.1-mini`, 50-question eval set. The judge is `gpt-4.1-mini`.

| | Baseline | Tuned | Change |
|---|---|---|---|
| Config | 500/50 tokens, vector, k=5, threshold 0.30 | 350/50 tokens, vector, k=3, threshold 0.224 | |
| Retrieval hit rate | 98% (@5) | 98% (@3) | same recall with fewer chunks |
| MRR | 0.790 | 0.850 | +0.06 |
| Context tokens / query | 1,678 | 744 | **−56%** |
| Answer accuracy (judge) | 82% | **94%** | +12 pts |
| Faithfulness (judge) | 100% | 98% | −1 question* |
| Citation accuracy | 82% | **98%** | +16 pts |
| False refusals | 15% | **2%** | −13 pts |
| Correct refusals (unanswerable) | 100% | 100% | |
| Latency p50 / p95 | 2.7s / 5.1s | 2.6s / 5.2s | |

Full reports: [`results/tuning.md`](results/tuning.md), [`results/retrieval_eval.md`](results/retrieval_eval.md), [`results/answer_eval.md`](results/answer_eval.md); the baseline run is in [`results/baseline/`](results/baseline/).

### What the evals found
1. **The refusal threshold was the biggest source of error, not retrieval.** All 6 baseline false refusals came from the `MIN_SIMILARITY=0.30` guard. The right chunk was retrieved each time, but its similarity was 0.26–0.29. The LLM never needed that guard.
2. **On-topic unanswerable questions can't be filtered by similarity.** "Does Tidepool offer a Gantt chart?" scores 0.65, higher than most answerable questions. Separating the two by threshold peaks at about 84% accuracy, while the prompt-level "I don't know" rule refused all 10 unanswerable questions. So the threshold is now tuned as a cheap off-topic filter that must never block a real question, not as a classifier.
3. **Smaller chunks with a smaller k cut context by 56% at the same recall.** Each chunk is more focused, which raised MRR and citation accuracy.
4. **Hybrid search ranks better; the cost rule picked vector anyway.** Keyword search alone gets the right chunk first 90% of the time vs 75% for vector, because questions often contain exact terms like "PayPal" or "SMS". Hybrid (RRF) at 350 tokens reaches MRR 0.90 vs 0.85 at k=3, and 100% recall at k=5. It tied vector on hit@3 but used about 10% more context, so the cost-first rule chose vector. If ranking quality matters more than tokens, `RETRIEVAL_MODE=hybrid` is the better setting. The rule is a choice, and the full grid is in `results/tuning.csv`.

### Remaining failures (tuned)
- *"What happens to tasks nobody has touched in a month?"* is a **retrieval miss** caused by vocabulary mismatch: the docs say "ripples not updated in 30 days". Query rewriting or HyDE would be the next experiment.
- \*Three answers were graded "partial" or "unfaithful" for small omissions or reasonable inferences, e.g. "after the grace period data is removed". These are judge-strictness cases; with 40 questions, one question is 2.5 points.

## Run it

### 1. Setup
```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env          # macOS/Linux: cp .env.example .env
```
Fill in `OPENAI_API_KEY`, `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` (the service_role key). Then paste [supabase/schema.sql](supabase/schema.sql) into the Supabase SQL editor and run it.

### 2. Baseline
```bash
python ingest.py
python eval.py
python eval_answers.py
```
Copy the numbers from `results/` into the **Baseline** column.

### 3. Tune
```bash
python tune.py
```
Paste the printed `.env` block into `.env`, then re-ingest (chunking changed) and re-evaluate:
```bash
python ingest.py --reset
python eval.py
python eval_answers.py
```
Fill in the **Tuned** column.

### 4. Chat locally
```bash
uvicorn api.index:app --reload
```
Open http://localhost:8000.

### 5. Deploy to Vercel
```bash
vercel
vercel env add OPENAI_API_KEY
vercel env add SUPABASE_URL
vercel env add SUPABASE_SERVICE_KEY
vercel --prod
```
The tuned retrieval settings are the code defaults, so only the three keys are required. Vercel detects the FastAPI app in `api/index.py` and serves `public/` statically. Don't add an `/api` rewrite: Vercel now routes rewritten requests by their destination path, so FastAPI would see `/api/index` and return 404. Ingestion, evals and tuning run locally and are excluded from the deploy.

## Project layout
```
api/index.py         FastAPI app (POST /api/chat, GET /api/health)
rag/config.py        env-driven settings (provider, models, chunking, retrieval)
rag/embeddings.py    OpenAI / Gemini embeddings, batching, retry on 429/5xx
rag/llm.py           prompt, chat completion, citation parsing
rag/pipeline.py      retrieve → guard → answer (shared by API and evals)
rag/store.py         Supabase: upsert, vector + hybrid search RPCs
rag/chunking.py      token-bounded chunker that prefers paragraph/sentence boundaries
rag/evalset.py       eval loading, hit logic, threshold search
ingest.py            incremental ingestion (re-embeds only changed chunks)
tune.py              hyperparameter sweep
eval.py              retrieval eval against the live index
eval_answers.py      end-to-end answer eval with LLM judge
evals.json           50 labelled questions
supabase/schema.sql  table, indexes, match_documents + hybrid_search
public/              chat UI
docs/                sample corpus (replace with your own and rewrite evals.json)
```

## Notes and limitations
- `tune.py` uses in-memory BM25 for the keyword side. Production hybrid search uses Postgres full-text search, so confirm the winning config with `eval.py` against the live index.
- With an eval set this small, one question is 2.5 points of hit rate. Treat differences under about 5 points as noise.
- Judging with the same model that answered can be lenient. Set `JUDGE_MODEL` to a stronger model for a stricter grade.
- Switching `PROVIDER` or `EMBED_MODEL` changes the embedding space. Chunk hashes include the model, so `python ingest.py` re-embeds everything automatically.
- Supabase free projects pause after about a week of inactivity.
