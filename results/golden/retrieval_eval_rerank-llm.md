# Retrieval eval

mode=`vector` · k=3 · reranker `llm` · MIN_SIMILARITY=0.224 · chunks 350/50 · `openai:text-embedding-3-small`

- Hit rate@3: 96/96 = 100%
- MRR@3:      1.000
- Top-1 similarity, answerable:   min 0.356  avg 0.547
- Top-1 similarity, unanswerable: max 0.446  avg 0.363
- Unanswerable refused by threshold 0.224: 0/4 (the LLM prompt is a second guard; see eval_answers.py)
- Best separating threshold on this data: 0.345 (98% accuracy)

```
  1  ✓       1    0.496  What exactly is an LLM, in simple words?
  2  ✓       1    0.383  what is a base model?
  3  ✓       1    0.488  Where does an LLM actually store everything it learned?
  4  ✓       1    0.499  How is ChatGPT different from a base model?
  5  ✓       1    0.632  Why should a product manager bother learning about LLMs?
  6  ✓       1    0.423  what does the swiss cheese capability model mean?
  7  ✓       1    0.530  Why do LLMs make stuff up, and how can we reduce it in a pro
  8  ✓       1    0.548  Why should I put the actual document in the prompt instead o
  9  ✓       1    0.680  What are the main stages of building an LLM like ChatGPT?
 10  ✓       1    0.441  What steps are in the FineWeb data pipeline?
 11  ✓       1    0.396  What is tokenization?
 12  ✓       1    0.457  how does byte pair encoding work and how big is GPT-4's voca
 13  ✓       1    0.467  How does the neural network actually learn during pre-traini
 14  ✓       1    0.512  How long does fine-tuning take compared to pre-training?
 15  ✓       1    0.581  Who writes the conversations used to fine-tune an assistant?
 16  ✓       1    0.376  When I'm chatting with ChatGPT, who am I really talking to?
 17  ✓       1    0.544  What happens in the reinforcement learning stage?
 18  ✓       1    0.476  Where do 'thinking' or reasoning models come from?
 19  ✓       1    0.356  What is RLHF and what's the catch?
 20  ✓       1    0.664  what is prompt engineering
 21  ✓       1    0.643  What are the benefits of doing prompt engineering properly?
 22  ✓       1    0.606  What are the parts of a prompt?
 23  ✓       1    0.364  What are system instructions used for?
 24  ✓       1    0.471  In what cases will the model refuse and give a fallback resp
 25  ✓       1    0.539  Difference between zero shot and few shot prompting?
 26  ✓       1    0.594  What is chain of thought prompting? Is zero-shot CoT differe
 27  ✓       1    0.614  Give me tips to write better prompts
 28  ✓       1    0.508  What temperature should I use for summarization vs brainstor
 29  ✓       1    0.592  How is top-p different from temperature?
 30  ✓       1    0.412  what is max tokens and why does it matter?
 31  ✓       1    0.481  What are the 10 steps in Anthropic's prompting framework?
 32  ✓       1    0.447  Why do people use XML tags in prompts?
 33  ✓       1    0.450  In the vehicle claims example, when is a car considered a to
 34  ✓       1    0.420  For the Maruti Swift example (E2), how was the payable amoun
 35  ✓       1    0.504  What should the claims bot do if some numbers are missing?
 36  ✓       1    0.584  what is context engineering
 37  ✓       1    0.577  What kinds of context do we need to manage in LLM apps?
 38  ✓       1    0.657  How is context engineering different from prompt engineering
 39  ✓       1    0.419  What is context rot?
 40  ✓       1    0.553  Why do models lose focus with very long context?
 41  ✓       1    0.599  What are the common strategies for agent context engineering
 42  ✓       1    0.630  What's a scratchpad in an agent?
 43  ✓       1    0.486  Explain semantic, episodic and procedural memory for agents
 44  ✓       1    0.620  In the AI interview coach example, what context is passed on
 45  ✓       1    0.625  How would you isolate context in the interview coach using m
 46  ✓       1    0.519  What is RAG?
 47  ✓       1    0.410  why can't chatgpt answer questions about my company's policy
 48  ✓       1    0.535  What do R, A and G stand for in RAG?
 49  ✓       1    0.687  When should I use RAG vs fine tuning vs prompt engineering?
 50  ✓       1    0.431  How do I stop my HR chatbot from answering salary questions?
 51  ✓       1    0.567  How does keyword search work?
 52  ✓       1    0.559  What's wrong with plain keyword search for a chatbot?
 53  ✓       1    0.626  what is semantic search?
 54  ✓       1    0.524  What are embeddings and embedding models?
 55  ✓       1    0.598  How is similarity between two texts calculated?
 56  ✓       1    0.607  Why do we need a vector database? Can't we just compare with
 57  ✓       1    0.359  Chroma or Pinecone – which should I use?
 58  ✓       1    0.591  What is chunking and why is it needed?
 59  ✓       1    0.454  what chunk size and overlap should i use?
 60  ✓       1    0.564  What other chunking methods are there besides fixed size?
 61  ✓       1    0.567  What are the steps to prepare documents for a RAG system?
 62  ✓       1    0.560  Walk me through what happens when a user asks the RAG bot a 
 63  ✓       1    0.581  What is MCP?
 64  ✓       1    0.633  Why was MCP created when we already had RAG and APIs?
 65  ✓       1    0.584  What can I do with MCP? Give examples
 66  ✓       1    0.515  Who benefits from MCP?
 67  ✓       1    0.625  What's the difference between MCP host, client and server?
 68  ✓       1    0.600  What does an MCP server expose?
 69  ✓       1    0.508  What is the difference between direct and templated resource
 70  ✓       1    0.670  How does an MCP client and server talk to each other?
 71  ✓       1    0.440  Which MCP transport should I use?
 72  ✓       1    0.585  As a PM, what should I focus on when building with MCP?
 73  ✓       1    0.519  How would an MCP based support assistant work?
 74  ✓       1    0.628  What's the difference between AI, ML and deep learning?
 75  ✓       1    0.582  How is deep learning different from traditional ML?
 76  ✓       1    0.766  Why does an AI PM need to understand machine learning?
 77  ✓       1    0.572  What are the types of machine learning?
 78  ✓       1    0.600  How do I know if my problem actually needs ML?
 79  ✓       1    0.618  What kinds of problems does ML solve? Any real examples?
 80  ✓       1    0.531  regression vs classification?
 81  ✓       1    0.495  What's overfitting vs underfitting?
 82  ✓       1    0.662  When should I use ridge regression and when lasso?
 83  ✓       1    0.590  In the naive bayes spam example, why is an email with 'Free'
 84  ✓       1    0.669  How does KNN make a prediction?
 85  ✓       1    0.510  Bagging vs boosting?
 86  ✓       1    0.565  How does K-means clustering work?
 87  ✓       1    0.590  How is hierarchical clustering different from k-means?
 88  ✓       1    0.472  When would DBSCAN be better than K-means?
 89  ✓       1    0.510  how do you check if clusters are any good when there are no 
 90  ✓       1    0.724  What is an agentic AI workflow?
 91  ✓       1    0.575  What's the difference between a workflow and an agent?
 92  ✓       1    0.678  How do I break down a task for an agentic workflow?
 93  ✓       1    0.530  What are the levels of autonomy in AI agents?
 94  ✓       1    0.624  Why are agentic workflows better than a single prompt?
 95  ✓       1    0.680  How should I evaluate an agentic workflow?
 96  ✓       1    0.553  What are the main agentic design patterns?
 97  LEAK  n/a    0.254  How much does Pinecone cost per month?
 98  LEAK  n/a    0.333  What's the context window size of GPT-5?
 99  LEAK  n/a    0.420  Give me step by step code to fine-tune Llama with LoRA
100  LEAK  n/a    0.446  Which is the best LLM to use right now?
```
