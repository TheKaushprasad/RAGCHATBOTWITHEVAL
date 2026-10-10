# Answer-quality eval: `evals_golden.json`

Provider `openai` · chat `gpt-4.1-mini` · judge `gpt-4.1-mini` · retrieval `vector` k=5 · reranker `llm` · MIN_SIMILARITY=0.224 · chunks 350/50

## Summary

| metric | value | n |
|---|---|---|
| Correctness vs golden answer (judge) | 93% | 96 |
| Fully correct answers (judge = yes) | 88% | 96 |
| Faithfulness / no hallucination (judge) | 100% | 96 |
| Context recall (judge) | 98% | 96 |
| Answers with a citation | 99% | 96 |
| False refusals | 1% | 96 |
| Semantic similarity to golden (cosine) | 0.77 | 96 |
| Out-of-scope handled correctly (judge) | 100% | 4 |
| Out-of-scope: said "I don't know" | 75% | 4 |
| Latency p50 / p95 | 4.3s / 5.5s | 100 |

## Outcome diagnosis

| outcome | questions |
|---|---|
| ok | 88 |
| generation miss | 9 |
| incomplete retrieval | 2 |
| refusal (retrieval miss) | 1 |

## By topic

| topic | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| LLM Fundamentals | 19 | 87% | 100% | 95% | 0.76 |
| RAG | 17 | 97% | 100% | 100% | 0.78 |
| Prompt Engineering | 16 | 88% | 100% | 100% | 0.75 |
| Machine Learning | 16 | 97% | 100% | 97% | 0.79 |
| MCP | 11 | 91% | 100% | 95% | 0.75 |
| Context Engineering | 10 | 100% | 100% | 100% | 0.78 |
| Agentic AI | 7 | 100% | 100% | 100% | 0.75 |
| Out of Scope | 4 | 100% | 100% | n/a | 0.53 |

## By type

| type | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| conceptual | 34 | 91% | 100% | 100% | 0.80 |
| comparison | 21 | 95% | 100% | 95% | 0.81 |
| procedural | 21 | 98% | 100% | 100% | 0.75 |
| factual | 18 | 89% | 100% | 94% | 0.68 |
| out_of_scope | 4 | 100% | 100% | n/a | 0.53 |
| calculation | 2 | 100% | 100% | 100% | 0.71 |

## By difficulty

| difficulty | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| medium | 56 | 92% | 100% | 97% | 0.76 |
| easy | 29 | 95% | 100% | 100% | 0.75 |
| hard | 15 | 97% | 100% | 97% | 0.78 |

## Failures (12)

- **Q001 · generation miss**: What exactly is an LLM, in simple words?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains that an LLM is a neural network predicting the next token based on statistical patterns learned from vast internet text and mentions its billions of parameters and assistant fine-tuning, but it omits the explicit description of tokens and the base model as a token simulator, which are key facts in the golden answer.
  - Bot: An LLM (Large Language Model) is a neural network designed to predict the next token in a sequence of text, effectively simulating how tokens follow each other statistically. It is trained on vast amounts of internet text and stores this knowledge in billions of parameters, allowing it to generate t
  - Golden: An LLM (Large Language Model) is a neural network that works as a very sophisticated text predictor. It is trained on huge amounts of text to learn the statistical patterns of how tokens follow each other, and then predicts the probability of the next token in a sequence.
- **Q008 · generation miss**: Why should I put the actual document in the prompt instead of trusting what the model already knows?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains that including the actual document in the prompt prevents hallucinations and enables accurate responses by providing necessary context, but it omits the key point from the golden answer that the model's stored knowledge is only a vague recollection and that the context window acts as the model's working memory for detailed answers.
  - Bot: You should put the actual document in the prompt because LLMs like ChatGPT cannot access private or external documents on their own and will hallucinate or provide incorrect answers without the necessary context. Providing the full document allows the model to refer to the exact information and gene
  - Golden: Because knowledge stored in the parameters is only a vague recollection. The context window acts as the model's working memory, so for accurate summaries or detailed answers the relevant information should be given explicitly in the context.
