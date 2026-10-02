# Answer-quality eval: `evals_golden.json`

Provider `openai` · chat `gpt-4.1-mini` · judge `gpt-4.1-mini` · retrieval `vector` k=5 · MIN_SIMILARITY=0.224 · chunks 350/50

## Summary

| metric | value | n |
|---|---|---|
| Correctness vs golden answer (judge) | 88% | 96 |
| Fully correct answers (judge = yes) | 80% | 96 |
| Faithfulness / no hallucination (judge) | 100% | 96 |
| Context recall (judge) | 95% | 96 |
| Answers with a citation | 98% | 96 |
| False refusals | 2% | 96 |
| Semantic similarity to golden (cosine) | 0.75 | 96 |
| Out-of-scope handled correctly (judge) | 100% | 4 |
| Out-of-scope: said "I don't know" | 100% | 4 |
| Latency p50 / p95 | 2.8s / 4.2s | 100 |

## Outcome diagnosis

| outcome | questions |
|---|---|
| ok | 81 |
| generation miss | 12 |
| incomplete retrieval | 4 |
| retrieval miss | 1 |
| false refusal | 1 |
| refusal (retrieval miss) | 1 |

## By topic

| topic | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| LLM Fundamentals | 19 | 79% | 100% | 92% | 0.74 |
| RAG | 17 | 94% | 100% | 100% | 0.77 |
| Prompt Engineering | 16 | 78% | 100% | 91% | 0.72 |
| Machine Learning | 16 | 97% | 100% | 94% | 0.78 |
| MCP | 11 | 86% | 100% | 95% | 0.70 |
| Context Engineering | 10 | 85% | 100% | 95% | 0.78 |
| Agentic AI | 7 | 100% | 100% | 100% | 0.76 |
| Out of Scope | 4 | 100% | 100% | n/a | 0.49 |

## By type

| type | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| conceptual | 34 | 88% | 100% | 93% | 0.78 |
| comparison | 21 | 88% | 100% | 93% | 0.79 |
| procedural | 21 | 90% | 100% | 98% | 0.73 |
| factual | 18 | 86% | 100% | 97% | 0.66 |
| out_of_scope | 4 | 100% | 100% | n/a | 0.49 |
| calculation | 2 | 50% | 100% | 100% | 0.73 |

## By difficulty

| difficulty | n | correctness | faithfulness | context recall | similarity |
|---|---|---|---|---|---|
| medium | 56 | 91% | 100% | 97% | 0.74 |
| easy | 29 | 91% | 100% | 91% | 0.72 |
| hard | 15 | 70% | 100% | 93% | 0.76 |

## Failures (19)

- **Q001 · generation miss**: What exactly is an LLM, in simple words?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains that an LLM is a neural network predicting the next token based on statistical relationships learned from vast text, but it adds details about refinement into an assistant and generating text resembling internet documents, which are supported by the passages but not explicitly in the golden answer; the core definition is conveyed but some nuances differ.
  - Bot: An LLM (Large Language Model) is a neural network designed to predict the next small text chunk (token) in a sequence by learning statistical relationships from vast amounts of text. It acts like a sophisticated text predictor and can generate text that resembles internet documents. After initial tr
  - Golden: An LLM (Large Language Model) is a neural network that works as a very sophisticated text predictor. It is trained on huge amounts of text to learn the statistical patterns of how tokens follow each other, and then predicts the probability of the next token in a sequence.
- **Q002 · retrieval miss**: what is a base model?
  - Judge: correct=no, faithful=True, context recall=no. The answer describes the Model Context Protocol (MCP) instead of explaining what a base model is, which is not supported by the passages and misses the key facts from the golden answer.
  - Bot: The Model Context Protocol (MCP) is an open-source standard developed by Anthropic to standardize how AI models communicate with tools and context providers safely and modularly. It enables AI applications like Claude or ChatGPT to connect to external data sources (e.g., local files, databases), too
  - Golden: A base model is the output of the pre-training stage. It's a 'token simulator' or 'internet document simulator' – it can generate text that statistically resembles documents on the internet, but it is not yet a helpful assistant.
