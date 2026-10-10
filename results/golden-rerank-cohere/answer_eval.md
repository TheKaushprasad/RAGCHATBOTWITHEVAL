# Answer-quality eval: `evals_golden.json`

Provider `openai` · chat `gpt-4.1-mini` · judge `gpt-4.1-mini` · retrieval `vector` k=3 · reranker `cohere` · MIN_SIMILARITY=0.224 · chunks 350/50

## Summary

| metric | value | n |
|---|---|---|
| Correctness vs golden answer (judge) | 89% | 96 |
| Fully correct answers (judge = yes) | 80% | 96 |
| Faithfulness / no hallucination (judge) | 99% | 96 |
| Context recall (judge) | 95% | 96 |
| Answers with a citation | 98% | 96 |
| False refusals | 1% | 96 |
| Semantic similarity to golden (cosine) | 0.76 | 96 |
| Out-of-scope handled correctly (judge) | 100% | 4 |
| Out-of-scope: said "I don't know" | 100% | 4 |
| Latency p50 / p95 | 5.5s / 6.7s | 100 |

## Outcome diagnosis

| outcome | questions |
|---|---|
| ok | 81 |
| generation miss | 11 |
| incomplete retrieval | 5 |
| refusal (retrieval miss) | 1 |
| hallucination | 1 |
| retrieval miss | 1 |

## By topic

| topic | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| LLM Fundamentals | 19 | 84% | 100% | 87% | 0.74 |
| RAG | 17 | 91% | 100% | 100% | 0.78 |
| Prompt Engineering | 16 | 88% | 94% | 100% | 0.76 |
| Machine Learning | 16 | 84% | 100% | 91% | 0.74 |
| MCP | 11 | 82% | 100% | 95% | 0.75 |
| Context Engineering | 10 | 100% | 100% | 100% | 0.78 |
| Agentic AI | 7 | 100% | 100% | 100% | 0.76 |
| Out of Scope | 4 | 100% | 100% | n/a | 0.51 |

## By type

| type | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| conceptual | 34 | 87% | 100% | 96% | 0.78 |
| comparison | 21 | 93% | 100% | 95% | 0.80 |
| procedural | 21 | 93% | 100% | 98% | 0.74 |
| factual | 18 | 83% | 100% | 92% | 0.68 |
| out_of_scope | 4 | 100% | 100% | n/a | 0.51 |
| calculation | 2 | 75% | 50% | 100% | 0.79 |

## By difficulty

| difficulty | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| medium | 56 | 87% | 100% | 94% | 0.74 |
| easy | 29 | 93% | 100% | 98% | 0.75 |
| hard | 15 | 90% | 93% | 97% | 0.77 |

## Failures (19)

- **Q008 · generation miss**: Why should I put the actual document in the prompt instead of trusting what the model already knows?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states that the model cannot access private documents and may hallucinate without context, but it omits the explanation that knowledge in parameters is a vague recollection and that the context window acts as working memory for accuracy.
  - Bot: You should put the actual document in the prompt instead of trusting what the model already knows because the model cannot access private or specific documents on its own and will typically hallucinate or provide incorrect or generic answers without the necessary context. By including the entire doc
  - Golden: Because knowledge stored in the parameters is only a vague recollection. The context window acts as the model's working memory, so for accurate summaries or detailed answers the relevant information should be given explicitly in the context.
- **Q009 · incomplete retrieval**: What are the main stages of building an LLM like ChatGPT?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly describes pretraining and supervised fine-tuning stages but omits the reinforcement learning stage and the term 'post-training' encompassing both SFT and RL, which are present in the golden answer and partially supported by the passages.
  - Bot: The main stages of building an LLM like ChatGPT are:

1. The Pretraining Stage: This is the first and most computationally demanding stage where the neural network acquires foundational knowledge by internalizing statistical patterns of token sequences from massive amounts of text. The output is a b
  - Golden: Three stages: (1) Pre-training, which creates the base model from massive internet text; (2) Supervised Fine-Tuning (SFT), which teaches it to behave like a conversational assistant; and (3) Reinforcement Learning (RL), which improves problem-solving and leads to reasoning. SFT and RL together are c
