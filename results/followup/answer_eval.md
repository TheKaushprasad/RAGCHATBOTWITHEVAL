# Answer-quality eval: `evals_followup.json`

Provider `openai` · chat `gpt-4.1-mini` · judge `gpt-4.1-mini` · retrieval `vector` k=3 · MIN_SIMILARITY=0.224 · chunks 350/50

## Summary

| metric | value | n |
|---|---|---|
| Correctness vs golden answer (judge) | 89% | 14 |
| Fully correct answers (judge = yes) | 79% | 14 |
| Faithfulness / no hallucination (judge) | 100% | 14 |
| Context recall (judge) | 96% | 14 |
| Answers with a citation | 100% | 14 |
| False refusals | 0% | 14 |
| Semantic similarity to golden (cosine) | 0.75 | 14 |
| Latency p50 / p95 | 4.4s / 8.9s | 14 |

## Outcome diagnosis

| outcome | questions |
|---|---|
| ok | 11 |
| generation miss | 3 |

## By topic

| topic | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| RAG | 3 | 67% | 100% | 100% | 0.67 |
| Prompt Engineering | 2 | 100% | 100% | 100% | 0.85 |
| Context Engineering | 2 | 100% | 100% | 100% | 0.75 |
| MCP | 2 | 75% | 100% | 100% | 0.61 |
| Machine Learning | 2 | 100% | 100% | 75% | 0.80 |
| Agentic AI | 2 | 100% | 100% | 100% | 0.73 |
| LLM Fundamentals | 1 | 100% | 100% | 100% | 0.95 |

## By type

| type | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| follow-up | 14 | 89% | 100% | 96% | 0.75 |

## By difficulty

| difficulty | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| medium | 9 | 89% | 100% | 94% | 0.75 |
| hard | 3 | 100% | 100% | 100% | 0.72 |
| easy | 2 | 75% | 100% | 100% | 0.75 |

## Failures (3)

- **F06 · generation miss**: what do the letters stand for?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly identifies the terms but uses 'Augmenting' instead of 'Augmentation' and lacks the detailed explanations provided in the golden answer.
  - Bot: The letters in RAG stand for Retrieval, Augmenting, and Generation [1].
  - Golden: Retrieval – looking up internal documents or knowledge bases and fetching the relevant information. Augmentation – adding that retrieved information to the user's prompt. Generation – the LLM writes the final answer based on the augmented prompt.
- **F07 · generation miss**: what are the embeddings it relies on, and what makes them?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains embeddings and embedding models and their role in semantic search, but it omits the example of the all-MiniLM-L6-v2 model producing 384-dimensional vectors present in the golden answer.
  - Bot: Semantic search relies on embeddings, which are arrays of numbers (vectors) that represent the meaning of text. These embeddings are created by embedding models, a type of machine learning model designed to convert text into numerical vectors that capture different aspects of the text's meaning. Bot
  - Golden: An embedding model converts text into a vector – an array of numbers that represents its meaning. These vectors are coordinates in a high-dimensional space where text with similar meaning sits close together. For example, the all-MiniLM-L6-v2 model produces 384-dimensional vectors.
- **F10 · generation miss**: and what does the server expose?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states that the MCP server exposes tools, resources, and prompts, but it lacks the detailed explanation and examples of each category provided in the golden answer.
  - Bot: The MCP server exposes specific capabilities through the protocol by providing information such as tools, resources, and prompts to the client [1][2].
  - Golden: Three things: Tools – functions the client can invoke (search, send a message, update DB records); Resources – read-only data like files, database records or API responses; and Prompt Templates – predefined, well-tested templates for AI interactions, like document Q&A or transcript summaries.

Per-question detail: `results/followup/answers.jsonl`.