- **Q007 · generation miss**: Why do LLMs make stuff up, and how can we reduce it in a product?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains that LLMs hallucinate due to their probabilistic nature and vague memory, and suggests tool use and training to admit ignorance as mitigations, but adds details about reinforcement learning and intermediate results generation that are not in the golden answer though supported by passages.
  - Bot: LLMs make stuff up because they are stochastic systems that rely on probability and sampling, which can lead to hallucinations (fabricating information) due to vague knowledge stored in their parameters and limitations in their reasoning capabilities [2][4]. To reduce hallucinations in a product, sa
  - Golden: LLMs are probabilistic systems, so they can confidently fabricate information (hallucinate). It can be reduced with tool use such as web search to fetch real information, training the model to admit when it doesn't know, and putting the relevant facts directly into the context window instead of rely
- **Q008 · incomplete retrieval**: Why should I put the actual document in the prompt instead of trusting what the model already knows?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly states that including the document in the prompt ensures factual, accurate responses based on external data rather than relying on internal knowledge, but it omits the explanation that the model's stored knowledge is only a vague recollection and that the context window acts as working memory; the passages support the answer's claims but do not explicitly mention the model's knowledge being vague or the context window as working memory.
  - Bot: You should put the actual document in the prompt to ensure the model generates a factual, accurate response based on the external data, as it explicitly instructs the model to refer to the provided policy information rather than relying on its internal knowledge, which may be incomplete or outdated 
  - Golden: Because knowledge stored in the parameters is only a vague recollection. The context window acts as the model's working memory, so for accurate summaries or detailed answers the relevant information should be given explicitly in the context.
- **Q015 · generation miss**: Who writes the conversations used to fine-tune an assistant?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly states that human labelers write the conversations following detailed instructions to ensure helpful, truthful, and harmless responses, but it omits that LLMs also help create these datasets and that millions of synthetic conversations are often included and edited by humans.
  - Bot: The conversations used to fine-tune an assistant are written by human labelers, who are hired contractors or laborers. These labelers create prompts and write out the ideal assistant responses following detailed labeling instructions provided by the company (e.g., OpenAI) to ensure the assistant is 
  - Golden: Human labelers hired by the company write prompts and ideal assistant responses, following detailed labeling instructions that ask for helpful, truthful and harmless answers. Today LLMs also help create these datasets, so they often contain millions of synthetic conversations that humans then edit.
- **Q016 · generation miss**: When I'm chatting with ChatGPT, who am I really talking to?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains that ChatGPT is a large language model trained on human-labeled conversation data to imitate an assistant persona, but it omits the key point that it is effectively a statistical simulation of a human data labeler following company instructions, as stated in the golden answer.
  - Bot: When you are chatting with ChatGPT, you are really talking to a large language model (LLM) that has been trained to imitate a helpful, truthful, and harmless assistant by learning statistical patterns from high-quality conversation datasets created by human labelers. The model generates responses ba
  - Golden: In effect, a statistical simulation of a human data labeler following the company's labeling instructions. The model learned its assistant persona by imitating those example conversations.
- **Q017 · generation miss**: What happens in the reinforcement learning stage?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly describes the RL stage as trial and error with scoring and training on successful token sequences, matching the golden answer, but adds extra details about emergent reasoning and RLHF not present in the golden answer.
  - Bot: In the reinforcement learning (RL) stage, the model moves beyond merely imitating human examples to refining its problem-solving capabilities by discovering token sequences or internal cognitive strategies that reliably lead to correct answers. The process is based on trial and error: the model gene
  - Golden: The model is given a prompt and the correct final answer but not the solution. It generates many candidate solutions (rollouts), these are scored as successful or not, and the model is trained on the token sequences that led to correct answers. In the school analogy, this is like a student doing pra
- **Q031 · false refusal**: What are the 10 steps in Anthropic's prompting framework?
  - Judge: correct=no, faithful=True, context recall=yes. The answer refuses to provide the 10 steps despite the passages containing a detailed list of them.
  - Bot: I don't know. The provided context does not include the 10 steps in Anthropic's prompting framework.
  - Golden: 1. Task context, 2. Tone context, 3. Background data/documents/images, 4. Detailed task description and rules, 5. Examples, 6. Conversation history, 7. Immediate task description or request, 8. Thinking step by step, 9. Output formatting, 10. Prefilled response (if any).
