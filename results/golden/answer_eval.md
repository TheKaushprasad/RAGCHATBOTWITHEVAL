# Answer-quality eval: `evals_golden.json`

Provider `openai` · chat `gpt-4.1-mini` · judge `gpt-4.1-mini` · retrieval `vector` k=3 · MIN_SIMILARITY=0.224 · chunks 350/50

## Summary

| metric | value | n |
|---|---|---|
| Correctness vs golden answer (judge) | 86% | 96 |
| Fully correct answers (judge = yes) | 76% | 96 |
| Faithfulness / no hallucination (judge) | 100% | 96 |
| Context recall (judge) | 92% | 96 |
| Answers with a citation | 95% | 96 |
| False refusals | 4% | 96 |
| Semantic similarity to golden (cosine) | 0.75 | 96 |
| Out-of-scope handled correctly (judge) | 100% | 4 |
| Out-of-scope: said "I don't know" | 100% | 4 |
| Latency p50 / p95 | 2.8s / 3.7s | 100 |

## Outcome diagnosis

| outcome | questions |
|---|---|
| ok | 77 |
| incomplete retrieval | 11 |
| generation miss | 8 |
| false refusal | 3 |
| refusal (retrieval miss) | 1 |

## By topic

| topic | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| LLM Fundamentals | 19 | 71% | 100% | 82% | 0.74 |
| RAG | 17 | 94% | 100% | 97% | 0.77 |
| Prompt Engineering | 16 | 84% | 100% | 91% | 0.72 |
| Machine Learning | 16 | 84% | 100% | 91% | 0.78 |
| MCP | 11 | 91% | 100% | 95% | 0.72 |
| Context Engineering | 10 | 90% | 100% | 100% | 0.76 |
| Agentic AI | 7 | 100% | 100% | 100% | 0.77 |
| Out of Scope | 4 | 100% | 100% | n/a | 0.51 |

## By type

| type | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| conceptual | 34 | 87% | 100% | 91% | 0.79 |
| comparison | 21 | 86% | 100% | 90% | 0.79 |
| procedural | 21 | 88% | 100% | 95% | 0.72 |
| factual | 18 | 81% | 100% | 92% | 0.65 |
| out_of_scope | 4 | 100% | 100% | n/a | 0.51 |
| calculation | 2 | 100% | 100% | 100% | 0.72 |

## By difficulty

| difficulty | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| medium | 56 | 86% | 100% | 94% | 0.74 |
| easy | 29 | 86% | 100% | 87% | 0.73 |
| hard | 15 | 90% | 100% | 97% | 0.76 |

## Failures (23)

- **Q002 · refusal (retrieval miss)**: what is a base model?
  - Judge: correct=no, faithful=True, context recall=no. The answer refuses to define 'base model' despite the golden answer providing a clear definition, but the passages do not contain information about 'base model'.
  - Bot: I don't know. The provided context does not define or explain what a base model is.
  - Golden: A base model is the output of the pre-training stage. It's a 'token simulator' or 'internet document simulator' – it can generate text that statistically resembles documents on the internet, but it is not yet a helpful assistant.
- **Q005 · incomplete retrieval**: Why should a product manager bother learning about LLMs?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly states the importance of understanding LLM limitations and reliability, but it omits details about hallucinations, 'Swiss cheese' gaps, token usage, and safeguards like tool use and verification mentioned in the golden answer; the passages provide partial information supporting the answer but lack some specifics from the golden answer.
  - Bot: A product manager should learn about LLMs not just for their capabilities but specifically for their limitations and the proper techniques required to deploy them effectively and reliably. Since LLMs are stochastic systems relying on probability and sampling, they are imperfect and must be used as a
  - Golden: Mainly to understand their limitations and how to deploy them reliably. LLMs are stochastic and can't be fully trusted, they hallucinate, their built-in knowledge is only a vague recollection, they have 'Swiss cheese' gaps in capability, and they need tokens to think. A PM needs this to design safeg
