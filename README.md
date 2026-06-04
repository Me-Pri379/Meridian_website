# Financial Analyst Agent

This project is organized as a FastAPI backend with a static HTML/CSS frontend.

Structure:
- `src/` - core application logic, agent assembly, RAG pipeline, database access, and server wiring
- `entrypoints/` - application launcher
- `static/` - frontend assets
- `data/` - runtime data assets such as the SQLite database and policy PDFs
- `vector_db/` - persisted FAISS index data

Use `scaffold.py` to create this scaffold if files are missing.
