# Answer-quality eval: `evals_golden.json`

Provider `openai` · chat `gpt-4.1-mini` · judge `openai:gpt-4.1-mini` · retrieval `vector` k=5 · reranker `llm` · MIN_SIMILARITY=0.224 · chunks 350/50

## Summary

| metric | value | n |
|---|---|---|
| Correctness vs golden answer (judge) | 93% | 96 |
| Fully correct answers (judge = yes) | 89% | 96 |
| Faithfulness / no hallucination (judge) | 100% | 96 |
| Context recall (judge) | 98% | 96 |
| Answers with a citation | 98% | 96 |
| False refusals | 2% | 96 |
| Semantic similarity to golden (cosine) | 0.76 | 96 |
| Out-of-scope handled correctly (judge) | 100% | 4 |
| Out-of-scope: said "I don't know" | 100% | 4 |
| Latency p50 / p95 | 5.4s / 7.0s | 100 |

## Outcome diagnosis

| outcome | questions |
|---|---|
| ok | 89 |
| generation miss | 7 |
| false refusal | 2 |
| retrieval miss | 1 |
| incomplete retrieval | 1 |

## By topic

| topic | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| LLM Fundamentals | 19 | 89% | 100% | 95% | 0.76 |
| RAG | 17 | 100% | 100% | 100% | 0.77 |
| Prompt Engineering | 16 | 84% | 100% | 100% | 0.75 |
| Machine Learning | 16 | 97% | 100% | 97% | 0.78 |
| MCP | 11 | 86% | 100% | 95% | 0.71 |
| Context Engineering | 10 | 95% | 100% | 100% | 0.79 |
| Agentic AI | 7 | 100% | 100% | 100% | 0.76 |
| Out of Scope | 4 | 100% | 100% | n/a | 0.53 |

## By type

| type | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| conceptual | 34 | 99% | 100% | 100% | 0.81 |
| comparison | 21 | 90% | 100% | 95% | 0.79 |
| procedural | 21 | 98% | 100% | 100% | 0.73 |
| factual | 18 | 81% | 100% | 94% | 0.68 |
| out_of_scope | 4 | 100% | 100% | n/a | 0.53 |
| calculation | 2 | 75% | 100% | 100% | 0.73 |

## By difficulty

| difficulty | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| medium | 56 | 92% | 100% | 97% | 0.75 |
| easy | 29 | 98% | 100% | 100% | 0.74 |
| hard | 15 | 87% | 100% | 97% | 0.76 |

## Failures (11)

- **Q010 · retrieval miss**: What steps are in the FineWeb data pipeline?
  - Judge: correct=no, faithful=True, context recall=no. The answer describes the RAG data preparation pipeline steps (chunking, embedding generation, vector DB storage) which differ entirely from the FineWeb data pipeline steps listed in the golden answer (URL filtering, text extraction, language filtering, etc.), and the passages do not contain the FineWeb pipeline details.
  - Bot: The FineWeb data pipeline steps are described as the Data Preparation Pipeline (Ingestion) in the RAG pipeline and include:

1. Document Chunking: Large policy documents are broken down into smaller, focused pieces called chunks. This solves the precision problem by ensuring users receive specific r
  - Golden: URL filtering (block malware, adult, spam sites) → text extraction → language filtering (e.g. keep pages with more than 50% English) → Gopher filtering (reliability and safety) → MinHash dedup (remove near-duplicates) → C4 filters → custom filters (based on model goals, safety, domain) → PII removal
- **Q015 · generation miss**: Who writes the conversations used to fine-tune an assistant?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states that human labelers hired by companies write prompts and ideal responses following detailed instructions requiring helpful, truthful, and harmless answers, but it omits that today LLMs also help create these datasets, resulting in millions of synthetic conversations that humans then edit, which is included in the golden answer and passages.
  - Bot: The conversations used to fine-tune an assistant are written by human labelers, who are human contractors hired by companies. These labelers create conversations by coming up with prompts and writing out the ideal assistant responses following detailed labeling instructions provided by the company. 
  - Golden: Human labelers hired by the company write prompts and ideal assistant responses, following detailed labeling instructions that ask for helpful, truthful and harmless answers. Today LLMs also help create these datasets, so they often contain millions of synthetic conversations that humans then edit.
- **Q016 · generation miss**: When I'm chatting with ChatGPT, who am I really talking to?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer accurately describes ChatGPT as a model trained through pre-training and supervised fine-tuning on human-labeled conversations to adopt an assistant persona, but it omits the key point that ChatGPT is effectively a statistical simulation of a human data labeler following company labeling instructions, which is central to the golden answer.
  - Bot: When you are chatting with ChatGPT, you are really talking to an assistant model that has gone through post-training stages to take on the persona of a knowledgeable, helpful assistant. This assistant is based on a Large Language Model (LLM) that was initially trained as a base model to simulate int
  - Golden: In effect, a statistical simulation of a human data labeler following the company's labeling instructions. The model learned its assistant persona by imitating those example conversations.
- **Q027 · generation miss**: Give me tips to write better prompts
  - Judge: correct=partial, faithful=True, context recall=yes. The answer covers the six key strategies from the golden answer but adds many extra tips not summarized in the golden answer, making it more detailed but partially aligned; all claims are supported by the passages, which contain the needed information.
  - Bot: Tips to write better prompts include:

1. Set clear goals and objectives for the prompt [1].

2. Provide context and background information, including dynamic content (input that changes per query) and static data (context constant across queries) [1][2].

