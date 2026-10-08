# Answer-quality eval: `evals_followup.json`

Provider `openai` · chat `gpt-4.1-mini` · judge `gpt-4.1-mini` · retrieval `vector` k=3 · MIN_SIMILARITY=0.224 · chunks 350/50

## Summary

| metric | value | n |
|---|---|---|
| Correctness vs golden answer (judge) | 61% | 14 |
| Fully correct answers (judge = yes) | 50% | 14 |
| Faithfulness / no hallucination (judge) | 100% | 14 |
| Context recall (judge) | 86% | 14 |
| Answers with a citation | 93% | 14 |
| False refusals | 7% | 14 |
| Semantic similarity to golden (cosine) | 0.70 | 14 |
| Latency p50 / p95 | 3.0s / 25.4s | 14 |

## Outcome diagnosis

| outcome | questions |
|---|---|
| ok | 7 |
| generation miss | 3 |
| incomplete retrieval | 2 |
| retrieval miss | 1 |
| false refusal | 1 |

## By topic

| topic | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| RAG | 3 | 83% | 100% | 100% | 0.72 |
| Prompt Engineering | 2 | 25% | 100% | 75% | 0.81 |
| Context Engineering | 2 | 0% | 100% | 50% | 0.43 |
| MCP | 2 | 75% | 100% | 100% | 0.63 |
| Machine Learning | 2 | 100% | 100% | 100% | 0.82 |
| Agentic AI | 2 | 100% | 100% | 100% | 0.76 |
| LLM Fundamentals | 1 | 0% | 100% | 50% | 0.71 |

## By type

| type | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| follow-up | 14 | 61% | 100% | 86% | 0.70 |

## By difficulty

| difficulty | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| medium | 9 | 72% | 100% | 89% | 0.79 |
| hard | 3 | 33% | 100% | 83% | 0.50 |
| easy | 2 | 50% | 100% | 75% | 0.61 |

## Failures (7)

- **F01 · incomplete retrieval**: how is ChatGPT different from it?
  - Judge: correct=no, faithful=True, context recall=partial. The answer explains differences between ChatGPT, RAG, and MCP but does not address how ChatGPT differs from a base model via post-training stages like supervised fine-tuning and reinforcement learning as stated in the golden answer; the passages only partially cover this information.
  - Bot: ChatGPT differs from RAG (Retrieval-Augmented Generation) in that ChatGPT, as a traditional LLM, operates within a fixed context window and does not have direct access to external private data or documents unless that information is provided in the prompt. RAG, on the other hand, involves retrieving
  - Golden: ChatGPT is not just a base model. It has gone through post-training stages like supervised fine-tuning and reinforcement learning that turn the internet document simulator into an assistant that holds conversations and answers questions in a helpful, knowledgeable persona.
- **F02 · incomplete retrieval**: how is top-p different from that?
  - Judge: correct=no, faithful=True, context recall=partial. The answer incorrectly compares top-p to keyword search instead of temperature, which is the actual comparison asked for; the passages contain information about top-p and temperature but not about keyword search in this context.
  - Bot: Top-p differs from keyword search in that top-p controls the range of possible next words the model can choose from based on their cumulative probability, allowing for more diverse or predictable word choices by limiting the "bag" of next words to those that make up a certain probability mass (e.g.,
  - Golden: Temperature sharpens or spreads out all the probabilities, making output more or less random. Top-p (nucleus sampling) cuts off the least likely words: the model only picks from the smallest set of words whose combined probability reaches p (e.g. top-p 0.9 ignores the rarest 10%). Usually you keep o
- **F03 · generation miss**: what about chain of thought? is the zero-shot version different?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains zero-shot CoT as combining chain of thought prompting with zero-shot prompting and its benefit, but it omits the definition of chain-of-thought prompting itself as breaking complex reasoning into intermediate steps leading to a well-structured answer, which is present in the passages.
  - Bot: Zero-shot Chain of Thought (CoT) prompting combines chain of thought prompting with zero-shot prompting by asking the model to perform reasoning steps without prior examples, which may often produce better output compared to standard CoT prompting [2].
  - Golden: Chain-of-thought prompting asks the model to break complex reasoning into intermediate steps, leading to a more complete, well-structured answer. Zero-shot CoT combines this with zero-shot prompting – you give no examples but simply ask the model to reason step by step, which often improves output.
- **F04 · retrieval miss**: how is it different from prompt engineering?
  - Judge: correct=no, faithful=True, context recall=no. The answer only explains prompt engineering and prompt design without addressing context engineering or comparing it to prompt engineering as described in the golden answer; the passages do not contain information about context engineering or managing multi-turn context state.
  - Bot: Prompt engineering is the art and science of designing and optimizing prompts to guide AI models, particularly large language models (LLMs), towards generating the desired responses by providing context, instructions, and examples that help the model understand intent and respond meaningfully [1]. I
  - Golden: Prompt engineering focuses on writing effective prompts, especially system prompts, usually for single-turn queries. Context engineering manages the entire context state – system instructions, tools, MCP, external data, message history – for agents that run over many turns, constantly deciding what 
- **F05 · false refusal**: why does that happen?
  - Judge: correct=no, faithful=True, context recall=yes. The answer is a refusal and thus contains no key facts, while the passages provide detailed reasons why models lose focus with very long context.
  - Bot: I don't know.
  - Golden: LLMs use the transformer architecture, where every token attends to every other token, creating n² pairwise relationships. As context grows, attention gets stretched thin. Models also see shorter sequences more often in training, so they have less experience with very long dependencies. Techniques l
- **F07 · generation miss**: what are the embeddings it relies on, and what makes them?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains embeddings and embedding models and their role in semantic search, but it omits the example of the all-MiniLM-L6-v2 model producing 384-dimensional vectors present in the golden answer.
  - Bot: Embeddings are arrays of numbers (vectors) that represent the meaning of text by capturing different aspects of its content. They are created by embedding models, which are machine learning models designed to convert text into these numerical vectors. These vectors map sentences and paragraphs into 
  - Golden: An embedding model converts text into a vector – an array of numbers that represents its meaning. These vectors are coordinates in a high-dimensional space where text with similar meaning sits close together. For example, the all-MiniLM-L6-v2 model produces 384-dimensional vectors.
- **F10 · generation miss**: and what does the server expose?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states that the MCP server exposes tools, resources, and prompts, but it lacks the detailed explanation and examples of each category provided in the golden answer.
  - Bot: The MCP server exposes information such as tools, resources, and prompts to the client [1][3].
  - Golden: Three things: Tools – functions the client can invoke (search, send a message, update DB records); Resources – read-only data like files, database records or API responses; and Prompt Templates – predefined, well-tested templates for AI interactions, like document Q&A or transcript summaries.

Per-question detail: `results/followup-norewrite/answers.jsonl`.
