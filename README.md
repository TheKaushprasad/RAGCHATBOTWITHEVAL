# RAG Chatbot with Evals and Tuning

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
- **refusal threshold**: for each chunking, the cosine cutoff that best separates answerable from unanswerable questions

**Selection rule.** The sweep keeps every config whose hit rate is within one question of the best. From those it picks the one that sends the fewest context tokens to the LLM, then the highest MRR. A bigger k almost always raises recall but costs tokens and adds noise to the prompt; this rule makes that trade-off explicit.

Embeddings are cached in `.cache/`, so re-running the sweep or adding grid points only embeds new chunks.

## Results

> Fill this in from `results/*.md` after running the pipeline on your keys (see below).

| | Baseline (500/50, vector, k=5) | Tuned |
|---|---|---|
| Retrieval hit rate | | |
| MRR | | |
| Context tokens / query | | |
| Answer accuracy | | |
| Faithfulness | | |
| Correct refusals (unanswerable) | | |

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
Also add your tuned `RETRIEVAL_MODE`, `TOP_K` and `MIN_SIMILARITY`. Leave the framework preset on **Other**. `vercel.json` routes `/api/*` to FastAPI and serves `public/` statically. Ingestion, evals and tuning run locally and are excluded from the deploy.

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
