# Answer-quality eval: `evals_golden.json`

Provider `openai` · chat `gpt-5.4-nano` · judge `openai:gpt-4.1-mini` · retrieval `vector` k=5 · reranker `llm` · MIN_SIMILARITY=0.224 · chunks 350/50

## Summary

| metric | value | n |
|---|---|---|
| Correctness vs golden answer (judge) | 82% | 96 |
| Fully correct answers (judge = yes) | 73% | 96 |
| Faithfulness / no hallucination (judge) | 99% | 96 |
| Context recall (judge) | 95% | 96 |
| Answers with a citation | 92% | 96 |
| False refusals | 8% | 96 |
| Semantic similarity to golden (cosine) | 0.76 | 96 |
| Out-of-scope handled correctly (judge) | 100% | 4 |
| Out-of-scope: said "I don't know" | 100% | 4 |
| Latency p50 / p95 | 4.6s / 5.9s | 100 |

## Outcome diagnosis

| outcome | questions |
|---|---|
| ok | 73 |
| generation miss | 17 |
| false refusal | 7 |
| refusal (retrieval miss) | 1 |
| incomplete retrieval | 1 |
| hallucination | 1 |

## By topic

| topic | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| LLM Fundamentals | 19 | 71% | 100% | 95% | 0.73 |
| RAG | 17 | 79% | 100% | 94% | 0.75 |
| Prompt Engineering | 16 | 78% | 100% | 97% | 0.76 |
| Machine Learning | 16 | 91% | 100% | 97% | 0.78 |
| MCP | 11 | 73% | 100% | 95% | 0.73 |
| Context Engineering | 10 | 100% | 100% | 100% | 0.79 |
| Agentic AI | 7 | 100% | 86% | 86% | 0.75 |
| Out of Scope | 4 | 100% | 100% | n/a | 0.52 |

## By type

| type | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| conceptual | 34 | 88% | 97% | 97% | 0.79 |
| comparison | 21 | 74% | 100% | 93% | 0.78 |
| procedural | 21 | 93% | 100% | 98% | 0.75 |
| factual | 18 | 72% | 100% | 94% | 0.66 |
| out_of_scope | 4 | 100% | 100% | n/a | 0.52 |
| calculation | 2 | 50% | 100% | 75% | 0.72 |

## By difficulty

| difficulty | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| medium | 56 | 83% | 100% | 95% | 0.74 |
| easy | 29 | 84% | 97% | 96% | 0.75 |
| hard | 15 | 80% | 100% | 93% | 0.76 |

## Failures (27)

- **Q001 · generation miss**: What exactly is an LLM, in simple words?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states that an LLM is a neural network designed as a sophisticated predictive system for text, but it omits the explanation that it learns statistical patterns of token sequences and predicts the probability of the next token, which is present in the passages and golden answer.
  - Bot: An LLM (Large Language Model) is a neural network designed to be a highly sophisticated predictive system for text. [1]
  - Golden: An LLM (Large Language Model) is a neural network that works as a very sophisticated text predictor. It is trained on huge amounts of text to learn the statistical patterns of how tokens follow each other, and then predicts the probability of the next token in a sequence.
- **Q005 · generation miss**: Why should a product manager bother learning about LLMs?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states that PMs should learn about LLMs for their limitations and reliable deployment, but it omits specific details about stochasticity, hallucinations, vague knowledge, Swiss cheese capability gaps, and token-based thinking that are present in the golden answer and passages.
  - Bot: A product manager should learn about LLMs not just for their capabilities, but specifically for their limitations and the proper techniques required to deploy them effectively and reliably. [1]
  - Golden: Mainly to understand their limitations and how to deploy them reliably. LLMs are stochastic and can't be fully trusted, they hallucinate, their built-in knowledge is only a vague recollection, they have 'Swiss cheese' gaps in capability, and they need tokens to think. A PM needs this to design safeg
- **Q008 · generation miss**: Why should I put the actual document in the prompt instead of trusting what the model already knows?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains that the model lacks access to private documents and may hallucinate without context, and that providing the document gives necessary context for accurate answers, but it omits the key point that the model's stored knowledge is only a vague recollection and that the context window acts as working memory for accuracy.
  - Bot: You should put the actual document in the prompt instead of trusting what the model already knows because the model may not have the necessary context for private or specific information and will typically hallucinate (provide an incorrect or generic answer) when it cannot access that private docume
  - Golden: Because knowledge stored in the parameters is only a vague recollection. The context window acts as the model's working memory, so for accurate summaries or detailed answers the relevant information should be given explicitly in the context.