3. Use few-shot prompting by providing one 
  - Golden: Six strategies: (1) set clear goals – use action verbs, define length/format, specify the audience; (2) provide context – relevant facts, sources, definitions; (3) use few-shot examples to show style and level of detail; (4) be specific – precise language, quantify requests, break tasks into steps; 
- **Q031 · false refusal**: What are the 10 steps in Anthropic's prompting framework?
  - Judge: correct=no, faithful=True, context recall=yes. The answer correctly notes that the passages do not explicitly list all 10 steps or attribute them to Anthropic, but it does mention several steps that align with the golden answer, reflecting partial correctness and faithful representation of the passages which contain the needed information.
  - Bot: I don't know. The provided passages describe a 10-step framework for effective prompting but do not list all 10 steps explicitly or attribute them to Anthropic. The passages include some steps such as Task Context, Tone Context, Incorporate Examples, Adding Conversation History, Immediate Task Descr
  - Golden: 1. Task context, 2. Tone context, 3. Background data/documents/images, 4. Detailed task description and rules, 5. Examples, 6. Conversation history, 7. Immediate task description or request, 8. Thinking step by step, 9. Output formatting, 10. Prefilled response (if any).
- **Q033 · generation miss**: In the vehicle claims example, when is a car considered a total loss?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states the threshold and ratio calculation for total loss but omits the details about the verdict being REPAIRABLE below the threshold and the 'needs_manual_review' explanation for borderline ratios.
  - Bot: A car is considered a total loss when the repair_to_market_ratio, which is the repair cost divided by the vehicle's market value, is greater than or equal to the total_loss_threshold of 0.70 (70%) [1][3][4].
  - Golden: When the repair-to-market-value ratio (repair cost ÷ market value) is greater than or equal to the threshold, which defaults to 0.70. Below that the verdict is REPAIRABLE. If the ratio is within ±0.05 of the threshold, 'needs_manual_review' is added to the explanations.
- **Q034 · generation miss**: For the Maruti Swift example (E2), how was the payable amount 370000 calculated?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states the payable amount calculation as repair cost minus salvage value but omits the intermediate steps of repair cost calculation, ratio, and total loss determination present in the golden answer and passages.
  - Bot: For the Maruti Swift example (E2), the payable amount of 370000 was calculated by subtracting the salvage value (20000) from the repair cost (390000), i.e., 390000 - 20000 = 370000 [3].
  - Golden: Repair cost = parts 350,000 + labour 30,000 = 390,000. Ratio = 390,000 / 500,000 = 0.78, which is ≥ 0.70, so it's a TOTAL_LOSS. Payable amount = repair cost − salvage value = 390,000 − 20,000 = 370,000 (never below 0).
- **Q043 · generation miss**: Explain semantic, episodic and procedural memory for agents
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly identifies semantic, episodic, and procedural memories and their roles but omits the examples and human parallels present in the golden answer.
  - Bot: Semantic, episodic, and procedural memories are types of memories that agents might select to provide task-relevant context:

- Episodic memories: few-shot examples for examples of desired behavior.
- Procedural memories: instructions to steer behavior.
- Semantic memories: facts for task-relevant c
  - Golden: Semantic memory stores facts (e.g. facts about a user). Episodic memory stores experiences (e.g. past agent actions, useful as few-shot examples). Procedural memory stores instructions (e.g. the agent's system prompt). Humans parallel: things learned in school, things I did, and instincts/motor skil
- **Q068 · generation miss**: What does an MCP server expose?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly identifies that MCP servers expose tools, resources, and prompts, but it lacks the detailed explanation and examples of each category provided in the golden answer.
  - Bot: An MCP server exposes specific capabilities through the protocol, primarily exposing information such as tools, resources, and prompts to the client [1][3].
  - Golden: Three things: Tools – functions the client can invoke (search, send a message, update DB records); Resources – read-only data like files, database records or API responses; and Prompt Templates – predefined, well-tested templates for AI interactions, like document Q&A or transcript summaries.
- **Q069 · false refusal**: What is the difference between direct and templated resources in MCP?
  - Judge: correct=no, faithful=True, context recall=partial. The answer admits lack of knowledge and does not convey the key facts about direct and templated resources, which are partially present in the passages describing resources and their types but without explicit explanation of the difference.
  - Bot: I don't know. The passages mention that MCP resources can be of two types: Direct and Templated, but they do not explain the difference between them.
  - Golden: Resources expose data at a URI, similar to GET handlers in an HTTP server, and can set a mime_type hint. A direct resource has a fixed URI (e.g. docs://documents returning a list of documents), while a templated resource has a parameter in the URI (e.g. docs://documents/{doc_id} returning a specific
- **Q081 · incomplete retrieval**: What's overfitting vs underfitting?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly explains overfitting and underfitting with bias and variance but incorrectly states underfitting involves high variance instead of low variance; the passages contain partial information on these concepts but do not fully clarify the bias-variance details for underfitting.
  - Bot: Overfitting occurs when a machine learning model learns its training data too well, capturing not just the underlying patterns but also the noise and random fluctuations. This results in poor performance on new, unseen data. It is characterized by the model performing well with training data (low bi
  - Golden: Overfitting is when a model learns the training data too well, including noise, so it does well on training data (low bias) but poorly on new data (high variance). Underfitting is when it performs badly on both. The goal is a generalized model with low bias and low variance.

Per-question detail: `results/golden-v2/answers.jsonl`.