- **Q010 · refusal (retrieval miss)**: What steps are in the FineWeb data pipeline?
  - Judge: correct=no, faithful=True, context recall=no. The answer correctly states lack of knowledge, which is faithful to the passages, but the passages do not contain any information about the FineWeb data pipeline steps, so the answer cannot provide the golden answer details.
  - Bot: I don't know. The provided context does not mention the FineWeb data pipeline or its steps.
  - Golden: URL filtering (block malware, adult, spam sites) → text extraction → language filtering (e.g. keep pages with more than 50% English) → Gopher filtering (reliability and safety) → MinHash dedup (remove near-duplicates) → C4 filters → custom filters (based on model goals, safety, domain) → PII removal
- **Q016 · incomplete retrieval**: When I'm chatting with ChatGPT, who am I really talking to?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly explains ChatGPT as a Large Language Model trained on internet text and fine-tuned as an assistant, but it omits the key fact that it simulates a human data labeler following labeling instructions, which is central to the golden answer; the passages do not mention the human data labeler simulation explicitly.
  - Bot: When you are chatting with ChatGPT, you are talking to a Large Language Model (LLM), which is fundamentally a neural network designed to be a highly sophisticated predictive system for text. It predicts the probability of the next token in a sequence based on statistical relationships learned during
  - Golden: In effect, a statistical simulation of a human data labeler following the company's labeling instructions. The model learned its assistant persona by imitating those example conversations.
- **Q017 · incomplete retrieval**: What happens in the reinforcement learning stage?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly describes the RL stage as training via trial and error with rewards and penalties and mentions the model receiving the prompt and final answer but not the solution, but it adds details about internal cognitive strategies and advanced reasoning not fully supported by the passages, and the passages only partially cover the exact process of generating candidate solutions and training on successful token sequences.
  - Bot: In the reinforcement learning (RL) stage, the model is trained to make decisions by interacting with an environment, learning through trial and error, and receiving rewards for good actions and penalties for bad ones. Over time, it develops strategies to maximize rewards and achieve goals. This stag
  - Golden: The model is given a prompt and the correct final answer but not the solution. It generates many candidate solutions (rollouts), these are scored as successful or not, and the model is trained on the token sequences that led to correct answers. In the school analogy, this is like a student doing pra
- **Q027 · generation miss**: Give me tips to write better prompts
  - Judge: correct=partial, faithful=True, context recall=yes. The answer covers the six key strategies from the golden answer and adds extra tips supported by the passages, but it includes additional points not in the golden answer and omits some specific details like defining length/format and specifying the audience.
  - Bot: Tips to write better prompts include:

1. Set clear goals and objectives to define what you want from the model [1].

2. Provide context and background information to help the model understand the task [1].

3. Use few-shot prompting by providing examples of desired input-output pairs to improve acc
  - Golden: Six strategies: (1) set clear goals – use action verbs, define length/format, specify the audience; (2) provide context – relevant facts, sources, definitions; (3) use few-shot examples to show style and level of detail; (4) be specific – precise language, quantify requests, break tasks into steps; 
- **Q031 · generation miss**: What are the 10 steps in Anthropic's prompting framework?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer covers most of the key steps from the passages but omits 'Background data/documents/images' and slightly misorders or combines some steps, with step 10 not explicitly listed in the passages but implied.
  - Bot: The 10 steps in Anthropic's prompting framework are:

1. Task Context: Clearly define the model’s role and expected task.
2. Tone Context
3. Show its Work: Encourage the model to show intermediate reasoning.
4. Incorporate Examples: Provide examples to improve accuracy.
5. Adding Conversation Histor
  - Golden: 1. Task context, 2. Tone context, 3. Background data/documents/images, 4. Detailed task description and rules, 5. Examples, 6. Conversation history, 7. Immediate task description or request, 8. Thinking step by step, 9. Output formatting, 10. Prefilled response (if any).
- **Q033 · generation miss**: In the vehicle claims example, when is a car considered a total loss?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states the threshold and condition for total loss but omits the details about the verdict being REPAIRABLE below the threshold and the 'needs_manual_review' explanation for ratios near the threshold.
  - Bot: A car is considered a total loss when the repair cost is greater than or equal to 70% (0.70) of the vehicle's market value, as per the total_loss_threshold. This means if the repair_to_market_ratio is ≥ 0.7, the verdict is "TOTAL_LOSS" [1][2].
  - Golden: When the repair-to-market-value ratio (repair cost ÷ market value) is greater than or equal to the threshold, which defaults to 0.70. Below that the verdict is REPAIRABLE. If the ratio is within ±0.05 of the threshold, 'needs_manual_review' is added to the explanations.