- **Q009 · generation miss**: What are the main stages of building an LLM like ChatGPT?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly identifies the three main stages and that RL is part of post-training, but it does not explicitly mention Supervised Fine-Tuning (SFT) as a separate stage within post-training or describe the purpose of each stage as clearly as the golden answer.
  - Bot: The main stages of building an LLM like ChatGPT are: (1) the Pretraining Stage, (2) the post-training stage, and (3) Reinforcement Learning (RL) as the third major stage within the post-training umbrella. [1][4][5]
  - Golden: Three stages: (1) Pre-training, which creates the base model from massive internet text; (2) Supervised Fine-Tuning (SFT), which teaches it to behave like a conversational assistant; and (3) Reinforcement Learning (RL), which improves problem-solving and leads to reasoning. SFT and RL together are c
- **Q010 · refusal (retrieval miss)**: What steps are in the FineWeb data pipeline?
  - Judge: correct=no, faithful=True, context recall=no. The answer admits lack of knowledge and does not provide the FineWeb data pipeline steps, which are not present in the passages.
  - Bot: I don't know. The provided passages describe a “Phase 1: The Data Preparation Pipeline (Ingestion)” for RAG (including Document Chunking, Embedding Generation, and Storage in a Vector Database), but they do not mention a “FineWeb data pipeline” or list its specific steps.
  - Golden: URL filtering (block malware, adult, spam sites) → text extraction → language filtering (e.g. keep pages with more than 50% English) → Gopher filtering (reliability and safety) → MinHash dedup (remove near-duplicates) → C4 filters → custom filters (based on model goals, safety, domain) → PII removal
- **Q011 · generation miss**: What is tokenization?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly defines tokenization as converting raw text into tokens used by LLMs, but it omits details about the one-dimensional sequence requirement and unique token IDs mentioned in the golden answer and passages.
  - Bot: Tokenization is the process of converting raw text into smaller units called tokens, which are the building blocks LLMs use to understand and generate language. [3]
  - Golden: Tokenization is converting raw text into smaller units called tokens. Neural networks need a one-dimensional sequence of symbols from a finite set, so text is turned into tokens, each with a unique ID, which are the building blocks the LLM reads and generates.
- **Q014 · false refusal**: How long does fine-tuning take compared to pre-training?
  - Judge: correct=no, faithful=True, context recall=yes. The answer correctly states that SFT takes around 3 hours and pre-training about three months, but it misses mentioning the cost difference and that post-training is far cheaper, which are key points in the golden answer.
  - Bot: I don't know. The passages state that Supervised Fine-Tuning (SFT) often takes around 3 hours compared to pre-training which can take roughly three months, but they do not explicitly state how long “fine-tuning” (in general) takes compared to pre-training. [2][3]
  - Golden: Much less. SFT often takes around 3 hours, while pre-training can take roughly three months. Pre-training needs most of the compute and millions of dollars; post-training is far cheaper.
- **Q015 · generation miss**: Who writes the conversations used to fine-tune an assistant?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states that human labelers hired by companies create the conversations for supervised fine-tuning, but it omits that these labelers write both prompts and ideal assistant responses following detailed instructions emphasizing helpfulness, truthfulness, and harmlessness, and that modern datasets often include millions of synthetic conversations generated and then edited by humans.
  - Bot: Human labelers (human contractors or laborers hired by companies) create the conversations used for supervised fine-tuning (SFT). [2]
  - Golden: Human labelers hired by the company write prompts and ideal assistant responses, following detailed labeling instructions that ask for helpful, truthful and harmless answers. Today LLMs also help create these datasets, so they often contain millions of synthetic conversations that humans then edit.
- **Q016 · generation miss**: When I'm chatting with ChatGPT, who am I really talking to?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains that ChatGPT is a model transformed through post-training stages into a conversational assistant, but it omits the key detail that the model simulates a human data labeler following company labeling instructions, which is central to the golden answer.
  - Bot: When you’re chatting with ChatGPT, you’re talking to a model that has gone through post-training stages (like supervised fine-tuning) to transform a pre-trained “internet document simulator” into a helpful, conversational assistant. [1][3]
  - Golden: In effect, a statistical simulation of a human data labeler following the company's labeling instructions. The model learned its assistant persona by imitating those example conversations.
