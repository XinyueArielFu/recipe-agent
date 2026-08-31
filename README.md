# Recipe Agent — AI Recipe Assistant Built on Family Recipes

A full-stack AI Agent project combining a relational database, RAG-based
vector search, ML clustering, and a multi-LLM-backend tool-calling agent.
Built on 17 real, hand-digitized family recipes (bilingual, Chinese/English)
to demonstrate end-to-end AI/ML engineering — from data modeling to a
deployed agent interface.

## Tech Stack

| Layer | Technology |
|---|---|
| Database | SQLite (5-table relational schema + security view) |
| Vector Search (RAG) | ChromaDB + BAAI/bge-small-zh-v1.5 embeddings |
| Machine Learning | scikit-learn (TF-IDF, MultiLabelBinarizer, KMeans, PCA) |
| LLM Backend | Custom abstraction layer supporting Anthropic Claude API + local Ollama models (llama3.2, deepseek-r1) |
| Agent | Multi-turn / parallel tool-calling (function calling); 3 tools: SQL query, semantic search, unit conversion |
| Backend API | FastAPI |
| Frontend | Streamlit |

## Project Structure
```
recipe-agent/
├── data/ # Raw recipe JSON + SQLite database
├── src/
│ ├── db/ # Schema, import script, query functions
│ ├── vector_store/ # ChromaDB indexing and semantic search
│ ├── ml/ # KMeans clustering experiments
│ └── backend/ # LLM backend abstraction, agent routing, FastAPI service
└── frontend/ # Streamlit UI
```


## Key Design Decisions & Technical Highlights

**1. Database design: BOM-style component reuse + security view**
The schema supports recipe-to-recipe composition (e.g., "mango box" references
a shared "crepe" and "cream" sub-recipe) to avoid data duplication. All
user-facing queries go through a `verified_recipes` view, enforcing at the
database level that AI-synthesized training data can never leak into
real user-facing answers.

**2. Clear separation of responsibilities between SQL and RAG**
Precise numerical data (ingredient amounts, cooking temperature/duration) is
stored in SQL to prevent the LLM from hallucinating exact figures. Long-form
step descriptions are retrieved via semantic search and translated/organized
by the LLM on demand — balancing structured-query accuracy with natural
language generation flexibility.

**3. Embedding model selection validated through hands-on debugging**
The initial multilingual embedding model (paraphrase-multilingual-MiniLM)
showed poor discriminative power on short Chinese culinary text — a
quantitative test revealed two completely unrelated recipes scored a higher
similarity than the correct recipe did against its own name. After isolating
the root cause, switched to BAAI/bge-small-zh-v1.5 (Chinese-optimized),
which resolved the issue and was confirmed with before/after retrieval tests.

**4. Unified multi-LLM backend abstraction with real comparative findings**
Designed an `LLMBackend` abstract class so Claude API and local Ollama models
share the same agent routing code. Testing surfaced concrete limitations of
lightweight local models (3B parameters) in multi-tool scenarios — including
incorrect tool selection and hallucinated answers caused by malformed
conversation history — which were partially mitigated by fixing history
formatting and tuning system prompts, though a capability ceiling remained
for tasks requiring aggregation across multiple retrieved candidates.

**5. Agent autonomously discovers data relationships**
Without any explicit "component expansion" orchestration logic, Claude
independently recognized — purely from component names surfaced in RAG
results — that answering a full recipe required additional SQL lookups for
a referenced sub-recipe, and issued multiple parallel tool calls to retrieve
that data. This validated that well-structured underlying data can enable
an LLM to perform non-trivial multi-step reasoning on its own.

**6. Clustering experiments with an honest discussion of limitations**
Compared clustering quality across different `n_clusters` values and found
that KMeans silhouette scores in high-dimensional space are distorted by
the curse of dimensionality (PCA-reduced sweet/savory binary clustering
improved from -0.03 to 0.338). Also identified that ingredient TF-IDF and
tag-based features alone are insufficient to further separate desserts with
similar texture/flavor profiles — documented as a known limitation of the
current feature engineering approach rather than over-tuning for a better-
looking number.

## How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialize the SQLite database
python3 src/db/load_json_to_sql.py

# 3. Build the vector store
python3 src/vector_store/build_vector_db.py

# 4. Start the backend API
uvicorn src.backend.main:app --reload

# 5. Start the frontend (new terminal)
streamlit run frontend/app.py
```

API docs: `http://localhost:8000/docs`
Frontend: `http://localhost:8501`