- **Q034 · hallucination**: For the Maruti Swift example (E2), how was the payable amount 370000 calculated?
  - Judge: correct=partial, faithful=False, context recall=yes. The answer incorrectly states the repair cost as 380,000 instead of 390,000 and the ratio as 0.76 instead of 0.78, which conflicts with the passages; however, it correctly computes the payable amount as 370,000 and identifies the verdict as TOTAL_LOSS, and the passages contain the needed information.
  - Bot: {
  "claim_id": "E2",
  "verdict": "TOTAL_LOSS",
  "repair_cost": 380000,
  "market_value": 500000,
  "market_value_source": "estimated_from_valuation_table_2025",
  "repair_to_market_ratio": 0.76,
  "total_loss_threshold": 0.7,
  "total_loss": true,
  "salvage_value": 20000,
  "payable_amount": 370
  - Golden: Repair cost = parts 350,000 + labour 30,000 = 390,000. Ratio = 390,000 / 500,000 = 0.78, which is ≥ 0.70, so it's a TOTAL_LOSS. Payable amount = repair cost − salvage value = 390,000 − 20,000 = 370,000 (never below 0).
- **Q047 · generation miss**: why can't chatgpt answer questions about my company's policy?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states ChatGPT lacks access to private documents causing hallucination and mentions MCP as a solution, but the golden answer specifically highlights RAG as the fix, which the answer does not mention.
  - Bot: ChatGPT cannot answer questions about your company's policy because it lacks access to the private document containing that policy and thus lacks the necessary context, which often leads to hallucination or incorrect answers [1]. MCP (Model Context Protocol) exists to address this limitation by enab
  - Golden: Because it has no access to your private documents. Without that context it will usually hallucinate and give a generic or wrong answer. RAG fixes this by retrieving the relevant policy content and giving it to the model with the question.
- **Q051 · generation miss**: How does keyword search work?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains keyword search by identifying keywords, counting occurrences, and ranking documents, and mentions TF-IDF and BM25, but it incorrectly states TF instead of TF-IDF as a popular approach and slightly misrepresents the combination of counts as selecting the single document with maximum occurrences rather than ranking documents.
  - Bot: Keyword search works by identifying keywords from the user's query and ranking documents based on the occurrence and frequency of those keywords within them. The system counts the occurrences of each keyword in all documents and combines these counts to select the document with the maximum occurrenc
  - Golden: It finds the keywords from the query in all documents, counts how often each appears, and ranks documents by those occurrences. Popular methods are TF-IDF, which scores the importance of each word, and BM25, which is stricter and scores the most important and unique words.
- **Q054 · generation miss**: What are embeddings and embedding models?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains embeddings and embedding models and their role in semantic search, but it omits the example of the all-MiniLM-L6-v2 model producing 384-dimensional vectors present in the golden answer.
  - Bot: Embeddings are arrays of numbers (vectors) that represent the meaning of text by capturing different aspects of its content. Embedding models are machine learning models that convert text into these numerical vectors, mapping sentences and paragraphs into a high-dimensional dense vector space where 
  - Golden: An embedding model converts text into a vector – an array of numbers that represents its meaning. These vectors are coordinates in a high-dimensional space where text with similar meaning sits close together. For example, the all-MiniLM-L6-v2 model produces 384-dimensional vectors.
- **Q063 · generation miss**: What is MCP?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states MCP is an open-source standard by Anthropic for connecting AI applications to external systems and standardizing communication safely and modularly, but it omits the analogy to USB-C and the specific examples of data sources, tools, and workflows mentioned in the golden answer.
  - Bot: MCP (Model Context Protocol) is an open-source standard introduced by Anthropic for connecting AI applications to external systems such as data sources, tools, and workflows. It standardizes how models communicate with tools and context providers safely and modularly, enabling AI applications to acc
  - Golden: MCP (Model Context Protocol) is an open-source standard for connecting AI applications to external systems – data sources like files and databases, tools like search engines and calculators, and workflows like specialized prompts. It's like a USB-C port for AI applications: one standard way to conne
- **Q068 · generation miss**: What does an MCP server expose?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states that an MCP server exposes tools, resources, and prompts, but it lacks the detailed explanation and examples of each category provided in the golden answer.
  - Bot: An MCP server exposes specific capabilities through the protocol, including information such as tools, resources, and prompts to the client [1][2].
  - Golden: Three things: Tools – functions the client can invoke (search, send a message, update DB records); Resources – read-only data like files, database records or API responses; and Prompt Templates – predefined, well-tested templates for AI interactions, like document Q&A or transcript summaries.
- **Q069 · incomplete retrieval**: What is the difference between direct and templated resources in MCP?
  - Judge: correct=no, faithful=True, context recall=partial. The answer correctly states that the context does not explain the specific difference between direct and templated resources, but it fails to convey the key facts from the golden answer about URIs and mime_type hints.
  - Bot: Direct and templated resources in MCP are two types of resources that an MCP server can expose to a client. However, the provided context does not explain the specific difference between direct and templated resources, only that resources can be of these two types [1][2].
  - Golden: Resources expose data at a URI, similar to GET handlers in an HTTP server, and can set a mime_type hint. A direct resource has a fixed URI (e.g. docs://documents returning a list of documents), while a templated resource has a parameter in the URI (e.g. docs://documents/{doc_id} returning a specific
- **Q076 · generation miss**: Why does an AI PM need to understand machine learning?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer covers many key points from the golden answer such as assessing problem fit, translating business problems, planning data needs, communicating with data scientists, and managing expectations, but it omits managing the ML lifecycle (monitoring data drift, retraining, A/B testing) and responsible AI issues like bias and explainability.
  - Bot: An AI Product Manager (AI PM) needs to understand machine learning (ML) because it is the fundamental technology underlying most AI products, enabling them to effectively define, develop, and manage these products [1][2]. Specifically, ML knowledge helps the AI PM to:

- Define and scope the product
  - Golden: To assess whether a problem fits ML and translate business problems into ML tasks; to plan data needs; to talk with data scientists about features and metrics like precision and recall and set realistic expectations since models are probabilistic; to manage the lifecycle – monitoring data drift, ret
- **Q081 · incomplete retrieval**: What's overfitting vs underfitting?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly explains overfitting and underfitting with respect to training and test performance and bias/variance, but incorrectly states underfitting involves high variance instead of low variance; the passages do not mention noise in overfitting explicitly, and the goal of a generalized model with low bias and low variance is only in the passages, not in the answer.
  - Bot: Overfitting occurs when a model performs well on training data (low bias) but poorly on test data (high variance) because it captures noise and random fluctuations in the training data [1][2]. Underfitting happens when a model has bad accuracy on both training and test data, indicating high bias and
  - Golden: Overfitting is when a model learns the training data too well, including noise, so it does well on training data (low bias) but poorly on new data (high variance). Underfitting is when it performs badly on both. The goal is a generalized model with low bias and low variance.
- **Q084 · generation miss**: How does KNN make a prediction?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains KNN's prediction steps and distance metrics, but omits that K is often tuned by testing values like 1–50 and that KNN is a 'lazy' learner storing data until prediction time.
  - Bot: KNN makes a prediction by first determining the value of K, which specifies the number of nearest points to consider. Then, it calculates the distance between the new data point and existing points using distance metrics like Euclidean or Manhattan distance. For classification problems, KNN predicts
  - Golden: Pick K, the number of neighbors (a hyperparameter often tuned by testing values like 1–50). Measure distance from the new point to existing points using Euclidean or Manhattan distance. For classification, take a majority vote among the K nearest neighbors; for regression, average their values. It's
- **Q089 · retrieval miss**: how do you check if clusters are any good when there are no labels?
  - Judge: correct=no, faithful=True, context recall=no. The answer refuses to provide information, but the passages do not contain details about the Silhouette Score or methods to evaluate clusters without labels.
  - Bot: The provided context does not contain information on how to check if clusters are any good when there are no labels.
  - Golden: Use the Silhouette Score. It measures cohesion (how close points are within their cluster) and separation (how far clusters are from each other), giving a quantitative way to validate unsupervised clustering.

Per-question detail: `results/golden-rerank-cohere/answers.jsonl`.