- **Q023 · generation miss**: What are system instructions used for?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states that system instructions are passed before user input and dictate style, tone, and constraints, but it omits the detail that they are usually passed via a dedicated systemInstruction parameter and the illustrative example of a pirate dog character ending messages with 'woof!'.
  - Bot: System instructions are instructions that get passed to the model before any user input in the prompt, and they can be used to dictate the style and tone of the model while adding constraints on what it can and can’t talk about. [1]
  - Golden: They are instructions passed to the model before any user input, usually through a dedicated systemInstruction parameter. They set the model's style, tone and constraints – for example, making it play a pirate dog character that only talks about pirate topics and ends every message with 'woof!'.
- **Q027 · generation miss**: Give me tips to write better prompts
  - Judge: correct=partial, faithful=True, context recall=yes. The answer covers the six key strategies from the golden answer but adds many extra tips not summarized in the golden answer, and omits some details like specifying audience and quantifying requests; all claims are supported by the passages, which contain extensive prompt-writing tips beyond the golden answer.
  - Bot: 1. Set clear goals and objectives. [1]  
2. Provide context and background information. [1][2]  
3. Use few-shot prompting (provide one or more examples of desired input-output pairs before the actual prompt). [1][3]  
4. Be specific. [1]  
5. Iterate and experiment. [1]  
6. Leverage chain-of-thoug
  - Golden: Six strategies: (1) set clear goals – use action verbs, define length/format, specify the audience; (2) provide context – relevant facts, sources, definitions; (3) use few-shot examples to show style and level of detail; (4) be specific – precise language, quantify requests, break tasks into steps; 
- **Q031 · false refusal**: What are the 10 steps in Anthropic's prompting framework?
  - Judge: correct=no, faithful=True, context recall=yes. The answer correctly states that the full list of 10 steps is not provided in the passages, which only show some steps, matching the golden answer's enumeration.
  - Bot: I don't know. The provided passages include a “10-Step Framework for Effective Prompting,” but they only show steps 1 and 2 (and then later steps 5–10), and they do not provide the full list of all 10 steps in Anthropic’s prompting framework. [3][4][5]
  - Golden: 1. Task context, 2. Tone context, 3. Background data/documents/images, 4. Detailed task description and rules, 5. Examples, 6. Conversation history, 7. Immediate task description or request, 8. Thinking step by step, 9. Output formatting, 10. Prefilled response (if any).
- **Q033 · generation miss**: In the vehicle claims example, when is a car considered a total loss?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states the threshold and condition for total loss but omits the details about the REPAIRABLE verdict below the threshold and the 'needs_manual_review' explanation for ratios within ±0.05 of the threshold.
  - Bot: A car is considered a total loss when the repair-to-market ratio is greater than or equal to the total_loss_threshold (≥ 0.70, i.e., repair cost is at least 70% of market value). [1][4]
  - Golden: When the repair-to-market-value ratio (repair cost ÷ market value) is greater than or equal to the threshold, which defaults to 0.70. Below that the verdict is REPAIRABLE. If the ratio is within ±0.05 of the threshold, 'needs_manual_review' is added to the explanations.
- **Q034 · false refusal**: For the Maruti Swift example (E2), how was the payable amount 370000 calculated?
  - Judge: correct=no, faithful=True, context recall=partial. The answer correctly states the formula for payable amount but does not provide the specific calculation steps or values (repair cost and salvage value) that lead to 370,000 as in the golden answer; the passages contain the example data but do not explicitly show the calculation steps.
  - Bot: I don't know. The passages show that for E2 the payable_amount is 370000 and that it is computed as max(0, repair_cost - salvage_value) when salvage exists, but they do not explicitly state the intermediate subtraction used to reach 370000. [3][4]
  - Golden: Repair cost = parts 350,000 + labour 30,000 = 390,000. Ratio = 390,000 / 500,000 = 0.78, which is ≥ 0.70, so it's a TOTAL_LOSS. Payable amount = repair cost − salvage value = 390,000 − 20,000 = 370,000 (never below 0).
