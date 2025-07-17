# Personal Knowledge Agent (PKA)

An AI-powered personal assistant that enables conversational question answering over your personal documents, emails, bookmarks, and calendar events.  
Built with cutting-edge Retrieval-Augmented Generation (RAG), agent workflows, and LangGraph.

---

## Features

- Conversational chat interface with native Streamlit UI components
- File ingestion and vector search for personal documents (PDF, TXT, DOCX)
- Multi-step agent workflows powered by LangGraph
- Modular architecture with Streamlit frontend and FastAPI backend
- Configurable settings: memory, streaming responses
- Extensible design to add new data sources and skills

---

## Demo Screenshot

![Demo Screenshot](assets/demo_screenshot.png)

---

## Installation

### Prerequisites

- Python 3.9+
- [Poetry](https://python-poetry.org/) or pip

### Setup

1. Clone the repository

```bash
git clone https://github.com/your-username/personal-knowledge-agent.git
cd personal-knowledge-agent
````

2. Create virtual environment and install dependencies

Using pip:

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
.\.venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

Using Poetry:

```bash
poetry install
poetry shell
```

3. Configure environment variables

Copy `.env.example` to `.env` and fill in your OpenAI API keys, Azure credentials, or other config.

```bash
cp .env.example .env
# Edit .env file accordingly
```

---

## Usage

### Run frontend

```bash
streamlit run src/streamlit/app.py
```

### Run backend (optional)

```bash
uvicorn src.backend.api:app --reload
```

---

## Project Structure

```
personal-knowledge-agent/
├── assets/              # Static assets (logos, images)
├── src/
│   ├── components/      # Streamlit UI components (chat_ui, input_bar, sidebar)
│   ├── backend/         # FastAPI backend code
│   ├── config/          # Configuration & settings
│   ├── services/        # Agent and data ingestion services
│   ├── utils/           # Helper utilities and logging
│   └── streamlit/       # Streamlit app entry point
├── tests/               # Unit and integration tests
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Contributing

Contributions are welcome! Please open issues or pull requests.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Acknowledgments

* OpenAI for GPT APIs
* LangGraph for agent orchestration
* Streamlit for rapid UI development