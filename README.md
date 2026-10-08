# Queryva: RAG Chatbot with Evals and Tuning

**Live demo: [ragevaltest.vercel.app](https://ragevaltest.vercel.app)** (chat at [/chat](https://ragevaltest.vercel.app/chat/)). Queryva is a chatbot over my AI Product Management notes (70 pages: LLMs, prompt and context engineering, RAG, MCP, ML, agentic AI). Try *"What is the swiss cheese capability model?"* or *"regression vs classification?"*. Ask *"Which is the best LLM to use right now?"* and it says the notes don't cover that instead of guessing. You can also open **Documents** and upload your own Word, PDF or markdown file to chat with it.

Answers cite their source passages, and the bot says "I don't know" when the documents don't cover the question. Quality is measured, not eyeballed: a **100-question golden dataset** grades every answer for correctness, faithfulness and retrieval quality, and each failure is diagnosed as a retrieval or a generation problem.

| Layer | Choice |
|---|---|
| LLM + embeddings | OpenAI (`gpt-4.1-mini`, `text-embedding-3-small` @ 768 dims) or Google Gemini, set by `PROVIDER` |
| Vector store | Supabase Postgres + pgvector (HNSW), plus Postgres full-text search for hybrid retrieval |
| Backend | FastAPI, deployed as a Vercel Python function |
| Frontend | Vanilla HTML/JS chat UI with clickable citations and document upload (DOCX, PDF, MD, TXT) |
| Evals | Golden-dataset answer eval with an LLM judge (correctness, faithfulness, context recall), retrieval eval (hit rate, MRR), tuning sweep |

## Architecture

```
                       ingest.py
docs/*.docx|pdf|md ──► load ──► chunk (350 tokens, 50 overlap) ──► embed ──► Supabase `documents`
                                                                             ├─ namespace 'public'
browser ── POST /api/upload ──► same loaders/chunker/embedder ──────────────► ├─ namespace 'session:<uuid>' (expires 24h)
                                                                             ├─ embedding (HNSW)
                                                                             └─ fts tsvector (GIN)

browser ── POST /api/chat ──► rag/pipeline.py
                                ├─ retrieve top-k (public docs + this visitor's uploads only):
                                │            vector  → match_documents()
                                │            hybrid  → hybrid_search()  (vector + keyword, Reciprocal Rank Fusion)
                                ├─ guard 1: top similarity < MIN_SIMILARITY → "I don't know" (no LLM call)
                                ├─ LLM with numbered passages; must cite [n]; guard 2: refuse if unsupported
                                └─ {answer, citations, retrieved, grounded}

eval_answers.py ── every golden question through the real pipeline + LLM judge ──► results/golden/answer_eval.md
eval.py         ── retrieval metrics against the live index                    ──► results/<set>/retrieval_eval.md
tune.py         ── in-memory sweep over chunking × retrieval mode × k          ──► results/<set>/tuning.md
```

The API and the evals call the same `rag/pipeline.py`, so the evals measure what users actually get.

## Evaluation against the golden dataset

### The dataset: [`evals_golden.json`](evals_golden.json)
I wrote 100 question–answer pairs from the AI PM notes, the way real users ask: casual phrasing, mixed capitalisation and short forms. Each entry is tagged:

```json
{
  "id": "Q006", "topic": "LLM Fundamentals", "type": "conceptual", "difficulty": "medium",
  "question": "what does the swiss cheese capability model mean?",
  "answer": "It means LLMs have random holes in their abilities: they can be brilliant in one area ... yet fail at simple things like counting ...",
  "source_section": "Why should a product manager learn about it?"
}
```

- **96 answerable questions** across 7 topics and 5 question types (conceptual, comparison, procedural, factual, calculation), at 3 difficulty levels.
- **4 out-of-scope questions**, such as "How much does Pinecone cost per month?". The golden answer describes the *expected behaviour*: say it isn't in the knowledge base, optionally mention what the notes do say, and don't invent anything.

### How each answer is graded
`eval_answers.py` sends every question through the live pipeline (retrieve, then guards, then LLM). It then gives a **judge LLM** the question, the golden answer, the bot's answer and the passages the bot retrieved, and gets back three grades:

| Grade | Question the judge answers | Catches |
|---|---|---|
| **Correctness** (yes / partial / no) | Does the bot's answer convey the key facts of the golden answer? Wording may differ. | Wrong or incomplete answers |
| **Faithfulness** (true / false) | Is every claim in the bot's answer supported by the retrieved passages? | Hallucination, even when the claim happens to be true |
| **Context recall** (yes / partial / no) | Do the retrieved passages contain what's needed to write the golden answer? | Retrieval failures |

Plus deterministic checks: refusals, whether the answer cites anything, semantic similarity (cosine between the bot's and the golden answer's embeddings) and latency.

### Diagnosing every failure
Combining **context recall** with **correctness** tells you *which component* to fix:

| Diagnosis | What happened | Fix |
|---|---|---|
| retrieval miss | The answer wasn't in the retrieved passages | Search: hybrid, query rewriting, chunking |
| incomplete retrieval | Only part of the answer was retrieved | Retrieve more (k) or use larger chunks |
| generation miss | Everything was retrieved; the answer didn't use it | Prompt or model |
| false refusal | Said "I don't know" although the passages had the answer | Prompt (over-cautious) |
| hallucination | A claim not supported by the passages | Prompt or guards |

The report breaks results down by topic, question type and difficulty, and lists every failure with the judge's reasoning, so a human can audit the judge.

## Results on the golden dataset

`gpt-4.1-mini` answers and judges, with `text-embedding-3-small`, 350/50-token chunks and vector search.

| | k=3 (start) | **k=5 (adopted)** |
|---|---|---|
| Correctness vs golden (judge) | 86% | **88%** |
| Fully correct answers | 76% | **80%** |
| Faithfulness (no hallucination) | 100% | 100% |
| Context recall | 92% | **95%** |
| False refusals | 4% | **2%** |
| Out-of-scope handled correctly | 4/4 | 4/4 |
| Latency p50 / p95 | 2.8s / 3.7s | 2.8s / 4.2s |

Reports: [`results/golden/answer_eval.md`](results/golden/answer_eval.md) (k=3) and [`results/golden-k5/answer_eval.md`](results/golden-k5/answer_eval.md) (k=5), with per-question detail in each folder's `answers.jsonl`.

### What the golden-set eval found
1. **Failures were incomplete answers, not wrong ones.** At k=3, every "generation miss" was graded *partial*. In 11 of them the retrieved passages held only part of the answer, because these notes explain broad topics across several pages. Re-labelling these as **incomplete retrieval** pointed at the fix: retrieve more chunks. With k=5, incomplete retrieval fell from 11 to 4, and 12 failures were fixed, such as "What are the main stages of building an LLM?", where the bot had dropped the RL stage.
2. **Easy questions retrieve worse than hard ones.** Context recall was 87% for easy vs 97% for hard at k=3. Short questions like *"what is a base model?"* give the search little to match on: vector search returned ML-evaluation pages that matched on "model". Hybrid search finds the right chunk. That question remains the one true retrieval miss, and the next experiment is hybrid search or query rewriting.
3. **No hallucinations; the bot is cautious instead.** Faithfulness was 100% in both runs, and all 4 out-of-scope questions were declined correctly. At k=3 the opposite error showed up instead: 3 false refusals where the passages *did* contain the answer, e.g. the FineWeb pipeline. k=5 cut them to 1.
4. **The judge needs auditing.** In one case it marked an answer as missing "very complex logic" when the answer opens with exactly that. 8 answers flipped from *yes* to *partial* between runs without a clear cause. With n≈16 per topic, one question moves a topic score 6 points. Treat small differences as noise and read the failure list.
5. **The golden set needs review too.** In Q034 (the Maruti Swift claim), the source notes are inconsistent: parts 350,000 + labour 30,000 sums to 380,000, but the example output says `repair_cost: 390000`. The golden answer inherited the inconsistency, so the bot can't be right on that question. Fixing the source or the golden answer is the right move, not tuning the bot.

## User feedback: closing the loop

Every answer in the chat has 👍 / 👎 buttons. A thumbs-down opens an optional "What was wrong?" box.
- **What's stored:** each rating goes to a `feedback` table in Supabase with the question, the answer, the cited sources, whether it was an "I don't know", and the model and retrieval settings that produced it. That makes ratings comparable across config changes.
- **Changing your mind:** a visitor can change or remove their vote; it's one row per answer, keyed by an ID the browser generates.
- **No session ID is stored**, so ratings aren't linked to a visitor or their uploads.

```bash
python feedback_report.py
python feedback_report.py --export golden_candidates.json
```

The first command prints the helpful rate, splits it by config, and lists every thumbs-down with the user's comment and the cited pages. The second turns those thumbs-downs into draft golden-dataset entries. Each draft includes the bot's answer and the user's comment; you write the correct `answer`, then add it to `evals_golden.json`. Real user failures become permanent eval cases, so the next `eval_answers.py` run checks they stay fixed.

## Case study: tuning on a synthetic corpus

Before the AI PM notes, I tuned the pipeline on a fictional product's docs ("Tidepool", 8 files) with a 50-question eval set. Because it's fictional, the model can't answer from general knowledge. That work is kept in [`examples/tidepool/`](examples/tidepool/) and set the chunking and the refusal threshold used today.

`tune.py` grid-searched 132 configs (chunk size 200–800 × overlap 0–100 × vector/keyword/hybrid × k 1–8). Among configs within one question of the best hit rate, it picked the one that sends the fewest tokens to the LLM.

| | Baseline | Tuned |
|---|---|---|
| Config | 500/50, vector, k=5, threshold 0.30 | 350/50, vector, k=3, threshold 0.224 |
| Answer accuracy (judge) | 82% | **94%** |
| Citation accuracy | 82% | **98%** |
| False refusals | 15% | **2%** |
| Context tokens / query | 1,678 | **744 (−56%)** |

**Key lessons:**
- **The refusal threshold, not retrieval, caused all 6 baseline false refusals.** On-topic unanswerable questions score as high as answerable ones, so a similarity threshold can't separate them. The threshold is now tuned as an off-topic filter that must never block a real question, and the prompt handles the rest.
- **Hybrid search ranked better** (MRR 0.90 vs 0.85), but the cost-first rule chose vector.

Full reports are in [`examples/tidepool/results/`](examples/tidepool/results/).

**Settings don't transfer between corpora.** k=3 was best for Tidepool's short, fact-dense docs, but k=5 is better for the AI PM notes, where answers span several pages. That's why the golden dataset matters: tune on *your* documents and *your* users' questions.

## Run it

### 1. Setup
```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env          # macOS/Linux: cp .env.example .env
```
Fill in `OPENAI_API_KEY`, `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` (the service_role key). Then paste [supabase/schema.sql](supabase/schema.sql) into the Supabase SQL editor and run it.

### 2. Index and evaluate
```bash
python ingest.py
python eval_answers.py
```
`ingest.py` indexes everything in `docs/`. `eval_answers.py` runs the golden dataset and writes `results/golden/`.

### 3. Experiment
Change a setting via an env var and write to a separate folder so the baseline isn't overwritten:
```bash
TOP_K=8 python eval_answers.py --out results/golden-k8
```
```bash
RETRIEVAL_MODE=hybrid python eval_answers.py --out results/golden-hybrid
```
Rebuild a report from saved answers without re-asking the questions:
```bash
python eval_answers.py --report-only
```
Reproduce the Tidepool case study. Note this swaps the live index to the Tidepool docs; run `python ingest.py` afterwards to switch back:
```bash
python ingest.py --docs examples/tidepool/docs
python tune.py --docs examples/tidepool/docs --file examples/tidepool/evals.json
python eval_answers.py --file examples/tidepool/evals.json
```

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
The tuned settings are the code defaults, so only the three keys are required. Vercel detects the FastAPI app in `api/index.py` and serves `public/` statically. Don't add an `/api` rewrite: Vercel now routes rewritten requests by their destination path, so FastAPI would see `/api/index` and return 404. Ingestion and evals run locally and are excluded from the deploy.

### Uploading your own documents
Visitors can upload `.docx`, `.pdf`, `.md` or `.txt` files from the **Documents** panel (button or drag-and-drop).
- **Private per browser.** The page creates a random session ID (kept in `localStorage`) and sends it as `X-Session-Id`. Uploads are stored under `session:<id>`, and the search functions only return `public` chunks plus the caller's own namespace. Other visitors can't see or delete them, and nobody can delete the indexed docs through the API.
- **Temporary.** Uploads expire after 24 hours. Expired rows are filtered out of search and purged on the next upload.
- **Cost-bounded for a public demo.** 4 MB per file, 5 files per visitor, 150 chunks per file, and 5,000 uploaded chunks across all visitors (configurable through `UPLOAD_*` env vars).
- **Same pipeline.** Uploads go through the same loaders, chunker and embedder as `ingest.py`. Word headings, lists and tables are kept. PDFs exported from Google Docs, which place every word separately, are detected and re-extracted in layout mode.

## Project layout
```
api/index.py         FastAPI app (chat, upload, documents, feedback, health)
rag/config.py        env-driven settings (provider, models, chunking, retrieval, upload limits)
rag/embeddings.py    OpenAI / Gemini embeddings, batching, retry on 429/5xx
rag/llm.py           prompt, chat completion, citation parsing
rag/loaders.py       DOCX / PDF / markdown / text → sections
rag/chunking.py      token-bounded chunker that prefers paragraph/sentence boundaries
rag/pipeline.py      retrieve → guard → answer (shared by API and evals)
rag/store.py         Supabase: upsert, namespaces, vector + hybrid search RPCs
rag/uploads.py       visitor upload validation, limits, indexing
rag/evalset.py       eval loading, hit logic, threshold search, results folders
ingest.py            incremental ingestion of docs/ (re-embeds only changed chunks)
eval_answers.py      golden-dataset answer eval with LLM judge + failure diagnosis
eval.py              retrieval eval (hit rate / MRR; needs expected_substring labels)
feedback_report.py   thumbs up/down summary; export thumbs-downs as golden-dataset drafts
tune.py              hyperparameter sweep (needs expected_substring labels)
evals_golden.json    100-question golden dataset for the AI PM notes
docs/                the indexed corpus (ai-pm-notes.pdf)
examples/tidepool/   synthetic-corpus case study: docs, 50-question eval set, tuning results
results/             golden-dataset eval reports
supabase/schema.sql  documents + feedback tables, indexes, namespaces, match_documents + hybrid_search
public/              landing page (index.html) + chat UI (chat/) + documents panel
```

## Notes and limitations
- **The judge is an LLM.** It can be lenient or inconsistent, as finding 4 above shows. Set `JUDGE_MODEL` to a stronger model for stricter grading, and spot-check the failure list.
- **Small samples.** 100 questions is a small set: one question is 1 point overall and about 6 points within a topic.
- **Golden labels are section names, not exact text.** That's why retrieval quality for the golden set is measured by judged context recall. `eval.py` and `tune.py` need exact-text labels (`expected_substring`), which only the Tidepool set has. Adding them to the golden set would enable an automated sweep on the AI PM notes.
- **Switching embedding model re-embeds everything.** Changing `PROVIDER` or `EMBED_MODEL` changes the embedding space; chunk hashes include the model, so `python ingest.py` re-embeds automatically.
- **Supabase free projects pause** after about a week of inactivity.
- **No OCR.** Scanned PDFs without a text layer aren't supported.
- **The session ID is a capability, not authentication.** Anyone holding a browser's ID could read that browser's uploads. That's fine for temporary demo files; real user data would need accounts.