- **Q048 · generation miss**: What do R, A and G stand for in RAG?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly identifies the terms Retrieval, Augmenting, and Generation for R, A, and G respectively, but it omits the detailed explanations of each component provided in the golden answer and passages.
  - Bot: In RAG, R stands for Retrieval, A stands for Augmenting, and G stands for Generation. [1]
  - Golden: Retrieval – looking up internal documents or knowledge bases and fetching the relevant information. Augmentation – adding that retrieved information to the user's prompt. Generation – the LLM writes the final answer based on the augmented prompt.
- **Q050 · false refusal**: How do I stop my HR chatbot from answering salary questions?
  - Judge: correct=no, faithful=True, context recall=partial. The answer is a refusal and does not convey the key facts from the golden answer about using prompt engineering with strict rules to handle salary questions, although the passages partially contain relevant information about prompt engineering for sensitive topics.
  - Bot: I don't know.  

The passages explain that prompt engineering can define limitations and that, for sensitive topics, the prompt engineering rule might instruct the chatbot to politely redirect users to HR instead of providing answers in the chat, but they do not describe how to apply this specifical
  - Golden: Through prompt engineering: give the LLM strict rules marking topics like salary discussions or performance review appeals as off-limits, instruct it to politely redirect users to HR, and to never reveal personal employee information or confidential details.
- **Q053 · generation miss**: what is semantic search?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains semantic search as searching based on meaning rather than exact keywords and its goal to find correct documents even without exact keyword matches, but it omits the illustrative examples of 'allowance' and 'work from home' provided in the golden answer.
  - Bot: Semantic search is a technique that searches documents based on the meaning of words, with the primary goal of having a much higher chance of locating the correct documents based on the user’s input even if the user does not use the exact keywords present in the documents. [1]
  - Golden: Semantic search finds documents based on meaning rather than exact words. For example, searching 'allowance' can find documents about 'reimbursements', and 'work from home' can find 'remote work' or 'home office' policies.
- **Q054 · generation miss**: What are embeddings and embedding models?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains embeddings and embedding models as vectors representing meaning in high-dimensional space and their role in semantic search, but it omits the example of the all-MiniLM-L6-v2 model producing 384-dimensional vectors present in the golden answer.
  - Bot: Embeddings are the “magic” behind semantic search, where both the search query and the documents are converted into mathematical vectors that represent the text’s meaning. [2][4]  

An embedding model is a machine learning model designed to take text and convert it into numbers that represent meanin
  - Golden: An embedding model converts text into a vector – an array of numbers that represents its meaning. These vectors are coordinates in a high-dimensional space where text with similar meaning sits close together. For example, the all-MiniLM-L6-v2 model produces 384-dimensional vectors.
- **Q057 · false refusal**: Chroma or Pinecone – which should I use?
  - Judge: correct=no, faithful=True, context recall=partial. The answer is a refusal and does not convey the key facts about Chroma and Pinecone present in the passages, although the passages contain the needed information except for the mention that most vector DBs use HNSW indexing by default.
  - Bot: I don't know.  

The passages only say that Chroma is an open-source, Python-friendly, locally installable database that is non-persistent by default (stores data in memory and loses it when the program stops, but can be made persistent by specifying a path), while Pinecone is a managed service desi
  - Golden: Chroma is open-source, free, Python-friendly and runs locally – great for learning, students and small projects. It's in-memory by default but can be made persistent by giving it a storage path. Pinecone is a managed service for large companies in production, where the provider handles infrastructur
- **Q066 · generation miss**: Who benefits from MCP?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly identifies the beneficiaries of MCP but omits details about reduced development time and complexity for developers, enhanced capabilities for AI apps, and reusability of MCP servers mentioned in the golden answer.
  - Bot: Developers, AI applications or agents, and end-users benefit from MCP. [2]
  - Golden: Developers get less development time and complexity; AI apps and agents get access to an ecosystem of data sources and tools; end-users get more capable assistants that can access their data and act on their behalf. MCP servers are also reusable across many AI apps.
- **Q068 · generation miss**: What does an MCP server expose?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states that an MCP server exposes tools, resources, and prompts, but it lacks the detailed explanation and examples of each category provided in the golden answer.
  - Bot: An MCP server exposes specific capabilities through the protocol, and its primary job is to expose information (tools, resources, and prompts) to the client. [2][3]
  - Golden: Three things: Tools – functions the client can invoke (search, send a message, update DB records); Resources – read-only data like files, database records or API responses; and Prompt Templates – predefined, well-tested templates for AI interactions, like document Q&A or transcript summaries.
