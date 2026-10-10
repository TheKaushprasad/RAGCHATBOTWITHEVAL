# Answer-quality eval: `evals_golden.json`

Provider `openai` · chat `gpt-4.1-mini` · judge `gpt-4.1-mini` · retrieval `vector` k=3 · reranker `llm` · MIN_SIMILARITY=0.224 · chunks 350/50

## Summary

| metric | value | n |
|---|---|---|
| Correctness vs golden answer (judge) | 93% | 96 |
| Fully correct answers (judge = yes) | 89% | 96 |
| Faithfulness / no hallucination (judge) | 100% | 96 |
| Context recall (judge) | 98% | 96 |
| Answers with a citation | 99% | 96 |
| False refusals | 1% | 96 |
| Semantic similarity to golden (cosine) | 0.76 | 96 |
| Out-of-scope handled correctly (judge) | 100% | 4 |
| Out-of-scope: said "I don't know" | 100% | 4 |
| Latency p50 / p95 | 4.2s / 5.7s | 100 |

## Outcome diagnosis

| outcome | questions |
|---|---|
| ok | 89 |
| generation miss | 7 |
| incomplete retrieval | 3 |
| false refusal | 1 |

## By topic

| topic | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| LLM Fundamentals | 19 | 87% | 100% | 97% | 0.76 |
| RAG | 17 | 91% | 100% | 100% | 0.75 |
| Prompt Engineering | 16 | 91% | 100% | 94% | 0.75 |
| Machine Learning | 16 | 100% | 100% | 100% | 0.78 |
| MCP | 11 | 91% | 100% | 95% | 0.73 |
| Context Engineering | 10 | 100% | 100% | 100% | 0.78 |
| Agentic AI | 7 | 100% | 100% | 100% | 0.76 |
| Out of Scope | 4 | 100% | 100% | n/a | 0.50 |

## By type

| type | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| conceptual | 34 | 94% | 100% | 100% | 0.80 |
| comparison | 21 | 93% | 100% | 98% | 0.79 |
| procedural | 21 | 100% | 100% | 100% | 0.74 |
| factual | 18 | 83% | 100% | 92% | 0.67 |
| out_of_scope | 4 | 100% | 100% | n/a | 0.50 |
| calculation | 2 | 100% | 100% | 100% | 0.70 |

## By difficulty

| difficulty | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| medium | 56 | 94% | 100% | 98% | 0.75 |
| easy | 29 | 93% | 100% | 98% | 0.73 |
| hard | 15 | 93% | 100% | 97% | 0.76 |

## Failures (11)

- **Q001 · generation miss**: What exactly is an LLM, in simple words?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains that an LLM is a neural network predicting the next token based on statistical patterns learned from vast internet text, but it omits the explicit mention that it is a very sophisticated text predictor and does not clearly state that the prediction is probabilistic; it also adds some details about parameters and assistant fine-tuning that are supported by the passages.
  - Bot: An LLM (Large Language Model) is a neural network designed to predict the next token in a sequence of text, effectively simulating how tokens follow each other statistically. It is trained on vast amounts of internet text to learn these patterns and stores this knowledge in billions of parameters. T
  - Golden: An LLM (Large Language Model) is a neural network that works as a very sophisticated text predictor. It is trained on huge amounts of text to learn the statistical patterns of how tokens follow each other, and then predicts the probability of the next token in a sequence.
- **Q009 · generation miss**: What are the main stages of building an LLM like ChatGPT?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly describes pretraining and supervised fine-tuning stages with details from the passages but omits the third stage, Reinforcement Learning, mentioned in the golden answer.
  - Bot: The main stages of building an LLM like ChatGPT are:

1. The Pretraining Stage: This is the first and most computationally demanding stage where the neural network acquires foundational knowledge by internalizing statistical patterns of token sequences from massive text data. It involves steps like 
  - Golden: Three stages: (1) Pre-training, which creates the base model from massive internet text; (2) Supervised Fine-Tuning (SFT), which teaches it to behave like a conversational assistant; and (3) Reinforcement Learning (RL), which improves problem-solving and leads to reasoning. SFT and RL together are c
- **Q010 · incomplete retrieval**: What steps are in the FineWeb data pipeline?
  - Judge: correct=no, faithful=True, context recall=partial. The answer describes the FineWeb data pipeline steps related to document chunking, embedding generation, and vector database storage, which are not the steps listed in the golden answer; the passages provide information on chunking and embedding but do not cover the FineWeb pipeline steps such as URL filtering, language filtering, or PII removal.
  - Bot: The FineWeb data pipeline includes the following steps:

1. Document Chunking: Large documents are broken into smaller chunks, typically fixed size (e.g., 500 characters) with overlap (e.g., 50 characters) to preserve context and improve precision [1][2].

2. Embedding Generation: The text chunks ar
  - Golden: URL filtering (block malware, adult, spam sites) → text extraction → language filtering (e.g. keep pages with more than 50% English) → Gopher filtering (reliability and safety) → MinHash dedup (remove near-duplicates) → C4 filters → custom filters (based on model goals, safety, domain) → PII removal