- **Q007 · incomplete retrieval**: Why do LLMs make stuff up, and how can we reduce it in a product?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly explains that LLMs are stochastic and use tools like web search to reduce hallucinations, but it omits the explanation that hallucinations arise because LLMs are probabilistic and confident fabricators, and it does not mention training models to admit ignorance or using context windows with relevant facts, which are in the golden answer but not fully supported by the passages.
  - Bot: LLMs make stuff up because they are stochastic systems that rely on probability and sampling, meaning they do not fully trust their outputs and can generate hallucinations or made-up facts [2]. To reduce this in a product, LLMs can be trained to use external tools such as web search to retrieve rece
  - Golden: LLMs are probabilistic systems, so they can confidently fabricate information (hallucinate). It can be reduced with tool use such as web search to fetch real information, training the model to admit when it doesn't know, and putting the relevant facts directly into the context window instead of rely
- **Q008 · incomplete retrieval**: Why should I put the actual document in the prompt instead of trusting what the model already knows?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly explains that including the actual document in the prompt ensures factual and accurate responses by augmenting the prompt with relevant context, but it does not explicitly mention that the model's stored knowledge is only a vague recollection or that the context window acts as working memory, which are key points in the golden answer; the passages provide partial information about retrieval-augmentation-generation but do not explicitly state the model's knowledge limitations or the context window as working memory.
  - Bot: The Model Context Protocol (MCP) involves including the actual document or relevant context in the prompt rather than relying on the model's pre-existing knowledge. This is because the Retrieval-Augmentation-Generation (R-A-G) system retrieves the most relevant information from a vector database and
  - Golden: Because knowledge stored in the parameters is only a vague recollection. The context window acts as the model's working memory, so for accurate summaries or detailed answers the relevant information should be given explicitly in the context.
- **Q009 · incomplete retrieval**: What are the main stages of building an LLM like ChatGPT?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly describes pretraining and supervised fine-tuning stages but omits the reinforcement learning stage and the term 'post-training' encompassing both SFT and RL, which are present in the golden answer and partially supported by the passages.
  - Bot: The main stages of building an LLM like ChatGPT are:

1. The Pretraining Stage: This is the first and most computationally demanding stage where the neural network acquires foundational knowledge by internalizing statistical patterns of token sequences from massive amounts of text. The output is a b
  - Golden: Three stages: (1) Pre-training, which creates the base model from massive internet text; (2) Supervised Fine-Tuning (SFT), which teaches it to behave like a conversational assistant; and (3) Reinforcement Learning (RL), which improves problem-solving and leads to reasoning. SFT and RL together are c
- **Q010 · false refusal**: What steps are in the FineWeb data pipeline?
  - Judge: correct=no, faithful=True, context recall=yes. The answer correctly states it does not know, but the passages do contain the detailed steps of the FineWeb data pipeline as listed in the golden answer.
  - Bot: I don't know. The provided context passages do not mention the FineWeb data pipeline or its steps.
  - Golden: URL filtering (block malware, adult, spam sites) → text extraction → language filtering (e.g. keep pages with more than 50% English) → Gopher filtering (reliability and safety) → MinHash dedup (remove near-duplicates) → C4 filters → custom filters (based on model goals, safety, domain) → PII removal
- **Q014 · incomplete retrieval**: How long does fine-tuning take compared to pre-training?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly states that fine-tuning is less computationally expensive and costly than pre-training, but it omits the specific time comparison (3 hours vs. three months) and the detail that pre-training is the majority of the compute cost; the passages support the cost and compute difference but do not provide exact time durations.
  - Bot: Fine-tuning takes much less computational resources and is less expensive compared to pre-training, which demands the majority of computational resources and millions of dollars [1].
  - Golden: Much less. SFT often takes around 3 hours, while pre-training can take roughly three months. Pre-training needs most of the compute and millions of dollars; post-training is far cheaper.