- **Q069 · false refusal**: What is the difference between direct and templated resources in MCP?
  - Judge: correct=no, faithful=True, context recall=partial. The answer admits lack of knowledge and does not convey the key facts about direct and templated resources, although the passages only partially contain the needed explanation.
  - Bot: I don't know. The passages only state that “The resources can be of two types: Direct and Templated” [3], but they do not explain how Direct resources differ from Templated resources.
  - Golden: Resources expose data at a URI, similar to GET handlers in an HTTP server, and can set a mime_type hint. A direct resource has a fixed URI (e.g. docs://documents returning a list of documents), while a templated resource has a parameter in the URI (e.g. docs://documents/{doc_id} returning a specific
- **Q071 · false refusal**: Which MCP transport should I use?
  - Judge: correct=no, faithful=True, context recall=yes. The answer correctly states that the passages do not provide a personal recommendation, but it omits the key factual details about the three MCP transport types and their use cases described in the golden answer.
  - Bot: I don't know.  

The passages list common MCP transport types (Standard IO, HTTP and Server-Sent Events, and Streamable HTTP) and describe when they’re used (local vs remote, stateful vs stateless, and that Streamable HTTP is recommended in updated versions), but they don’t provide a decision rule f
  - Golden: Standard IO is for local servers that the client launches as a subprocess. HTTP with Server-Sent Events is for remote servers keeping a stateful connection. Streamable HTTP is the recommended transport in newer versions – it supports both stateful connections and efficient stateless ones, which scal
- **Q077 · generation miss**: What are the types of machine learning?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly lists the three types of machine learning but omits the detailed explanations and examples provided in the golden answer.
  - Bot: Machine learning is mainly divided into three core types: Supervised Learning, Unsupervised Learning, and Reinforcement Learning. [3][4]
  - Golden: Three: Supervised learning (trained on labeled data with known answers – classification and regression), Unsupervised learning (finds patterns in unlabeled data – clustering and association), and Reinforcement learning (an agent learns by trial and error with rewards and penalties – robotics, games,
- **Q081 · incomplete retrieval**: What's overfitting vs underfitting?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly describes overfitting and underfitting in terms of training and test performance and bias/variance, but it misses that overfitting includes learning noise and that underfitting means poor performance on both datasets; the passages provide partial information but do not explicitly mention noise or the goal of a generalized model with low bias and variance.
  - Bot: Overfitting is when the model performs well with training data (low bias) but fails to perform well with test data (high variance). [1][2]  

Underfitting is when model accuracy is bad with both training and test data (high bias and high variance). [2]
  - Golden: Overfitting is when a model learns the training data too well, including noise, so it does well on training data (low bias) but poorly on new data (high variance). Underfitting is when it performs badly on both. The goal is a generalized model with low bias and low variance.
- **Q087 · generation miss**: How is hierarchical clustering different from k-means?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states that hierarchical clustering does not require specifying K upfront and creates a dendrogram, unlike k-means, but it omits details about the agglomerative bottom-up merging process and cutting the dendrogram to decide cluster count.
  - Bot: Hierarchical clustering differs from k-means in that hierarchical clustering “does not require you to specify the number of clusters (K) beforehand” and instead “creates a hierarchy (tree-like structure) of clusters called a dendrogram,” whereas k-means requires you to “choose the number of clusters
  - Golden: Hierarchical clustering doesn't need you to choose K upfront. It builds a tree of clusters called a dendrogram – usually bottom-up (agglomerative), merging the closest clusters until one remains. You then 'cut' the dendrogram with a horizontal line to decide how many clusters to keep.
- **Q090 · hallucination**: What is an agentic AI workflow?
  - Judge: correct=yes, faithful=False, context recall=no. The answer correctly defines an agentic AI workflow as an iterative, multi-step process involving LLMs and distinguishes it from a single-prompt approach, but the passages provided do not contain any information about agentic AI workflows; they discuss DBSCAN clustering instead.
  - Bot: An agentic AI workflow is a process in which an AI system, most commonly leveraging Large Language Models (LLMs), executes a series of steps—often iteratively—to complete a task. [1]  

It is distinct from a classic, linear approach where a user prompts an LLM once for an entire output and receives 
  - Golden: It's a process where an AI system, usually LLM-based, completes a task through a series of steps, often iteratively – planning, researching, drafting, reviewing and revising – instead of producing everything in one prompt and one response.

Per-question detail: `results/golden-nano/answers.jsonl`.