- **Q032 · refusal (retrieval miss)**: Why do people use XML tags in prompts?
  - Judge: correct=no, faithful=True, context recall=no. The answer admits lack of knowledge and the passages do not mention XML tags or their use in prompts, so the answer is faithful but does not convey the key facts or recall the needed context.
  - Bot: I don't know. The provided context passages do not mention the use of XML tags in prompts or explain why people use them.
  - Golden: LLMs work best with clearly organized input. Delimiters like XML tags (e.g. <user_preferences>) or Markdown separate and label sections so the model can refer back to them. Wrapping the final output in tags like <final_verdict> or using JSON also makes it consistent and easy to process automatically
- **Q033 · incomplete retrieval**: In the vehicle claims example, when is a car considered a total loss?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly states the threshold and condition for total loss but omits the default threshold value, the REPAIRABLE verdict below threshold, and the 'needs_manual_review' explanation for borderline ratios, which are present in the golden answer and partially supported by the passages.
  - Bot: A car is considered a total loss when the repair-to-market ratio is greater than or equal to the total loss threshold of 0.70 (i.e., repair cost is 70% or more of the market value) [2][4].
  - Golden: When the repair-to-market-value ratio (repair cost ÷ market value) is greater than or equal to the threshold, which defaults to 0.70. Below that the verdict is REPAIRABLE. If the ratio is within ±0.05 of the threshold, 'needs_manual_review' is added to the explanations.
- **Q034 · generation miss**: For the Maruti Swift example (E2), how was the payable amount 370000 calculated?
  - Judge: correct=no, faithful=True, context recall=yes. The ANSWER incorrectly sums parts and labor to 380,000 instead of 390,000, thus miscalculating the repair cost and the basis for the payable amount, though all factual claims are supported by the PASSAGES which contain the needed information.
  - Bot: The payable amount of 370000 for the Maruti Swift example (E2) was calculated as repair_cost (350000 parts_total + 30000 labor_charges = 380000) minus salvage_value (20000), resulting in 380000 - 20000 = 370000 [2].
  - Golden: Repair cost = parts 350,000 + labour 30,000 = 390,000. Ratio = 390,000 / 500,000 = 0.78, which is ≥ 0.70, so it's a TOTAL_LOSS. Payable amount = repair cost − salvage value = 390,000 − 20,000 = 370,000 (never below 0).
- **Q040 · generation miss**: Why do models lose focus with very long context?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains context rot, the transformer architecture's n² attention, and training on shorter sequences, but it omits mention of position encoding interpolation and the gradual precision drop rather than a hard cliff described in the golden answer.
  - Bot: Models lose focus with very long context because as the number of tokens in the context window increases, the model’s ability to accurately recall information decreases, a phenomenon known as context rot. This happens due to the architectural constraints of LLMs based on the transformer architecture
  - Golden: LLMs use the transformer architecture, where every token attends to every other token, creating n² pairwise relationships. As context grows, attention gets stretched thin. Models also see shorter sequences more often in training, so they have less experience with very long dependencies. Techniques l