- **Q010 · refusal (retrieval miss)**: What steps are in the FineWeb data pipeline?
  - Judge: correct=no, faithful=True, context recall=no. The answer correctly states that the passages do not mention the FineWeb data pipeline or its steps, which matches the content of the passages that focus on a different data pipeline and chunking methods.
  - Bot: I don't know. The provided context passages do not mention the FineWeb data pipeline or its steps.
  - Golden: URL filtering (block malware, adult, spam sites) → text extraction → language filtering (e.g. keep pages with more than 50% English) → Gopher filtering (reliability and safety) → MinHash dedup (remove near-duplicates) → C4 filters → custom filters (based on model goals, safety, domain) → PII removal
- **Q016 · generation miss**: When I'm chatting with ChatGPT, who am I really talking to?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains that ChatGPT is a Large Language Model post-trained via supervised fine-tuning on human-labeled conversation data to act as a helpful assistant, but it omits the key point that it is effectively a statistical simulation of a human data labeler following company instructions, as stated in the golden answer.
  - Bot: When you are chatting with ChatGPT, you are really talking to a Large Language Model (LLM) that has been post-trained to act as a helpful, conversational assistant. Initially, the base model is trained on massive internet text to simulate token sequences statistically resembling internet documents. 
  - Golden: In effect, a statistical simulation of a human data labeler following the company's labeling instructions. The model learned its assistant persona by imitating those example conversations.
- **Q027 · generation miss**: Give me tips to write better prompts
  - Judge: correct=partial, faithful=True, context recall=yes. The answer covers the six key strategies from the golden answer and adds more detailed tips, some of which are not in the golden answer but are supported by the passages; however, it includes extra points beyond the six strategies, making it more extensive but still faithful and based on the passages.
  - Bot: Tips to write better prompts include:

1. Set clear goals and objectives for the prompt to guide the model effectively [1].

2. Provide context and background information to help the model understand the task [1][4].

3. Use few-shot prompting by including examples of desired input-output pairs to i
  - Golden: Six strategies: (1) set clear goals – use action verbs, define length/format, specify the audience; (2) provide context – relevant facts, sources, definitions; (3) use few-shot examples to show style and level of detail; (4) be specific – precise language, quantify requests, break tasks into steps; 
- **Q031 · generation miss**: What are the 10 steps in Anthropic's prompting framework?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly lists most of the 10 steps with accurate descriptions but omits 'Background data/documents/images' as a distinct step and adds an unnumbered step about controlling randomness and output length not explicitly in the golden list.
  - Bot: The 10 steps in Anthropic's prompting framework are:

1. Task Context: Clearly define the model’s role and what it is expected to do.
2. Tone Context
3. Show its Work: Ask the model to carefully examine step by step to show reasoning.
4. Incorporate Examples: Provide examples to improve accuracy and
  - Golden: 1. Task context, 2. Tone context, 3. Background data/documents/images, 4. Detailed task description and rules, 5. Examples, 6. Conversation history, 7. Immediate task description or request, 8. Thinking step by step, 9. Output formatting, 10. Prefilled response (if any).
- **Q032 · generation miss**: Why do people use XML tags in prompts?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states that XML tags specify output presentation for clarity and automation, but it omits that XML tags also help organize input sections for the model to refer back to, which is a key fact in the golden answer and supported by the passages.
  - Bot: People use XML tags in prompts to specify exactly how the output should be presented, ensuring clarity, consistency, and ease of automation. Wrapping the final output in clear delimiters such as XML tags helps structure the output so it can be easily processed or stored in a database [1][2].
  - Golden: LLMs work best with clearly organized input. Delimiters like XML tags (e.g. <user_preferences>) or Markdown separate and label sections so the model can refer back to them. Wrapping the final output in tags like <final_verdict> or using JSON also makes it consistent and easy to process automatically