- **Q015 · generation miss**: Who writes the conversations used to fine-tune an assistant?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states that human labelers write the conversations following detailed instructions requiring helpful, truthful, and harmless responses, but it omits that LLMs also help create these datasets and that millions of synthetic conversations are involved.
  - Bot: The conversations used to fine-tune an assistant are written by human labelers, who are hired contractors or laborers. These labelers create prompts and write out the ideal assistant responses following detailed labeling instructions provided by the company, such as OpenAI. The instructions require 
  - Golden: Human labelers hired by the company write prompts and ideal assistant responses, following detailed labeling instructions that ask for helpful, truthful and harmless answers. Today LLMs also help create these datasets, so they often contain millions of synthetic conversations that humans then edit.
- **Q016 · generation miss**: When I'm chatting with ChatGPT, who am I really talking to?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains that the user is talking to an AI assistant trained by imitating human labelers through supervised fine-tuning, but it adds extra details about data access and external system connections not mentioned in the golden answer, which focuses on the model as a statistical simulation of a human labeler following instructions.
  - Bot: You are talking to an AI assistant that has been trained to respond helpfully, truthfully, and harmlessly by imitating expert human labelers through supervised fine-tuning (SFT) on high-quality conversation datasets [1]. However, the assistant itself does not inherently have access to private or ext
  - Golden: In effect, a statistical simulation of a human data labeler following the company's labeling instructions. The model learned its assistant persona by imitating those example conversations.
- **Q027 · generation miss**: Give me tips to write better prompts
  - Judge: correct=partial, faithful=True, context recall=yes. The answer covers the six key strategies from the golden answer and adds extra tips from the passages, but it omits details like using action verbs, defining length/format, and specifying the audience explicitly, making it only partially correct though fully supported by the passages.
  - Bot: To write better prompts, consider these tips based on the provided context:

1. Set clear goals and objectives for what you want the model to achieve [1].
2. Provide context and background information to help the model understand the task [1].
3. Use few-shot prompting by giving examples of desired 
  - Golden: Six strategies: (1) set clear goals – use action verbs, define length/format, specify the audience; (2) provide context – relevant facts, sources, definitions; (3) use few-shot examples to show style and level of detail; (4) be specific – precise language, quantify requests, break tasks into steps; 
- **Q031 · false refusal**: What are the 10 steps in Anthropic's prompting framework?
  - Judge: correct=no, faithful=True, context recall=partial. The answer admits lack of knowledge, which is faithful to the passages, but the passages only partially contain the 10 steps, so the answer is not correct and the context recall is partial.
  - Bot: I don't know. The provided context does not include the full list of the 10 steps in Anthropic's prompting framework.
  - Golden: 1. Task context, 2. Tone context, 3. Background data/documents/images, 4. Detailed task description and rules, 5. Examples, 6. Conversation history, 7. Immediate task description or request, 8. Thinking step by step, 9. Output formatting, 10. Prefilled response (if any).
- **Q032 · incomplete retrieval**: Why do people use XML tags in prompts?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly states that XML tags provide clear, structured context for the model to reference, improving output clarity and relevance, but it omits details about labeling sections, using delimiters like Markdown, and wrapping final output for consistency and automatic processing found in the golden answer; the passages support the idea of providing clear contextual information but do not explicitly mention XML tags or output wrapping.
  - Bot: People use XML tags in prompts to provide clear, structured contextual information that the model can reference when generating a response, improving clarity and relevance of the output [2].
  - Golden: LLMs work best with clearly organized input. Delimiters like XML tags (e.g. <user_preferences>) or Markdown separate and label sections so the model can refer back to them. Wrapping the final output in tags like <final_verdict> or using JSON also makes it consistent and easy to process automatically
