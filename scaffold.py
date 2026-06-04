from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

PROJECT_STRUCTURE: Dict[str, Dict[str, str]] = {
    "src": {
        "__init__.py": "# src package\n",
        "agents.py": "# Agent assembly and tool registration for the financial analyst agent\n",
        "tools.py": "# Wrappers for portfolio lookup, market data search, calculations, policy retriever, and search tools\n",
        "database_queries.py": "# SQLite database access helpers and query functions\n",
        "rag.py": "# RAG pipeline: PDF loading, splitting, embedding, FAISS build/load, and retriever creation\n",
        "schemas.py": "# Pydantic request/response models and shared data schemas\n",
        "config.py": "# Environment and path configuration, including .env loading logic\n",
        "server.py": "# FastAPI application factory, routes, and static file mounting\n",
        "utils.py": "# Shared utility functions for path handling and safe file operations\n",
    },
    "entrypoints": {
        "app.py": "# Thin launcher for the FastAPI app\n",
    },
    "static": {
        "index.html": "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Financial Analyst Agent</title>\n    <link rel=\"stylesheet\" href=\"styles.css\">\n</head>\n<body>\n    <main>\n        <h1>Financial Analyst Agent</h1>\n        <section id=\"app\">\n            <form id=\"query-form\">\n                <label for=\"query\">Ask the agent:</label>\n                <textarea id=\"query\" name=\"query\" rows=\"4\"></textarea>\n                <button type=\"submit\">Submit</button>\n            </form>\n            <div id=\"response\"></div>\n        </section>\n    </main>\n    <script src=\"app.js\"></script>\n</body>\n</html>\n",
        "styles.css": "/* Basic styling for the financial analyst frontend */\nbody { font-family: Arial, sans-serif; background: #f5f7fa; color: #20232a; margin: 0; padding: 0; }\nmain { max-width: 900px; margin: 2rem auto; padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08); }\nh1 { margin-bottom: 1rem; }\ntextarea { width: 100%; padding: 0.75rem; font-size: 1rem; border: 1px solid #d1d5db; border-radius: 8px; }\nbutton { margin-top: 1rem; padding: 0.8rem 1.2rem; background: #2563eb; color: white; border: none; border-radius: 8px; cursor: pointer; }\n#response { margin-top: 1.5rem; white-space: pre-wrap; background: #f8fafc; padding: 1rem; border-radius: 8px; border: 1px solid #e2e8f0; }\n",
        "app.js": "// Frontend stub to connect the static UI to the FastAPI backend\ndocument.getElementById('query-form').addEventListener('submit', async (event) => {\n    event.preventDefault();\n    const query = document.getElementById('query').value.trim();\n    if (!query) return;\n    const responseElement = document.getElementById('response');\n    responseElement.textContent = 'Loading...';\n\n    try {\n        const resp = await fetch('/api/query', {\n            method: 'POST',\n            headers: { 'Content-Type': 'application/json' },\n            body: JSON.stringify({ query }),\n        });\n        const result = await resp.json();\n        responseElement.textContent = result.answer ?? JSON.stringify(result, null, 2);\n    } catch (error) {\n        responseElement.textContent = 'Request failed: ' + error.message;\n    }\n});\n",
    },
    "data": {
        ".gitkeep": "# Keep the data folder in version control\n",
    },
    "vector_db": {
        ".gitkeep": "# Keep the vector_db folder in version control\n",
    },
    ".env.example": "OPENAI_API_KEY=your_openai_api_key_here\nTAVILY_API_KEY=your_tavily_api_key_here\nDATA_PATH=./data\nVECTOR_DB_PATH=./vector_db\n",
    "requirements.txt": "fastapi\nuvicorn[standard]\npython-dotenv\nlangchain\nopenai\nfaiss-cpu\npydantic\npython-multipart\n",
    "README.md": "# Financial Analyst Agent\n\nThis project is organized as a FastAPI backend with a static HTML/CSS frontend.\n\nStructure:\n- `src/` - core application logic, agent assembly, RAG pipeline, database access, and server wiring\n- `entrypoints/` - application launcher\n- `static/` - frontend assets\n- `data/` - runtime data assets such as the SQLite database and policy PDFs\n- `vector_db/` - persisted FAISS index data\n\nUse `scaffold.py` to create this scaffold if files are missing.\n",
}


def create_file(path: Path, content: str) -> None:
    if path.exists():
        print(f"Skipping existing file: {path}")
        return
    path.write_text(content, encoding="utf-8")
    print(f"Created file: {path}")


def create_structure(root: Path) -> None:
    root = root.resolve()
    for directory, files in PROJECT_STRUCTURE.items():
        if directory == ".env.example" or directory == "requirements.txt" or directory == "README.md":
            file_path = root / directory
            create_file(file_path, files)
            continue

        dir_path = root / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        for filename, content in files.items():
            file_path = dir_path / filename
            create_file(file_path, content)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold the LangChain ReAct FastAPI project structure."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Root directory for the scaffolded project.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(f"Scaffolding project structure under: {args.root}")
    create_structure(args.root)
    print("Scaffold generation complete.")


if __name__ == "__main__":
    main()