- **Q016 · generation miss**: When I'm chatting with ChatGPT, who am I really talking to?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains that ChatGPT is a large language model transformed into a conversational assistant via supervised fine-tuning, but it omits that this assistant is effectively a statistical simulation of a human data labeler following company instructions, which is a key fact in the golden answer.
  - Bot: When chatting with ChatGPT, you are talking to an assistant that is a Large Language Model (LLM) which has been transformed from a base model (an internet document simulator) into a helpful, conversational assistant through post-training stages like Supervised Fine-Tuning (SFT). This assistant is pr
  - Golden: In effect, a statistical simulation of a human data labeler following the company's labeling instructions. The model learned its assistant persona by imitating those example conversations.
- **Q023 · generation miss**: What are system instructions used for?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states that system instructions dictate style, tone, constraints, and behavior control, but it omits that these instructions are passed before any user input via a dedicated systemInstruction parameter and does not provide the illustrative example given in the golden answer.
  - Bot: System instructions are used to dictate the style and tone of the model, add constraints to what it can and can't talk about, and control its behavior based on rules and user requests to ensure safe and professional responses [1][2][3].
  - Golden: They are instructions passed to the model before any user input, usually through a dedicated systemInstruction parameter. They set the model's style, tone and constraints – for example, making it play a pirate dog character that only talks about pirate topics and ends every message with 'woof!'.
- **Q031 · incomplete retrieval**: What are the 10 steps in Anthropic's prompting framework?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer lists the 10 steps mostly correctly but omits details for steps 3 and 4, which are present in the passages; the passages provide partial but not full detail for all steps.
  - Bot: The 10 steps in Anthropic's prompting framework are:

1. Task Context  
2. Tone Context  
3. (Not provided in the excerpts)  
4. (Not provided in the excerpts)  
5. Incorporate Examples  
6. Adding Conversation History  
7. Immediate Task Description or Request  
8. Thinking Step-by-Step  
9. Output
  - Golden: 1. Task context, 2. Tone context, 3. Background data/documents/images, 4. Detailed task description and rules, 5. Examples, 6. Conversation history, 7. Immediate task description or request, 8. Thinking step by step, 9. Output formatting, 10. Prefilled response (if any).
- **Q033 · incomplete retrieval**: In the vehicle claims example, when is a car considered a total loss?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly states the threshold ratio for total loss but omits the default threshold value, the REPAIRABLE verdict below the threshold, and the 'needs_manual_review' explanation for ratios near the threshold, which are present in the golden answer and partially supported by the passages.
  - Bot: A car is considered a total loss when the repair cost to market value ratio is greater than or equal to 0.7 (70%) [1][3].
  - Golden: When the repair-to-market-value ratio (repair cost ÷ market value) is greater than or equal to the threshold, which defaults to 0.70. Below that the verdict is REPAIRABLE. If the ratio is within ±0.05 of the threshold, 'needs_manual_review' is added to the explanations.
- **Q048 · generation miss**: What do R, A and G stand for in RAG?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly identifies what R, A, and G stand for but omits the detailed explanations of each component provided in the passages and golden answer.
  - Bot: R, A, and G in RAG stand for Retrieval, Augmentation, and Generation respectively [1][2].
  - Golden: Retrieval – looking up internal documents or knowledge bases and fetching the relevant information. Augmentation – adding that retrieved information to the user's prompt. Generation – the LLM writes the final answer based on the augmented prompt.
- **Q049 · generation miss**: When should I use RAG vs fine tuning vs prompt engineering?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains RAG and fine-tuning uses with examples and mechanisms, but does not specify prompt engineering's use as behavioral rules and restrictions, which is in the golden answer.
  - Bot: RAG should be used when you need the most accurate, dynamic, and current factual information by retrieving relevant external documents at query time. It involves three steps: Retrieval of relevant documents, Augmentation of the prompt with this information, and Generation of the answer by the LLM. A
  - Golden: Use RAG for dynamic factual information that may change, like internal policies, retrieved at query time. Use fine-tuning to teach stable patterns like communication style, tone and jargon (e.g. making a bot speak in the CEO's voice). Use prompt engineering for behavioral rules and restrictions – wh
- **Q054 · generation miss**: What are embeddings and embedding models?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains embeddings and embedding models and their role in semantic search, but it omits the example of the all-MiniLM-L6-v2 model producing 384-dimensional vectors present in the golden answer.
  - Bot: Embeddings are arrays of numbers (vectors) that represent the meaning of text by capturing different aspects of its content. Embedding models are machine learning models designed to convert text into these numerical vectors, mapping sentences and paragraphs into a high-dimensional dense vector space
  - Golden: An embedding model converts text into a vector – an array of numbers that represents its meaning. These vectors are coordinates in a high-dimensional space where text with similar meaning sits close together. For example, the all-MiniLM-L6-v2 model produces 384-dimensional vectors.
- **Q069 · false refusal**: What is the difference between direct and templated resources in MCP?
  - Judge: correct=no, faithful=True, context recall=partial. The answer refuses to provide information despite the passages containing partial details about resources and their types, but the key distinction between direct and templated resources is not fully explained in the passages.
  - Bot: I don't know. The provided context does not explain the difference between direct and templated resources in MCP.
  - Golden: Resources expose data at a URI, similar to GET handlers in an HTTP server, and can set a mime_type hint. A direct resource has a fixed URI (e.g. docs://documents returning a list of documents), while a templated resource has a parameter in the URI (e.g. docs://documents/{doc_id} returning a specific

Per-question detail: `results/golden-rerank/answers.jsonl`.