- **Q033 · incomplete retrieval**: In the vehicle claims example, when is a car considered a total loss?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly states the threshold and ratio concept but omits the explanation about the 'needs_manual_review' condition when the ratio is within ±0.05 of the threshold, which is present in the golden answer; the passages provide partial information on the threshold and ratio but do not mention the ±0.05 review condition explicitly.
  - Bot: A car is considered a total loss when the repair-to-market ratio (repair cost divided by market value) is greater than or equal to the total loss threshold, which is typically 0.7 (70%) or higher [1][2].
  - Golden: When the repair-to-market-value ratio (repair cost ÷ market value) is greater than or equal to the threshold, which defaults to 0.70. Below that the verdict is REPAIRABLE. If the ratio is within ±0.05 of the threshold, 'needs_manual_review' is added to the explanations.
- **Q036 · generation miss**: what is context engineering
  - Judge: correct=partial, faithful=True, context recall=yes. The answer accurately describes context engineering as curating information for the LLM's limited context window and managing various context types, but it omits the analogy comparing the LLM to a CPU, the context window to RAM, and context engineering to an operating system managing RAM.
  - Bot: Context engineering is the art and science of curating what information will go into the limited context window of a large language model (LLM) from a constantly evolving universe of possible information. It involves managing various types of context such as instructions (prompts, memories, few-shot
  - Golden: Context engineering is the natural next step after prompt engineering. It's the set of strategies for curating and maintaining the best set of tokens in the context window during inference – including everything beyond the prompt itself. A common analogy: the LLM is the CPU, the context window is th
- **Q045 · generation miss**: How would you isolate context in the interview coach using multiple agents?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly describes splitting the task into sub-agents with separate context windows and focuses on separation of concerns, but it omits the specific roles of the Question, Evaluation, and Feedback Agents and the central orchestrator passing summaries rather than full transcripts as detailed in the golden answer.
  - Bot: To isolate context in the interview coach using multiple agents, you split the overall task into sub-tasks handled by different sub-agents. Each sub-agent has its own specific set of tools, instructions, and context window, allowing separation of concerns. This means each agent focuses on a particul
  - Golden: Split it into three sub-agents, each with its own context window: a Question Agent (focuses on difficulty and topic rotation), an Evaluation Agent (uses the evaluation rubric), and a Feedback Agent (uses summarized performance). A central orchestrator coordinates them and passes summaries, not full 
- **Q054 · generation miss**: What are embeddings and embedding models?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains embeddings and embedding models and their role in semantic search, but it omits the example of the all-MiniLM-L6-v2 model producing 384-dimensional vectors present in the golden answer.
  - Bot: Embeddings are arrays of numbers (vectors) that represent the meaning of text by capturing different aspects of its content. Embedding models are machine learning models that convert text into these numerical vectors, mapping sentences and paragraphs into a high-dimensional dense vector space where 
  - Golden: An embedding model converts text into a vector – an array of numbers that represents its meaning. These vectors are coordinates in a high-dimensional space where text with similar meaning sits close together. For example, the all-MiniLM-L6-v2 model produces 384-dimensional vectors.
- **Q062 · incomplete retrieval**: Walk me through what happens when a user asks the RAG bot a question
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly outlines the RAG steps but adds keyword search not emphasized in the golden answer and omits the embedding step; the passages mention keyword and semantic search but do not detail embeddings or combining chunks explicitly.
  - Bot: When a user asks a RAG bot a question, the following happens:

1. Retrieval (R): The system searches internal documents or external knowledge bases to find relevant information. This can involve keyword search, which looks for exact word matches in documents, or semantic search, which is more contex
  - Golden: Retrieval: the question is converted into an embedding and a semantic search finds the closest chunks in the vector DB. Augmentation: those chunks are combined with the question into a prompt that tells the LLM to use the provided information. Generation: the LLM writes the answer based on that cont
- **Q069 · false refusal**: What is the difference between direct and templated resources in MCP?
  - Judge: correct=no, faithful=True, context recall=partial. The answer admits lack of knowledge and does not explain the difference between direct and templated resources, while the passages mention resources can be direct or templated but do not define the difference explicitly as in the golden answer.
  - Bot: I don't know. The provided context mentions that resources in MCP can be of two types: Direct and Templated [1][3], but it does not explain the difference between them.
  - Golden: Resources expose data at a URI, similar to GET handlers in an HTTP server, and can set a mime_type hint. A direct resource has a fixed URI (e.g. docs://documents returning a list of documents), while a templated resource has a parameter in the URI (e.g. docs://documents/{doc_id} returning a specific
- **Q077 · incomplete retrieval**: What are the types of machine learning?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly lists the three types of machine learning but omits the key details about each type's characteristics and examples provided in the golden answer; the passages contain detailed descriptions for supervised and unsupervised learning but lack explicit details on reinforcement learning's trial-and-error learning with rewards and penalties.
  - Bot: The types of machine learning are:
1. Supervised Learning
2. Unsupervised Learning
3. Reinforcement Learning [1][2].
  - Golden: Three: Supervised learning (trained on labeled data with known answers – classification and regression), Unsupervised learning (finds patterns in unlabeled data – clustering and association), and Reinforcement learning (an agent learns by trial and error with rewards and penalties – robotics, games,
- **Q078 · generation miss**: How do I know if my problem actually needs ML?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly lists the key conditions for when ML fits the problem and adds relevant examples and the role of an AI PM, but it omits the phrase 'very complex logic' exactly and slightly rephrases 'existing examples of correct answers' as 'actual answers'; the passages contain all needed information to write the golden answer.
  - Bot: You can determine if your problem needs ML if it:

- Handles very complex logic
- Scales up fast
- Adapts in real-time
- Requires specialized personalization
- Has existing examples of actual answers

Additionally, ML is suitable when your problem can be translated into tasks like ranking, recommend
  - Golden: ML fits when the problem involves very complex logic, needs to scale fast, must adapt in real time, requires specialized personalization, or has existing examples of correct answers to learn from.
- **Q080 · incomplete retrieval**: regression vs classification?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly distinguishes regression as predicting continuous outputs and classification as predicting categories with examples, but it misses some key example details from the golden answer such as house prices and sales revenue, and the passages only partially support the examples given.
  - Bot: Regression involves predicting a continuous output, while classification involves predicting a categorical output [1][2]. For example, regression predicts values like averages (e.g., regression averaging in K nearest neighbors), whereas classification predicts categories such as pass/fail or spam/no
  - Golden: Regression predicts a continuous number, like house prices, sales revenue or a person's weight from their age. Classification predicts a category, like spam vs not spam, pass vs fail, or a medical condition.
- **Q081 · generation miss**: What's overfitting vs underfitting?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains overfitting and underfitting with respect to training and test performance and bias/variance, but incorrectly states underfitting involves high variance instead of low variance as in the golden answer; the passages support the key concepts but do not explicitly mention noise in overfitting or the goal of a generalized model.
  - Bot: Overfitting occurs when a model performs well on training data (low bias) but poorly on test data (high variance), meaning it has learned noise and random fluctuations rather than the underlying pattern [1][2]. Underfitting happens when a model has bad accuracy on both training and test data, indica
  - Golden: Overfitting is when a model learns the training data too well, including noise, so it does well on training data (low bias) but poorly on new data (high variance). Underfitting is when it performs badly on both. The goal is a generalized model with low bias and low variance.
- **Q088 · incomplete retrieval**: When would DBSCAN be better than K-means?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly states that DBSCAN groups dense regions and identifies outliers, which K-Means does not, but it omits the key point that DBSCAN is better when the number of clusters is unknown and does not mention the example of customer clusters in city centers versus scattered rural points; also, the passages do not provide information about the number of clusters or the example.
  - Bot: DBSCAN would be better than K-Means when you want to group data points based on dense regions and identify outliers or noise, as DBSCAN marks points that lie far away as outliers or noise, which K-Means does not do [1].
  - Golden: When you don't know the number of clusters and the data has noise. DBSCAN groups dense regions of points and marks far-off points as outliers, so it can, for example, find dense customer clusters in city centers while ignoring scattered rural points or data errors.

Per-question detail: `results/golden/answers.jsonl`.
