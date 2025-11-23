# AI Research Agent

An intelligent research assistant powered by OpenAI and Mem0 semantic memory. Generates comprehensive research PDFs with AI-powered query generation, source scoring, and personalized recommendations.

## Features

- **AI-Powered Query Generation**: Uses GPT-4o-mini to generate smart, targeted search queries
- **Semantic Memory (Mem0)**: Learns your preferences and research patterns over time
- **Web Search Integration**: Automated web scraping with DuckDuckGo
- **AI Quality Scoring**: Sources are scored for relevance and quality (0-100)
- **PDF Generation**: Beautiful, formatted research PDFs using WeasyPrint
- **Persistent Context**: Inject custom context that influences all research
- **Research History**: Track all past research sessions with full analytics
- **Memory Dashboard**: Monitor and manage your semantic memory

## Project Structure

```
research_project/
├── src/                        # Source code
│   ├── research_ui_flask.py    # Main Flask application
│   ├── memory_layer.py         # Mem0 integration & tracking
│   ├── ai_research_agent.py    # AI query generation
│   ├── ai_assistant.py         # AI coaching & insights
│   ├── database.py             # SQLite operations
│   └── research_to_pdf.py      # PDF generation
├── tests/                      # Test files
│   ├── test_all_routes.py      # HTTP endpoint tests
│   ├── test_endpoints.py       # Memory layer tests
│   └── test_ai_scoring.py      # AI scoring tests
├── data/                       # Databases & vector storage
│   ├── research_memory.db      # Research sessions
│   ├── mem0_usage_tracking.db  # Memory operations
│   └── research_memory_vectors/ # Qdrant vectors
├── pdf_output/                 # Generated PDFs
├── docs/                       # Documentation
├── requirements.txt
├── run.py                      # Launch script
└── README.md
```

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/research_project.git
   cd research_project
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

## Running the Application

**Option 1: From project root**
```bash
python3 run.py
```

**Option 2: From src directory**
```bash
cd src
python3 research_ui_flask.py
```

Then open your browser to: **http://localhost:5001**

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Homepage - Start new research |
| `/start_research` | POST | Generate AI-powered queries |
| `/search_web` | POST | Search web for sources |
| `/generate_pdf` | POST | Generate PDF from sources |
| `/download` | GET | Download generated PDF |
| `/history` | GET | View research history |
| `/analytics` | GET | Usage analytics |
| `/mem0-monitor` | GET | Memory system dashboard |
| `/mem0-context` | GET/POST | Manage persistent context |
| `/mem0-memories` | GET | View stored memories |
| `/mem0-preferences` | GET | View learned preferences |

## Usage Workflow

1. **Enter a research topic** on the homepage
2. **Select AI mode**: Basic, Quality (AI scoring), or Premium
3. **Review generated queries** - edit or deselect as needed
4. **Search the web** - sources are automatically scored
5. **Select sources** for your PDF
6. **Generate & download** your research PDF

## Memory System

The Mem0 integration provides:
- **Automatic learning** from your research patterns
- **Preferred domains** tracking (learns which sources you select)
- **Topic expertise** building over time
- **Manual memory** addition for custom knowledge
- **Persistent context** injection into all AI prompts

## Configuration

### Change Port
Edit `src/research_ui_flask.py` or use:
```bash
export FLASK_RUN_PORT=5002
```

### AI Model
The application uses `gpt-4o-mini` for cost-effective operation (~$0.20/1M tokens).

## Cost Estimate

Using OpenAI GPT-4o-mini:
- Query generation: ~500 tokens
- Source scoring: ~200 tokens per source
- Typical session: ~$0.001-0.01

## License

MIT License

---

**Last Updated**: 2025-11-22
**Version**: 2.0.0
