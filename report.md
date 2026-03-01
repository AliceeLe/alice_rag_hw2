


python embed.py: turns every chunk into a vector → embeddings.npy + metadata.json

python index.py: reads embeddings.npy → builds FAISS index → faiss.index
reads documents.jsonl → builds BM25 index → bm25.index


    Question comes in: "When was Picklesburgh founded?"

retrieve.py
    Step 1 — Dense:  embed the question → search faiss.index → top 10 chunks by meaning
    Step 2 — Sparse: tokenize the question → search bm25.index → top 10 chunks by keywords
    Step 3 — Hybrid: combine both lists → rerank → top 5 chunks

generate.py
    takes the question + top 5 chunk texts
    builds a prompt like:
        "Answer this question using the context below.
         Question: When was Picklesburgh founded?
         Context: [chunk 1 text] [chunk 2 text] ..."
    sends prompt to LLM → returns answer: "2015"


run crawl.py, process.py, embed.py

Report: below points are awarded based on your report.
# Data creation (10 points)
clearly describe how you created your data. Please include the following details:
How did you compile your knowledge resource, and how did you decide which documents to include?
How did you extract raw data? What tools did you use?

For my data, I used the provided websites and pdfs from the Github. I also added additional websites that I can find online, with topics suggested by ChatGPT. I would first crawl each website using BeautifulSoup for all possible HTML hyperlinks that the website contains. Then, I compiled everything into `data/crawled_urls.json`. 

Afterwards, I run `python3 preprocess/process.py` to process the URLs. To extract raw data, I classified into 2 sources: HTML and PDFs. Because I have too many URLs, I used multithreaded processing with 8 workers for HTML and 4 workers for PDFs to accelerate the collection stage.

`preprocess/process.py` would call methods written in `preprocess/scrape.py`, `preprocess/chunk.py`. For chunking, I utilized paragraph-based chunking with 300 word max and 1 paragraph overlap. Documents were first split on blank lines to identify paragraph boundaries, preserving semantic coherence. Paragraphs were then greedily merged into chunks of up to 300 words. When a single paragraph exceeded 300 words, it was split by words with a 30-word overlap to avoid losing context at boundaries. A 1-paragraph overlap was maintained between consecutive chunks to ensure that answers spanning chunk boundaries could still be retrieved. Chunks shorter than 20 words were discarded as noise. It will finally create `documents.jsonl` where the information are stored in chunks.


# Model details (10 points): clearly describe your model(s). 
What kind of methods (including baselines) did you try? Explain at least two variations (more is welcome). This can include variations of models, which data it was trained on, training strategy, embedding models, retrievers, re-rankers, etc.
What was your justification for trying these methods?

# Results (10 points): report raw numbers from your experiments. Please include the following details:
What was the result of each model that you tried on the public leaderboard?

# Analysis (10 points): perform quantitative/qualitative analysis and present your findings:
Perform a comparison of the outputs on a more fine-grained level than just holistic accuracy numbers, and report the results. For instance, how did your models perform across various types of questions?
Report your results across at least two variations you tried, including variations of models, which data it was trained on, training strategy, embedding models, retrievers, re-rankers, etc.
Perform an analysis that evaluates the effectiveness of retrieve-and-augment strategy vs closed-book use of your models.
Evaluate your hybrid retrieval approach by comparing dense-only, sparse-only, and hybrid retrieval performance. Which fusion strategies work best for different types of questions?
Show examples of outputs from at least two of the systems you created. Ideally, these examples could be representative of the quantitative differences that you found above.