- **Q033 · generation miss**: In the vehicle claims example, when is a car considered a total loss?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states the threshold and ratio condition for total loss but omits the detail about adding 'needs_manual_review' when the ratio is within ±0.05 of the threshold, which is present in the golden answer and supported by the passages.
  - Bot: A car is considered a total loss when the repair_to_market_ratio (repair cost divided by market value) is greater than or equal to the total_loss_threshold, which is 0.7 (70%) by default [1][4][8].
  - Golden: When the repair-to-market-value ratio (repair cost ÷ market value) is greater than or equal to the threshold, which defaults to 0.70. Below that the verdict is REPAIRABLE. If the ratio is within ±0.05 of the threshold, 'needs_manual_review' is added to the explanations.
- **Q054 · generation miss**: What are embeddings and embedding models?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains embeddings and embedding models and their role in semantic search, but it omits the example of the all-MiniLM-L6-v2 model producing 384-dimensional vectors mentioned in the golden answer.
  - Bot: Embeddings are numerical representations of text that capture its meaning. An embedding model is a machine learning model designed to convert text into arrays of numbers called vectors, which represent the meaning of the text in a high-dimensional space. These vectors allow documents or text segment
  - Golden: An embedding model converts text into a vector – an array of numbers that represents its meaning. These vectors are coordinates in a high-dimensional space where text with similar meaning sits close together. For example, the all-MiniLM-L6-v2 model produces 384-dimensional vectors.
- **Q063 · generation miss**: What is MCP?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly describes MCP as an open-source standard connecting AI applications to external systems and mentions its architecture and benefits, but it omits the key analogy of MCP being like a USB-C port for AI applications and does not explicitly mention that MCP connects to workflows like specialized prompts as in the golden answer.
  - Bot: MCP (Model Context Protocol) is an open-source standard for connecting AI applications to external systems, allowing AI models like Claude or ChatGPT to access data sources, tools, and workflows to perform tasks and access key information. It standardizes how models communicate with tools and contex
  - Golden: MCP (Model Context Protocol) is an open-source standard for connecting AI applications to external systems – data sources like files and databases, tools like search engines and calculators, and workflows like specialized prompts. It's like a USB-C port for AI applications: one standard way to conne
- **Q069 · incomplete retrieval**: What is the difference between direct and templated resources in MCP?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly states that direct resources provide data at a specified URI similar to HTTP GET handlers and can return various data types, but it fails to explain the key difference that templated resources have parameters in their URIs, which is present in the golden answer but missing in the passages.
  - Bot: Direct resources in MCP provide data at a specified URI or location directly, similar to GET request handlers in HTTP servers, and can return any data type such as string, JSON, or binary. Templated resources, by contrast, are another type of resource but the exact distinction is not detailed in the
  - Golden: Resources expose data at a URI, similar to GET handlers in an HTTP server, and can set a mime_type hint. A direct resource has a fixed URI (e.g. docs://documents returning a list of documents), while a templated resource has a parameter in the URI (e.g. docs://documents/{doc_id} returning a specific
- **Q081 · incomplete retrieval**: What's overfitting vs underfitting?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly explains overfitting and underfitting with respect to training and test performance and bias-variance, but adds that underfitting involves high variance which is not supported by the passages; the passages only mention high bias and high variance for underfitting without clarifying variance for underfitting, and the goal of a generalized model is only mentioned in the passages, not in the answer.
  - Bot: Overfitting occurs when a model performs well on training data (low bias) but poorly on test data (high variance), meaning it has learned the training data too well including noise, resulting in poor generalization [1][2]. Underfitting happens when the model performs poorly on both training and test
  - Golden: Overfitting is when a model learns the training data too well, including noise, so it does well on training data (low bias) but poorly on new data (high variance). Underfitting is when it performs badly on both. The goal is a generalized model with low bias and low variance.

Per-question detail: `results/golden-rerank-k5/answers.jsonl`.