- **Q043 · generation miss**: Explain semantic, episodic and procedural memory for agents
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly identifies semantic, episodic, and procedural memory types and their roles for agents, but it omits the human parallel and the example details present in the golden answer.
  - Bot: Semantic memory refers to facts that provide task-relevant context for agents. Episodic memory consists of few-shot examples or episodic memories that show desired behavior. Procedural memory includes instructions that steer the agent's behavior. Agents might select these types of memories to help p
  - Golden: Semantic memory stores facts (e.g. facts about a user). Episodic memory stores experiences (e.g. past agent actions, useful as few-shot examples). Procedural memory stores instructions (e.g. the agent's system prompt). Humans parallel: things learned in school, things I did, and instincts/motor skil
- **Q045 · incomplete retrieval**: How would you isolate context in the interview coach using multiple agents?
  - Judge: correct=partial, faithful=True, context recall=partial. The answer correctly describes splitting the interview coach into sub-agents with isolated context windows focusing on different tasks, but it lacks the specific details about the three sub-agents (Question, Evaluation, Feedback) and the central orchestrator passing summaries rather than full transcripts, which are present in the golden answer and partially supported by the passages.
  - Bot: To isolate context in the interview coach using multiple agents, you would split the overall task into sub-tasks handled by different sub-agents. Each sub-agent would have its own specific set of tools, instructions, and context window, allowing separation of concerns. This means that instead of one
  - Golden: Split it into three sub-agents, each with its own context window: a Question Agent (focuses on difficulty and topic rotation), an Evaluation Agent (uses the evaluation rubric), and a Feedback Agent (uses summarized performance). A central orchestrator coordinates them and passes summaries, not full 
- **Q048 · generation miss**: What do R, A and G stand for in RAG?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly identifies the full forms of R, A, and G but omits the detailed explanations of each component provided in the golden answer and passages.
  - Bot: R, A, and G in RAG stand for Retrieval, Augmentation, and Generation respectively [1][5].
  - Golden: Retrieval – looking up internal documents or knowledge bases and fetching the relevant information. Augmentation – adding that retrieved information to the user's prompt. Generation – the LLM writes the final answer based on the augmented prompt.
- **Q055 · generation miss**: How is similarity between two texts calculated?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains similarity calculation using vector dot product and normalization with scores between 0 and 1, but it omits the example similarity scores from the golden answer.
  - Bot: Similarity between two texts is calculated by converting the texts into vectors using an embedding model, then measuring the distance between these vectors in a high-dimensional space. The similarity is quantified using the dot product, which involves multiplying corresponding values in the vectors,
  - Golden: By comparing their vectors with the dot product: multiply corresponding values, add them up, and normalize, giving a score between 0 and 1. Closer to 1 means more similar. In the example, 'dogs vs pets' scored 73.3% similarity while 'dogs vs remote' scored only 36.2%.
- **Q069 · incomplete retrieval**: What is the difference between direct and templated resources in MCP?
  - Judge: correct=no, faithful=True, context recall=partial. The answer correctly states that the passages do not provide a specific explanation of the difference between direct and templated resources, which is faithful to the passages; however, the golden answer contains key details about fixed versus parameterized URIs that are not present in the passages, so the passages only partially recall the needed context and the answer does not convey the key facts.
  - Bot: The context passages do not provide a specific explanation of the difference between direct and templated resources in MCP. They only mention that resources can be of two types: Direct and Templated [1][3]. 

I don't know the exact difference because the passages do not define or describe these two 
  - Golden: Resources expose data at a URI, similar to GET handlers in an HTTP server, and can set a mime_type hint. A direct resource has a fixed URI (e.g. docs://documents returning a list of documents), while a templated resource has a parameter in the URI (e.g. docs://documents/{doc_id} returning a specific
- **Q071 · generation miss**: Which MCP transport should I use?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly identifies Streamable HTTP as the recommended transport and its support for stateful and stateless connections, but it omits the detail that Standard IO is for local subprocess servers and HTTP with Server-Sent Events is for remote stateful servers, which are key facts in the golden answer.
  - Bot: The recommended MCP transport to use is Streamable HTTP, as it supports both stateful connections (using HTTP with server events) and efficient stateless connections (using HTTP on its own), making it suitable for scaling applications [3].
  - Golden: Standard IO is for local servers that the client launches as a subprocess. HTTP with Server-Sent Events is for remote servers keeping a stateful connection. Streamable HTTP is the recommended transport in newer versions – it supports both stateful connections and efficient stateless ones, which scal
- **Q081 · generation miss**: What's overfitting vs underfitting?
  - Judge: correct=partial, faithful=True, context recall=yes. The answer correctly explains overfitting and underfitting with respect to training and test performance and bias/variance, but adds an unsupported claim that underfitting involves high variance, which is not stated in the passages.
  - Bot: Overfitting occurs when a model performs well on training data (low bias) but poorly on test data (high variance), meaning it has learned the training data too well including noise, resulting in poor generalization [1][2]. Underfitting happens when a model performs poorly on both training and test d
  - Golden: Overfitting is when a model learns the training data too well, including noise, so it does well on training data (low bias) but poorly on new data (high variance). Underfitting is when it performs badly on both. The goal is a generalized model with low bias and low variance.

Per-question detail: `results/golden-k5/answers.jsonl`.
