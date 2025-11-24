"""
FastAPI-based Research UI Application
Migrated from Flask with identical functionality
"""
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import os
import secrets
import json
from datetime import datetime
from typing import Optional, List
from research_to_pdf import (
    generate_search_queries,
    search_web,
    fetch_and_clean,
    build_html_document,
    html_to_pdf
)
import database as db
import memory_layer as mem
import ai_assistant as ai
import ai_research_agent as ai_agent

# Create FastAPI app
app = FastAPI(title="AI Research Agent", description="Research to PDF Generator")

# Add session middleware with secret key
app.add_middleware(SessionMiddleware, secret_key=secrets.token_hex(16))

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    print("Initializing database...")
    db.init_database()
    print("FastAPI startup complete")

# User ID tracking for mem0
def get_user_id(request: Request) -> str:
    """Get or create user ID for memory tracking"""
    if 'user_id' not in request.session:
        request.session['user_id'] = secrets.token_hex(8)
    return request.session['user_id']

def build_html_from_markdown(topic: str, markdown_content: str) -> str:
    """Build HTML document from markdown content (for AI agent)"""
    try:
        import markdown
        html_body = markdown.markdown(markdown_content)
    except ImportError:
        html_body = f'<div style="white-space: pre-wrap;">{markdown_content}</div>'

    html = f"""
    <html>
    <head>
        <meta charset='utf-8'>
        <title>{topic}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 40px auto;
                padding: 20px;
                color: #333;
            }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #34495e; margin-top: 30px; border-bottom: 2px solid #95a5a6; padding-bottom: 5px; }}
            h3 {{ color: #7f8c8d; margin-top: 20px; }}
            p {{ margin: 15px 0; }}
            ul, ol {{ margin: 15px 0; padding-left: 30px; }}
            li {{ margin: 8px 0; }}
            strong {{ color: #2c3e50; }}
            em {{ color: #7f8c8d; }}
            hr {{ border: none; border-top: 1px solid #bdc3c7; margin: 30px 0; }}
        </style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """
    return html

# HTML Template (shared base template) - using string concatenation to avoid escaping issues
def get_html_template(content: str) -> str:
    """Generate complete HTML with content inserted"""
    return '''<!DOCTYPE html>
<html>
<head>
    <title>Research to PDF</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 { color: #333; margin-top: 0; }
        h2 { color: #555; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { color: #666; font-size: 1.1em; }

        input[type="text"] {
            width: 100%;
            padding: 12px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #007bff;
        }

        button {
            background: #007bff;
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
        }
        button:hover { background: #0056b3; }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        button.secondary {
            background: #6c757d;
        }
        button.secondary:hover {
            background: #545b62;
        }

        .query-item {
            background: #f8f9fa;
            padding: 10px 15px;
            margin: 10px 0;
            border-left: 4px solid #007bff;
            border-radius: 4px;
        }

        .url-item {
            background: #fff;
            border: 1px solid #ddd;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .url-item:hover {
            border-color: #007bff;
        }
        .url-item input[type="checkbox"] {
            margin-right: 10px;
            transform: scale(1.3);
        }
        .url-title {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        .url-link {
            color: #666;
            font-size: 0.9em;
            word-break: break-all;
        }

        .progress {
            background: #f0f0f0;
            border-radius: 4px;
            height: 30px;
            margin: 20px 0;
            overflow: hidden;
        }
        .progress-bar {
            background: #007bff;
            height: 100%;
            line-height: 30px;
            color: white;
            text-align: center;
            transition: width 0.3s;
        }

        .success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
        }

        .info {
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
        }

        .error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
        }

        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #007bff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 10px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .next-steps {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 20px;
            border-radius: 4px;
            margin: 20px 0;
        }
        .next-steps h3 {
            margin-top: 0;
            color: #856404;
        }
        .next-steps ul {
            margin: 0;
            padding-left: 20px;
        }
        .next-steps li {
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Research to PDF</h1>
            <p>Turn any topic into a comprehensive research PDF for NotebookLM</p>
        </div>

        <div id="app">
            ''' + content + '''
        </div>
    </div>

    <script>
        function selectAll(checked) {
            document.querySelectorAll('.url-checkbox').forEach(cb => {
                cb.checked = checked;
            });
        }
    </script>
</body>
</html>'''

def render_template(content: str) -> HTMLResponse:
    """Render content within the base HTML template"""
    return HTMLResponse(content=get_html_template(content))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user_id = get_user_id(request)

    # Get personalized greeting
    greeting_data = ai.get_personalized_greeting(user_id)
    topic_suggestions = ai.get_topic_suggestions(user_id)
    smart_defaults = ai.get_smart_defaults(user_id)
    coaching_tips = ai.get_ai_coaching(user_id, 'start')

    suggestions_html = ''
    if topic_suggestions:
        suggestions_html = '''
        <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #4caf50;">
            <strong>Suggested Topics:</strong>
            <div style="margin-top: 10px;">''' + ''.join([f'''
                <button type="button" class="secondary" style="margin: 5px; background: #4caf50;"
                        onclick="document.getElementsByName('topic')[0].value = '{suggestion}'">
                    {suggestion}
                </button>''' for suggestion in topic_suggestions]) + '''
            </div>
        </div>'''

    content = f'''
    <!-- Personalized Greeting -->
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
        <h2 style="margin: 0 0 10px 0; color: white;">{greeting_data['greeting']}</h2>
        <p style="margin: 0; opacity: 0.9;">{greeting_data['suggestion']}</p>
    </div>

    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h2 style="margin: 0;">Step 1: Enter Your Research Topic</h2>
        <div>
            <button type="button" class="secondary" onclick="window.location.href='/history'">History</button>
            <button type="button" class="secondary" onclick="window.location.href='/analytics'">Analytics</button>
            <button type="button" class="secondary" onclick="window.location.href='/mem0-monitor'">Mem0</button>
        </div>
    </div>

    {suggestions_html}

    <!-- AI Coaching Tips -->
    <div style="background: #fff3cd; padding: 12px 15px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #ffc107;">
        <strong>AI Tips:</strong>
        <ul style="margin: 8px 0 0 0; padding-left: 20px; font-size: 14px;">
            {chr(10).join([f'<li>{tip}</li>' for tip in coaching_tips])}
        </ul>
    </div>

    <form method="POST" action="/start_research" id="researchForm">
        <input type="text" name="topic" placeholder="e.g., quantum computing basics, machine learning ethics, web3 security" required>

        <div style="margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px;">
            <h3 style="margin-top: 0; font-size: 18px;">Research Mode</h3>

            <div style="margin: 15px 0;">
                <label style="display: block; margin-bottom: 10px; font-weight: 600;">How should I research this topic?</label>

                <div style="margin: 10px 0;">
                    <label style="display: flex; align-items: start; padding: 12px; background: #e8f5e9; border: 2px solid #4caf50; border-radius: 6px; cursor: pointer;">
                        <input type="radio" name="research_mode" value="ai_agent" checked onclick="document.getElementById('aiAgentConfig').style.display='block'; document.getElementById('webSearchConfig').style.display='none';" style="margin: 4px 10px 0 0;">
                        <div>
                            <strong style="color: #2e7d32;">AI-Powered Web Search (Default)</strong>
                            <div style="font-size: 13px; color: #555; margin-top: 4px;">
                                AI uses your mem0 context to generate smart queries, then searches the web for relevant URLs.
                            </div>
                        </div>
                    </label>
                </div>

                <div style="margin: 10px 0;">
                    <label style="display: flex; align-items: start; padding: 12px; background: #fff; border: 2px solid #ddd; border-radius: 6px; cursor: pointer;">
                        <input type="radio" name="research_mode" value="web_search" onclick="document.getElementById('webSearchConfig').style.display='block'" style="margin: 4px 10px 0 0;">
                        <div>
                            <strong>Web Search Mode</strong>
                            <div style="font-size: 13px; color: #555; margin-top: 4px;">
                                Search the web for sources using DuckDuckGo. More control but slower.
                            </div>
                        </div>
                    </label>
                </div>
            </div>

            <!-- AI Agent Configuration -->
            <div id="aiAgentConfig" style="margin: 15px 0; display: block;">
                <h4 style="margin: 0 0 15px 0; font-size: 16px;">AI-Powered Search Settings</h4>

                <div style="margin: 15px 0;">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Number of AI-Generated Queries:</label>
                    <select name="ai_num_queries" style="width: 100%; padding: 8px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;">
                        <option value="3">3 queries (Quick)</option>
                        <option value="5">5 queries (Balanced)</option>
                        <option value="7" selected>7 queries (Comprehensive)</option>
                        <option value="10">10 queries (Exhaustive)</option>
                    </select>
                </div>

                <div style="margin: 15px 0;">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Results per Query:</label>
                    <select name="ai_results_per_query" style="width: 100%; padding: 8px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;">
                        <option value="10">10 results</option>
                        <option value="20">20 results</option>
                        <option value="30" selected>30 results</option>
                        <option value="50">50 results</option>
                    </select>
                </div>

                <div style="margin: 15px 0;">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Max Total Sources:</label>
                    <select name="ai_max_sources" style="width: 100%; padding: 8px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;">
                        <option value="30">30 sources</option>
                        <option value="50" selected>50 sources</option>
                        <option value="75">75 sources</option>
                        <option value="100">100 sources</option>
                    </select>
                </div>
            </div>

            <!-- Web Search Configuration (hidden by default) -->
            <div id="webSearchConfig" style="display: none; margin-top: 20px; padding-top: 20px; border-top: 2px solid #ddd;">
                <h4 style="margin: 0 0 15px 0; font-size: 16px;">Web Search Settings</h4>

                <div style="margin: 15px 0;">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Number of Search Queries:</label>
                    <select name="num_queries" style="width: 100%; padding: 8px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;">
                        <option value="3">3 queries (Quick)</option>
                        <option value="5">5 queries (Balanced)</option>
                        <option value="7" selected>7 queries (Comprehensive)</option>
                        <option value="10">10 queries (Exhaustive)</option>
                    </select>
                </div>

                <div style="margin: 15px 0;">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Results per Query:</label>
                    <select name="results_per_query" style="width: 100%; padding: 8px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;">
                        <option value="10">10 results</option>
                        <option value="20">20 results</option>
                        <option value="30" selected>30 results</option>
                        <option value="50">50 results</option>
                    </select>
                </div>

                <div style="margin: 15px 0;">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Max Total Sources:</label>
                    <select name="max_sources" style="width: 100%; padding: 8px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;">
                        <option value="30">30 sources</option>
                        <option value="50" selected>50 sources</option>
                        <option value="75">75 sources</option>
                        <option value="100">100 sources</option>
                    </select>
                </div>

                <div style="margin: 15px 0;">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Query Focus:</label>
                    <select name="query_focus" style="width: 100%; padding: 8px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;">
                        <option value="balanced" selected>Balanced (mix of all types)</option>
                        <option value="academic">Academic (research papers, scholarly articles)</option>
                        <option value="practical">Practical (guides, tutorials, how-tos)</option>
                        <option value="recent">Recent (latest news, 2024-2025 updates)</option>
                        <option value="technical">Technical (documentation, specifications)</option>
                    </select>
                </div>

                <div style="margin: 20px 0; padding: 20px; background: #e3f2fd; border-radius: 8px; border-left: 4px solid #2196f3;">
                    <h3 style="margin-top: 0; font-size: 18px; color: #1976d2;">AI Quality Enhancement</h3>

                    <div style="margin: 15px 0;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">AI Enhancement Level:</label>
                        <select name="ai_enhancement" style="width: 100%; padding: 8px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;">
                            <option value="none">None (Fastest, free search only)</option>
                            <option value="basic" selected>Basic (AI query generation only)</option>
                            <option value="quality">Quality Filtering (AI scores sources)</option>
                            <option value="premium">Premium (AI scoring + summaries)</option>
                        </select>
                    </div>

                    <div style="margin: 15px 0;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">Minimum Quality Score:</label>
                        <select name="min_quality_score" style="width: 100%; padding: 8px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;">
                            <option value="0">0 - No filtering</option>
                            <option value="40">40 - Low bar</option>
                            <option value="60" selected>60 - Moderate</option>
                            <option value="70">70 - High</option>
                            <option value="80">80 - Very High</option>
                        </select>
                    </div>

                    <div style="margin: 15px 0;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">Max Sources to AI Score:</label>
                        <select name="max_to_score" style="width: 100%; padding: 8px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;">
                            <option value="10">10 sources</option>
                            <option value="20">20 sources</option>
                            <option value="30" selected>30 sources</option>
                            <option value="50">50 sources</option>
                        </select>
                    </div>
                </div>
            </div>
        </div>

        <button type="submit">Start Research</button>

        <script>
            document.querySelectorAll('input[name="research_mode"]').forEach(radio => {{
                radio.addEventListener('change', function() {{
                    if (this.value === 'ai_agent') {{
                        document.getElementById('aiAgentConfig').style.display = 'block';
                        document.getElementById('webSearchConfig').style.display = 'none';
                    }} else {{
                        document.getElementById('aiAgentConfig').style.display = 'none';
                        document.getElementById('webSearchConfig').style.display = 'block';
                    }}
                }});
            }});
        </script>
    </form>

    <div class="info" style="margin-top: 30px;">
        <strong>How it works:</strong>
        <ol>
            <li>Enter a topic you want to research</li>
            <li>Configure search parameters (optional)</li>
            <li>AI generates diverse search queries</li>
            <li>System searches across all queries</li>
            <li>Select which sources to include</li>
            <li>Download your comprehensive research PDF</li>
        </ol>
    </div>
    '''
    return render_template(content)


@app.post("/start_research", response_class=HTMLResponse)
async def start_research(
    request: Request,
    topic: str = Form(...),
    research_mode: str = Form("ai_agent"),
    ai_num_queries: int = Form(7),
    ai_results_per_query: int = Form(30),
    ai_max_sources: int = Form(50),
    num_queries: int = Form(7),
    results_per_query: int = Form(30),
    max_sources: int = Form(50),
    query_focus: str = Form("balanced"),
    ai_enhancement: str = Form("basic"),
    min_quality_score: int = Form(60),
    max_to_score: int = Form(30)
):
    """Route research to either AI Agent or Web Search based on mode"""
    topic = topic.strip()
    if not topic:
        return RedirectResponse(url="/", status_code=303)

    if research_mode == "ai_agent":
        # Store form data in session and redirect to AI research
        request.session['topic'] = topic
        request.session['ai_num_queries'] = ai_num_queries
        request.session['ai_results_per_query'] = ai_results_per_query
        request.session['ai_max_sources'] = ai_max_sources
        return await ai_research_route(request)
    else:
        # Store form data in session and redirect to web search
        request.session['topic'] = topic
        request.session['num_queries'] = num_queries
        request.session['results_per_query'] = results_per_query
        request.session['max_sources'] = max_sources
        request.session['query_focus'] = query_focus
        request.session['ai_enhancement'] = ai_enhancement
        request.session['min_quality_score'] = min_quality_score
        request.session['max_to_score'] = max_to_score
        return await generate_queries(request)


async def ai_research_route(request: Request):
    """Generate search queries using AI agent + mem0 context, then search web"""
    topic = request.session.get('topic', '')
    num_queries = request.session.get('ai_num_queries', 7)
    results_per_query = request.session.get('ai_results_per_query', 30)
    max_sources = request.session.get('ai_max_sources', 50)
    user_id = get_user_id(request)

    if not topic:
        return RedirectResponse(url="/", status_code=303)

    # Update session
    request.session['num_queries'] = num_queries
    request.session['results_per_query'] = results_per_query
    request.session['max_sources'] = max_sources
    request.session['research_mode'] = 'ai_web_search'

    # Generate smart queries using AI + mem0
    queries = ai_agent.generate_smart_search_queries(user_id, topic, num_queries=num_queries)

    if not queries:
        content = '''
        <div class="error">Failed to generate search queries. Please try again.</div>
        <button onclick="window.location.href='/'">Start Over</button>
        '''
        return render_template(content)

    # Save queries to session
    request.session['queries'] = queries

    # Build query editing form
    queries_html = "".join([f'''
    <div class="query-item" style="display: flex; align-items: center; gap: 10px; margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 6px;">
        <input type="checkbox" class="query-checkbox" name="use_query_{i}" checked onchange="updateQueryCount()"
               style="transform: scale(1.3); cursor: pointer;">
        <div style="flex: 1;">
            <input type="text" name="query_{i}" value="{q.replace('"', '&quot;')}"
                   style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
                   placeholder="Edit query...">
        </div>
        <button type="button" onclick="removeQuery(this)" class="secondary" style="padding: 6px 12px;">X</button>
    </div>
    ''' for i, q in enumerate(queries)])

    content = f'''
    <h2>AI-Generated Search Queries</h2>
    <p>Using your mem0 context and OpenAI, I've generated {len(queries)} optimized search queries for: <strong>{topic}</strong></p>

    <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50;">
        <h3 style="margin-top: 0; color: #2e7d32;">Review and Edit Queries</h3>
        <p>You can edit any query, uncheck ones you don't want, or add new ones below:</p>
    </div>

    <form method="POST" action="/search_web" id="queryForm">
        <input type="hidden" name="auto_search" value="1">

        <div style="margin: 20px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <strong>Select queries to search (<span id="queryCount">{len(queries)}</span> selected):</strong>
                <div>
                    <button type="button" onclick="selectAll(true)" class="secondary" style="margin-right: 5px;">Select All</button>
                    <button type="button" onclick="selectAll(false)" class="secondary">Deselect All</button>
                </div>
            </div>

            <div id="queriesList" style="margin: 15px 0;">
                {queries_html}
            </div>

            <button type="button" onclick="addNewQuery()" class="secondary" style="margin-top: 10px;">
                + Add New Query
            </button>
        </div>

        <div style="margin: 20px 0;">
            <button type="submit" style="padding: 12px 24px; background: #4caf50; color: white; border: none; border-radius: 4px; font-size: 16px; font-weight: 600; cursor: pointer;">
                Search Web with Selected Queries
            </button>
            <button type="button" class="secondary" onclick="window.location.href='/'">Start Over</button>
        </div>
    </form>

    <script>
        let queryCounter = {len(queries)};

        function selectAll(checked) {{
            document.querySelectorAll('.query-checkbox').forEach(cb => {{
                cb.checked = checked;
            }});
            updateQueryCount();
        }}

        function updateQueryCount() {{
            const count = document.querySelectorAll('.query-checkbox:checked').length;
            document.getElementById('queryCount').textContent = count;
        }}

        function removeQuery(btn) {{
            btn.closest('.query-item').remove();
            updateQueryCount();
        }}

        function addNewQuery() {{
            const queriesList = document.getElementById('queriesList');
            const newItem = document.createElement('div');
            newItem.className = 'query-item';
            newItem.style.cssText = 'display: flex; align-items: center; gap: 10px; margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 6px;';
            newItem.innerHTML = `
                <input type="checkbox" class="query-checkbox" name="use_query_${{queryCounter}}" checked onchange="updateQueryCount()"
                       style="transform: scale(1.3); cursor: pointer;">
                <div style="flex: 1;">
                    <input type="text" name="query_${{queryCounter}}" value=""
                           style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
                           placeholder="Enter your custom query...">
                </div>
                <button type="button" onclick="removeQuery(this)" class="secondary" style="padding: 6px 12px;">X</button>
            `;
            queriesList.appendChild(newItem);
            queryCounter++;
            updateQueryCount();
            newItem.querySelector('input[type="text"]').focus();
        }}
    </script>
    '''

    return render_template(content)


@app.post("/ai_research", response_class=HTMLResponse)
async def ai_research_post(
    request: Request,
    topic: str = Form(...),
    ai_num_queries: int = Form(7),
    ai_results_per_query: int = Form(30),
    ai_max_sources: int = Form(50)
):
    """POST handler for AI research"""
    request.session['topic'] = topic.strip()
    request.session['ai_num_queries'] = ai_num_queries
    request.session['ai_results_per_query'] = ai_results_per_query
    request.session['ai_max_sources'] = ai_max_sources
    return await ai_research_route(request)


async def generate_queries(request: Request):
    """Generate queries for web search mode"""
    topic = request.session.get('topic', '')
    if not topic:
        return RedirectResponse(url="/", status_code=303)

    num_queries = request.session.get('num_queries', 7)
    results_per_query = request.session.get('results_per_query', 30)
    max_sources = request.session.get('max_sources', 50)
    query_focus = request.session.get('query_focus', 'balanced')
    ai_enhancement = request.session.get('ai_enhancement', 'basic')
    min_quality_score = request.session.get('min_quality_score', 60)
    max_to_score = request.session.get('max_to_score', 30)

    try:
        # Save session to database
        session_id = db.save_session_start(
            topic=topic,
            num_queries=num_queries,
            ai_mode=ai_enhancement,
            query_focus=query_focus,
            min_quality_score=min_quality_score,
            max_sources=max_sources
        )
        request.session['session_id'] = session_id
        print(f"Saved session to database (ID: {session_id})")

        # Generate diverse queries
        from research_to_pdf import generate_search_queries_advanced

        if ai_enhancement == 'none':
            queries = [
                f"{topic} guide",
                f"{topic} tutorial",
                f"{topic} overview",
                f"{topic} documentation",
                f"{topic} examples"
            ][:num_queries]
        else:
            queries = generate_search_queries_advanced(topic, num_queries=num_queries, focus=query_focus)

        request.session['queries'] = queries

        # Save queries to database
        db.save_queries(session_id, queries)

        # Get AI analysis
        user_id = get_user_id(request)
        query_analysis = ai.analyze_queries(user_id, topic, queries)
        coaching_tips = ai.get_ai_coaching(user_id, 'queries')

        import html as html_module
        queries_html = ""
        for i, query in enumerate(queries, 1):
            escaped_query = html_module.escape(query, quote=True)
            queries_html += f'''
            <div class="query-item" style="display: flex; align-items: center; gap: 10px;">
                <input type="checkbox" class="query-checkbox" name="selected_queries"
                       value="{escaped_query}" checked onchange="updateQueryCount()"
                       style="transform: scale(1.3); cursor: pointer;">
                <div style="flex: 1;">
                    <strong>{i}.</strong> {query}
                </div>
            </div>
            '''

        content = f'''
        <h2>Step 2: Review and Select Search Queries</h2>
        <p><strong>Topic:</strong> {topic}</p>
        <p><strong>Generated:</strong> {len(queries)} queries</p>

        <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2196f3;">
            <div style="white-space: pre-wrap; font-size: 14px; line-height: 1.6;">{query_analysis}</div>
        </div>

        <div style="background: #fff3cd; padding: 12px 15px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #ffc107;">
            <strong>Query Tips:</strong>
            <ul style="margin: 8px 0 0 0; padding-left: 20px; font-size: 14px;">
                {chr(10).join([f'<li>{tip}</li>' for tip in coaching_tips])}
            </ul>
        </div>

        <div style="margin: 20px 0;">
            <button type="button" class="secondary" onclick="selectAllQueries(true)">Select All</button>
            <button type="button" class="secondary" onclick="selectAllQueries(false)">Deselect All</button>
            <span id="selectedCount" style="margin-left: 20px; font-weight: 600; color: #007bff;">
                {len(queries)} queries selected
            </span>
        </div>

        <h3>Select Queries to Search:</h3>
        <form method="POST" action="/search_web" id="queryForm">
            {queries_html}

            <div style="margin-top: 20px;">
                <button type="submit" id="searchButton">Search Web</button>
                <button type="button" class="secondary" onclick="window.location.href='/'">Back</button>
            </div>
        </form>

        <script>
        function selectAllQueries(selected) {{
            document.querySelectorAll('.query-checkbox').forEach(checkbox => {{
                checkbox.checked = selected;
            }});
            updateQueryCount();
        }}

        function updateQueryCount() {{
            const checkboxes = document.querySelectorAll('.query-checkbox');
            const selected = Array.from(checkboxes).filter(cb => cb.checked).length;
            const total = checkboxes.length;
            const countSpan = document.getElementById('selectedCount');
            const searchButton = document.getElementById('searchButton');

            countSpan.textContent = selected + ' of ' + total + ' queries selected';

            if (selected === 0) {{
                countSpan.style.color = '#dc3545';
                searchButton.disabled = true;
            }} else {{
                countSpan.style.color = '#007bff';
                searchButton.disabled = false;
            }}
        }}

        updateQueryCount();
        </script>
        '''

        return render_template(content)

    except Exception as e:
        content = f'''
        <div class="error">Error generating queries: {str(e)}</div>
        <button onclick="window.location.href='/'">Back</button>
        '''
        return render_template(content)


@app.post("/generate_queries", response_class=HTMLResponse)
async def generate_queries_post(
    request: Request,
    topic: str = Form(...),
    num_queries: int = Form(7),
    results_per_query: int = Form(30),
    max_sources: int = Form(50),
    query_focus: str = Form("balanced"),
    ai_enhancement: str = Form("basic"),
    min_quality_score: int = Form(60),
    max_to_score: int = Form(30)
):
    """POST handler for generate queries"""
    request.session['topic'] = topic.strip()
    request.session['num_queries'] = num_queries
    request.session['results_per_query'] = results_per_query
    request.session['max_sources'] = max_sources
    request.session['query_focus'] = query_focus
    request.session['ai_enhancement'] = ai_enhancement
    request.session['min_quality_score'] = min_quality_score
    request.session['max_to_score'] = max_to_score
    return await generate_queries(request)


@app.post("/search_web", response_class=HTMLResponse)
async def search_route(request: Request):
    """Search web with selected queries"""
    print("\n" + "="*60)
    print("SEARCH_WEB ROUTE CALLED (FastAPI)")
    print("="*60)

    form_data = await request.form()

    # Check if this is auto-search from AI agent mode
    auto_search = form_data.get('auto_search')

    if auto_search:
        # Collect edited/selected queries from AI agent mode
        selected_queries = []
        i = 0
        while True:
            query_key = f'query_{i}'
            use_key = f'use_query_{i}'

            if query_key not in form_data:
                break

            if use_key in form_data:
                query_text = form_data.get(query_key, '').strip()
                if query_text:
                    selected_queries.append(query_text)

            i += 1

        print(f"AI auto-search mode: using {len(selected_queries)} edited/selected queries")
    else:
        # Get selected queries from form (manual selection)
        selected_queries = form_data.getlist('selected_queries')
        selected_queries = [q.strip() for q in selected_queries if q and q.strip()]

    topic = request.session.get('topic', '')
    results_per_query = request.session.get('results_per_query', 30)
    max_sources = request.session.get('max_sources', 50)
    ai_enhancement = request.session.get('ai_enhancement', 'basic')
    min_quality_score = request.session.get('min_quality_score', 60)
    max_to_score = request.session.get('max_to_score', 30)

    print(f"Selected queries: {len(selected_queries)}")
    print(f"AI mode: {ai_enhancement}")

    if not selected_queries:
        content = '''
        <div class="error">No queries selected. Please select at least one query to search.</div>
        <button onclick="window.history.back()">Back</button>
        '''
        return render_template(content)

    request.session['selected_queries'] = selected_queries

    # Update database with selected queries
    session_id = request.session.get('session_id')
    if session_id:
        all_queries = request.session.get('queries', [])
        db.save_queries(session_id, all_queries, selected_queries)

    try:
        # Search across selected queries
        all_results = []
        seen_urls = set()

        print(f"\nSearching {len(selected_queries)} selected queries...")

        for query in selected_queries:
            print(f"Searching query: {query}")
            search_results = search_web(query, num_results=results_per_query)

            for r in search_results:
                url = r.get("url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append({
                        "title": r.get("title", "No title"),
                        "url": url,
                        "query": query
                    })

        print(f"\nFound {len(all_results)} unique results")

        # Apply AI quality filtering if enabled
        if ai_enhancement in ['quality', 'premium']:
            from research_to_pdf import filter_results_by_quality
            print(f"\nApplying AI quality filtering...")
            all_results = filter_results_by_quality(topic, all_results, min_score=min_quality_score, max_to_score=max_to_score)
            print(f"Filtered to {len(all_results)} results")

        # Limit to configured max sources
        urls = all_results[:max_sources]

        # Highlight preferred sources
        user_id = get_user_id(request)
        urls = ai.highlight_preferred_sources(user_id, urls)

        # Save sources to database
        if session_id:
            db.save_sources(session_id, urls)

        request.session['urls'] = urls

        # Count preferred sources
        preferred_count = sum(1 for u in urls if u.get('is_preferred'))
        rejected_count = sum(1 for u in urls if u.get('is_rejected'))

        # Get coaching tips
        coaching_tips = ai.get_ai_coaching(user_id, 'sources')

        # Build sources HTML
        sources_html = ""
        for i, url_data in enumerate(urls):
            title = url_data['title']
            url = url_data['url']
            query_source = url_data.get('query', 'Unknown')
            relevance_score = url_data.get('relevance_score')
            score_reasoning = url_data.get('score_reasoning', '')
            is_preferred = url_data.get('is_preferred', False)
            is_rejected = url_data.get('is_rejected', False)
            preference_note = url_data.get('preference_note', '')

            checked = 'checked' if (is_preferred or (i < 10 and not is_rejected)) else ''
            border_color = '#4caf50' if is_preferred else ('#f44336' if is_rejected else '#ddd')
            bg_color = '#f1f8f4' if is_preferred else ('#fff5f5' if is_rejected else '#fff')
            query_display = query_source if len(query_source) <= 60 else query_source[:57] + "..."

            score_html = ''
            if relevance_score is not None:
                if relevance_score >= 80:
                    score_color, score_badge = '#4caf50', 'G'
                elif relevance_score >= 70:
                    score_color, score_badge = '#8bc34a', 'G'
                elif relevance_score >= 60:
                    score_color, score_badge = '#ffc107', 'Y'
                else:
                    score_color, score_badge = '#ff9800', 'O'

                score_html = f'''
                <div style="margin-top: 8px; padding: 8px; background: #f5f5f5; border-radius: 4px; font-size: 12px;">
                    <strong style="color: {score_color};">[{score_badge}] AI Quality Score: {relevance_score}/100</strong>
                    <div style="color: #666; margin-top: 4px; font-style: italic;">{score_reasoning}</div>
                </div>'''

            sources_html += f'''
            <div class="url-item" style="background: {bg_color}; border-left: 4px solid {border_color};">
                {f'<div style="background: {border_color}; color: white; padding: 6px 12px; margin: -15px -15px 10px -15px; font-size: 13px; font-weight: 600;">{preference_note}</div>' if preference_note else ''}
                <div style="display: flex; align-items: start; gap: 10px;">
                    <input type="checkbox" class="url-checkbox" name="selected_urls" value="{url}" {checked}
                           style="margin-top: 5px; transform: scale(1.3); cursor: pointer;">
                    <div style="flex: 1;">
                        <div class="url-title" style="font-weight: 600; margin-bottom: 5px;">{title}</div>
                        <div style="margin-bottom: 5px;">
                            <a href="{url}" target="_blank" rel="noopener noreferrer"
                               style="color: #007bff; text-decoration: none; font-size: 13px;">
                                {url}
                            </a>
                        </div>
                        <div style="font-size: 11px; color: #888; font-style: italic;">
                            Found by: {query_display}
                        </div>
                        {score_html}
                    </div>
                </div>
            </div>
            '''

        preferred_html = f'''
        <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50;">
            <strong>{preferred_count} sources from your preferred domains!</strong>
        </div>''' if preferred_count > 0 else ''

        rejected_html = f'''
        <div style="background: #ffebee; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f44336;">
            <strong>{rejected_count} sources from domains you typically skip</strong>
        </div>''' if rejected_count > 0 else ''

        content = f'''
        <h2>Step 3: Select Sources</h2>
        <p><strong>Topic:</strong> {topic}</p>
        <p><strong>Searched:</strong> {len(selected_queries)} queries</p>
        <p>Found <strong>{len(urls)}</strong> unique sources. Select which ones to include:</p>

        {preferred_html}
        {rejected_html}

        <div style="background: #fff3cd; padding: 12px 15px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #ffc107;">
            <strong>Source Selection Tips:</strong>
            <ul style="margin: 8px 0 0 0; padding-left: 20px; font-size: 14px;">
                {chr(10).join([f'<li>{tip}</li>' for tip in coaching_tips])}
            </ul>
        </div>

        <div style="margin: 20px 0;">
            <button type="button" class="secondary" onclick="selectAll(true)">Select All</button>
            <button type="button" class="secondary" onclick="selectAll(false)">Deselect All</button>
        </div>

        <form method="POST" action="/generate_pdf">
            {sources_html}

            <div style="margin-top: 20px;">
                <button type="submit">Generate PDF</button>
                <button type="button" class="secondary" onclick="window.location.href='/'">Start Over</button>
            </div>
        </form>

        <form method="POST" action="/cancel_session" style="margin-top: 10px;">
            <button type="submit" class="secondary" style="background: #dc3545;"
                    onclick="return confirm('Cancel this research session?')">
                Cancel Session
            </button>
        </form>
        '''

        return render_template(content)

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR IN SEARCH ROUTE: {error_details}")

        content = f'''
        <div class="error">
            <h3>Error searching:</h3>
            <p>{str(e)}</p>
        </div>
        <button onclick="window.location.href='/'">Back</button>
        '''
        return render_template(content)


@app.post("/generate_pdf", response_class=HTMLResponse)
async def generate_pdf(request: Request):
    """Generate PDF from selected sources"""
    form_data = await request.form()
    selected_urls = form_data.getlist('selected_urls')

    topic = request.session.get('topic', 'research')

    if not selected_urls:
        content = '''
        <div class="error">No URLs selected. Please select at least one source.</div>
        <button onclick="window.history.back()">Back</button>
        '''
        return render_template(content)

    request.session['selected_urls'] = selected_urls

    content = f'''
    <h2>Step 4: Generating PDF</h2>
    <p><strong>Topic:</strong> {topic}</p>
    <p><strong>Sources:</strong> {len(selected_urls)}</p>

    <div class="progress">
        <div class="progress-bar" style="width: 10%;">Starting...</div>
    </div>

    <div id="status">Fetching content...</div>

    <meta http-equiv="refresh" content="2;url=/generate_pdf_process?urls={len(selected_urls)}">
    '''

    return render_template(content)


@app.get("/generate_pdf_process", response_class=HTMLResponse)
async def generate_pdf_process(request: Request):
    """Process PDF generation"""
    topic = request.session.get('topic', 'research')
    selected_urls = request.session.get('selected_urls', [])
    session_id = request.session.get('session_id')

    if not selected_urls:
        return RedirectResponse(url="/", status_code=303)

    # Update database with final selected URLs
    if session_id:
        all_urls = request.session.get('urls', [])
        db.save_sources(session_id, all_urls, selected_urls)

        # Track source preferences in mem0
        user_id = get_user_id(request)
        for url_data in all_urls:
            if url_data['url'] in selected_urls:
                mem.add_source_preference(user_id, url_data, "selected", topic)

    try:
        sources = []
        for url in selected_urls:
            content_html = fetch_and_clean(url)
            if content_html:
                sources.append((url, content_html))

        if not sources:
            content = '''
            <div class="error">No content could be fetched. Please try different sources.</div>
            <button onclick="window.location.href='/'">Start Over</button>
            '''
            return render_template(content)

        # Build PDF
        html_doc = build_html_document(topic, sources)
        safe_topic = "".join(c for c in topic if c.isalnum() or c in (" ", "_", "-")).strip()
        if not safe_topic:
            safe_topic = "research"
        output_pdf = f"{safe_topic.replace(' ', '_')}.pdf"

        html_to_pdf(html_doc, output_pdf)

        # Mark session as completed
        if session_id:
            db.mark_session_complete(session_id)

            # Add to mem0 memory
            user_id = get_user_id(request)
            mem.add_research_memory(
                user_id=user_id,
                session_data={
                    'session_id': session_id,
                    'topic': topic,
                    'date': datetime.now().isoformat(),
                    'ai_mode': request.session.get('ai_enhancement', 'basic'),
                    'query_focus': request.session.get('query_focus', 'balanced'),
                    'num_queries': request.session.get('num_queries', 0),
                    'total_sources': len(request.session.get('urls', [])),
                    'selected_sources': len(sources),
                    'top_queries': request.session.get('selected_queries', [])[:3],
                    'min_quality_score': request.session.get('min_quality_score', 60)
                }
            )

        request.session['pdf_path'] = output_pdf
        request.session['source_count'] = len(sources)

        # Get personalized completion insights
        user_id = get_user_id(request)
        completion_insights = ai.generate_personalized_summary(user_id, {
            'topic': topic,
            'selected_sources': len(sources),
            'total_sources': len(request.session.get('urls', []))
        })
        next_research = ai.suggest_next_research(user_id)
        coaching_tips = ai.get_ai_coaching(user_id, 'complete')

        insights_html = ''
        if completion_insights:
            insights_html = '''
            <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2196f3;">
                <strong>Your Research Insights:</strong>
                <ul style="margin: 8px 0 0 0; padding-left: 20px; font-size: 14px;">''' + chr(10).join([f'<li>{insight}</li>' for insight in completion_insights]) + '''
                </ul>
            </div>'''

        next_html = ''
        if next_research:
            next_html = f'''
            <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50;">
                <strong>Suggested Next Research:</strong>
                <p style="margin: 8px 0 0 0; font-size: 14px;">{next_research}</p>
            </div>'''

        content = f'''
        <h2>Success!</h2>

        <div class="success">
            Your research PDF has been generated successfully!
        </div>

        <p><strong>Topic:</strong> {topic}</p>
        <p><strong>Sources included:</strong> {len(sources)}</p>
        <p><strong>Filename:</strong> <code>{output_pdf}</code></p>

        {insights_html}
        {next_html}

        <div style="background: #fff3cd; padding: 12px 15px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #ffc107;">
            <strong>What's Next:</strong>
            <ul style="margin: 8px 0 0 0; padding-left: 20px; font-size: 14px;">
                {chr(10).join([f'<li>{tip}</li>' for tip in coaching_tips])}
            </ul>
        </div>

        <div style="margin: 20px 0;">
            <button onclick="window.location.href='/download?file={output_pdf}'">Download PDF</button>
            <button class="secondary" onclick="window.location.href='/'">Research Another Topic</button>
        </div>

        <div class="next-steps">
            <h3>Next Steps:</h3>
            <ul>
                <li><strong>Upload to NotebookLM:</strong> Go to <a href="https://notebooklm.google.com" target="_blank">notebooklm.google.com</a></li>
                <li><strong>Generate audio summaries:</strong> Let NotebookLM create podcast-style explanations</li>
                <li><strong>Ask questions:</strong> Chat with your research content</li>
            </ul>
        </div>
        '''

        return render_template(content)

    except Exception as e:
        content = f'''
        <div class="error">Error generating PDF: {str(e)}</div>
        <button onclick="window.location.href='/'">Start Over</button>
        '''
        return render_template(content)


@app.post("/cancel_session", response_class=HTMLResponse)
async def cancel_session_route(request: Request):
    """Cancel current session"""
    form_data = await request.form()
    session_id_from_form = form_data.get('session_id_to_cancel')

    if session_id_from_form:
        session_id = int(session_id_from_form)
        sess = db.get_session_details(session_id)
        topic = sess.get('topic', 'Unknown')
        db.cancel_session(session_id)
    else:
        session_id = request.session.get('session_id')
        topic = request.session.get('topic', 'Unknown')
        user_id = get_user_id(request)

        if session_id:
            db.cancel_session(session_id)

        # Clear session data but keep user_id
        for key in list(request.session.keys()):
            if key != 'user_id':
                del request.session[key]

    content = f'''
    <h2>Session Cancelled</h2>

    <div style="background: #fff3cd; padding: 20px; border-radius: 8px; border-left: 4px solid #ffc107; margin: 20px 0;">
        <strong>Session closed without generating PDF</strong>
        <p style="margin: 10px 0 0 0;">Topic: {topic}</p>
    </div>

    <div class="info">
        <strong>What was saved:</strong>
        <ul>
            <li>Your search queries (for learning patterns)</li>
            <li>Sources found (for preference tracking)</li>
        </ul>
    </div>

    <div style="margin: 30px 0;">
        <button onclick="window.location.href='/'">Start New Research</button>
        <button class="secondary" onclick="window.location.href='/history'">View History</button>
    </div>
    '''

    return render_template(content)


@app.get("/download")
async def download(request: Request, file: Optional[str] = None):
    """Download generated PDF"""
    pdf_filename = file or request.session.get('pdf_path')

    if not pdf_filename:
        raise HTTPException(status_code=404, detail="PDF filename not specified")

    # Security: Only allow filenames, not paths
    pdf_filename = os.path.basename(pdf_filename)

    if pdf_filename and os.path.exists(pdf_filename):
        return FileResponse(pdf_filename, filename=pdf_filename, media_type='application/pdf')
    else:
        raise HTTPException(status_code=404, detail=f"PDF file '{pdf_filename}' not found")


@app.get("/history", response_class=HTMLResponse)
async def history(request: Request):
    """View recent research sessions"""
    sessions = db.get_recent_sessions(limit=20)

    sessions_html = ""
    if not sessions:
        sessions_html = '''
        <div class="info">
            <p>No research sessions found. Start a new research session to build your history!</p>
        </div>
        '''
    else:
        for sess in sessions:
            session_id = sess['id']
            topic = sess['topic']
            date = sess['date']
            ai_mode = sess.get('ai_mode', 'N/A')
            completed = sess['completed']
            cancelled = sess.get('cancelled', 0)
            query_count = sess.get('query_count', 0)
            source_count = sess.get('source_count', 0)
            selected_count = sess.get('selected_count', 0)

            if cancelled:
                status_badge, status_color = 'Cancelled', '#dc3545'
            elif completed:
                status_badge, status_color = 'Complete', '#28a745'
            else:
                status_badge, status_color = 'In Progress', '#ffc107'

            sessions_html += f'''
            <div class="url-item" style="cursor: pointer; border-left: 4px solid {status_color};"
                 onclick="window.location.href='/session/{session_id}'">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <div class="url-title" style="font-size: 18px; margin-bottom: 8px;">{topic}</div>
                        <div style="font-size: 13px; color: #666; margin-bottom: 8px;">
                            {date} | {ai_mode} mode
                        </div>
                        <div style="font-size: 13px; color: #666;">
                            {query_count} queries | {source_count} sources | {selected_count} selected
                        </div>
                    </div>
                    <div style="background: {status_color}; color: white; padding: 5px 12px; border-radius: 4px; font-size: 12px; font-weight: 600;">
                        {status_badge}
                    </div>
                </div>
            </div>
            '''

    content = f'''
    <h2>Research History</h2>
    <p>View your past research sessions and their results.</p>

    <div style="margin: 20px 0;">
        <button onclick="window.location.href='/'">Back to Home</button>
        <button class="secondary" onclick="window.location.href='/analytics'">View Analytics</button>
    </div>

    {sessions_html}

    <div style="margin-top: 20px;">
        <button onclick="window.location.href='/'">Back to Home</button>
    </div>
    '''

    return render_template(content)


@app.get("/session/{session_id}", response_class=HTMLResponse)
async def view_session(request: Request, session_id: int):
    """View details of a specific research session"""
    try:
        sess = db.get_session_details(session_id)
    except:
        content = '''
        <div class="error">Session not found.</div>
        <button onclick="window.location.href='/history'">Back to History</button>
        '''
        return render_template(content)

    topic = sess['topic']
    date = sess['date']
    ai_mode = sess.get('ai_mode', 'N/A')
    completed = sess['completed']
    cancelled = sess.get('cancelled', 0)
    queries = sess.get('queries', [])
    sources = sess.get('sources', [])

    if cancelled:
        status_badge = 'Cancelled'
    elif completed:
        status_badge = 'Complete'
    else:
        status_badge = 'In Progress'

    queries_html = ""
    if queries:
        for query in queries:
            query_text = query['query_text']
            selected = query.get('selected', 0)
            badge_color = '#28a745' if selected else '#ccc'
            queries_html += f'''
            <div class="query-item" style="border-left-color: {badge_color};">
                <strong style="color: {badge_color};">{'[Y]' if selected else '[N]'}</strong> {query_text}
            </div>
            '''

    sources_html = ""
    if sources:
        for source in sources:
            url = source['url']
            title = source.get('title', 'No title')
            selected = source.get('selected', 0)
            badge_color = '#28a745' if selected else '#e0e0e0'
            sources_html += f'''
            <div class="url-item" style="border-left: 4px solid {badge_color};">
                <div class="url-title">{title}</div>
                <div style="margin: 5px 0;">
                    <a href="{url}" target="_blank" style="color: #007bff; text-decoration: none; font-size: 13px;">
                        {url}
                    </a>
                </div>
            </div>
            '''

    content = f'''
    <h2>Session Details</h2>

    <div style="margin: 20px 0;">
        <button onclick="window.location.href='/history'">Back to History</button>
        <button class="secondary" onclick="window.location.href='/'">Home</button>
    </div>

    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin-top: 0;">{topic}</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 14px;">
            <div><strong>Date:</strong> {date}</div>
            <div><strong>Status:</strong> {status_badge}</div>
            <div><strong>AI Mode:</strong> {ai_mode}</div>
            <div><strong>Session ID:</strong> #{session_id}</div>
        </div>
    </div>

    <h3>Generated Queries ({len(queries)})</h3>
    {queries_html if queries else '<p>No queries found.</p>'}

    <h3>Sources Found ({len(sources)})</h3>
    {sources_html if sources else '<p>No sources found.</p>'}

    <div style="margin-top: 20px;">
        <button onclick="window.location.href='/history'">Back to History</button>
    </div>
    '''

    return render_template(content)


@app.get("/mem0-monitor", response_class=HTMLResponse)
async def mem0_monitor(request: Request):
    """Mem0 usage monitoring dashboard"""
    user_id = get_user_id(request)

    total_stats = mem.get_total_stats()
    cost_breakdown = mem.get_cost_breakdown()
    usage_stats = mem.get_usage_stats(days=7)

    cost_html = ""
    for item in cost_breakdown:
        percentage = (item['count'] / total_stats['total_operations'] * 100) if total_stats['total_operations'] > 0 else 0
        cost_html += f'''
        <div style="background: #f8f9fa; padding: 12px; margin: 8px 0; border-left: 4px solid #007bff; border-radius: 4px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>{item['operation'].upper()}</strong>
                    <span style="color: #666; margin-left: 10px;">({item['count']} ops, {percentage:.1f}%)</span>
                </div>
                <div>
                    <span style="background: #007bff; color: white; padding: 4px 12px; border-radius: 12px; font-size: 13px;">
                        ${item['cost']:.5f}
                    </span>
                </div>
            </div>
        </div>
        '''

    usage_html = ""
    if usage_stats:
        for day in usage_stats:
            usage_html += f'''
            <div style="background: #f8f9fa; padding: 12px; margin: 8px 0; border-radius: 4px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div><strong>{day['date']}</strong></div>
                    <div style="font-size: 13px;">
                        {day['operations'] or 0} ops |
                        {day['memories'] or 0} memories |
                        ${day['cost'] or 0:.4f}
                    </div>
                </div>
            </div>
            '''
    else:
        usage_html = '<p>No usage data available yet.</p>'

    content = f'''
    <h2>Mem0 Memory System Monitor</h2>

    <div style="margin: 20px 0;">
        <button onclick="window.location.href='/history'">Back to History</button>
        <button class="secondary" onclick="window.location.href='/mem0-context'">Manage Context</button>
        <button class="secondary" onclick="window.location.href='/mem0-memories'">View Memories</button>
        <button class="secondary" onclick="window.location.href='/mem0-preferences'">My Preferences</button>
    </div>

    <h3>Overall Statistics</h3>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin: 20px 0;">
        <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; text-align: center;">
            <div style="font-size: 32px; font-weight: 600; color: #1976d2;">{total_stats['total_operations']}</div>
            <div style="color: #666; font-size: 13px;">Total Operations</div>
        </div>
        <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; text-align: center;">
            <div style="font-size: 32px; font-weight: 600; color: #388e3c;">{total_stats['total_adds']}</div>
            <div style="color: #666; font-size: 13px;">Memories Added</div>
        </div>
        <div style="background: #fce4ec; padding: 15px; border-radius: 8px; text-align: center;">
            <div style="font-size: 32px; font-weight: 600; color: #c2185b;">${total_stats['total_cost']:.4f}</div>
            <div style="color: #666; font-size: 13px;">Total Cost</div>
        </div>
        <div style="background: #e0f2f1; padding: 15px; border-radius: 8px; text-align: center;">
            <div style="font-size: 32px; font-weight: 600; color: #00796b;">{total_stats['success_rate']:.1f}%</div>
            <div style="color: #666; font-size: 13px;">Success Rate</div>
        </div>
    </div>

    <h3>Cost Breakdown by Operation</h3>
    <div style="margin: 20px 0;">
        {cost_html}
    </div>

    <h3>7-Day Usage Trend</h3>
    <div style="margin: 20px 0;">
        {usage_html}
    </div>

    <div style="margin-top: 20px;">
        <button onclick="window.location.href='/history'">Back to History</button>
    </div>
    '''

    return render_template(content)


@app.get("/mem0-context", response_class=HTMLResponse)
@app.post("/mem0-context", response_class=HTMLResponse)
async def mem0_context(request: Request):
    """Persistent context management interface"""
    user_id = get_user_id(request)
    message = ""

    if request.method == 'POST':
        form_data = await request.form()
        action = form_data.get('action')

        if action == 'add_context':
            context_text = form_data.get('context_text', '').strip()
            context_type = form_data.get('context_type', 'general')

            if context_text:
                context_id = mem.add_persistent_context(user_id, context_text, context_type)
                if context_id:
                    message = '<div class="success">Persistent context added successfully!</div>'
                else:
                    message = '<div class="error">Failed to add persistent context.</div>'

        elif action == 'remove_context':
            context_id = form_data.get('context_id')
            if context_id:
                success = mem.remove_persistent_context(user_id, int(context_id))
                if success:
                    message = '<div class="success">Context removed successfully!</div>'

        elif action == 'clear_all':
            count = mem.clear_all_persistent_contexts(user_id)
            message = f'<div class="success">Cleared {count} persistent contexts.</div>'

        elif action == 'add_memory':
            memory_text = form_data.get('memory_text', '').strip()
            memory_type = form_data.get('memory_type', 'manual')

            if memory_text:
                result = mem.add_manual_memory(user_id, memory_text, memory_type)
                if result:
                    message = '<div class="success">Manual memory added successfully!</div>'
                else:
                    message = '<div class="error">Failed to add manual memory.</div>'

    contexts = mem.get_persistent_contexts(user_id)

    contexts_html = ""
    if contexts:
        for ctx in contexts:
            contexts_html += f'''
            <div style="background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 6px; border-left: 4px solid #90caf9;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1; margin-right: 15px;">
                        <div style="font-size: 14px; line-height: 1.5; color: #333;">{ctx['context_text']}</div>
                        <div style="font-size: 12px; color: #888; margin-top: 8px;">[{ctx['context_type']}] Added: {ctx['created_at']}</div>
                    </div>
                    <form method="POST" style="display: inline;">
                        <input type="hidden" name="action" value="remove_context">
                        <input type="hidden" name="context_id" value="{ctx['id']}">
                        <button type="submit" class="secondary" style="padding: 6px 12px; font-size: 13px;"
                                onclick="return confirm('Remove this context?')">Remove</button>
                    </form>
                </div>
            </div>
            '''
    else:
        contexts_html = '''
        <div style="background: #fff3cd; padding: 15px; border-radius: 6px; border-left: 4px solid #ffc107;">
            <p style="margin: 0;">No persistent contexts yet. Add one below to get started!</p>
        </div>
        '''

    content = f'''
    <h2>Persistent Context Management</h2>
    <p>Manage persistent contexts that will be automatically injected into all AI query generations.</p>

    <div style="margin: 20px 0;">
        <button onclick="window.location.href='/mem0-monitor'">Back to Monitor</button>
        <button class="secondary" onclick="window.location.href='/mem0-memories'">View Memories</button>
    </div>

    {message}

    <h3>Current Persistent Contexts ({len(contexts)})</h3>
    {contexts_html}

    <h3 style="margin-top: 30px;">Add New Persistent Context</h3>
    <form method="POST" style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
        <input type="hidden" name="action" value="add_context">

        <div style="margin-bottom: 15px;">
            <label style="display: block; font-weight: 600; margin-bottom: 5px;">Context Type:</label>
            <select name="context_type" style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;">
                <option value="general">General</option>
                <option value="preference">Preference</option>
                <option value="instruction">Instruction</option>
                <option value="fact">Fact</option>
            </select>
        </div>

        <div style="margin-bottom: 15px;">
            <label style="display: block; font-weight: 600; margin-bottom: 5px;">Context Text:</label>
            <textarea name="context_text" rows="4"
                      style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;"
                      placeholder="E.g., 'I prefer academic papers and peer-reviewed sources'"
                      required></textarea>
        </div>

        <button type="submit" style="padding: 12px 24px; background: #4caf50; color: white; border: none; border-radius: 4px;">
            Add Persistent Context
        </button>
    </form>

    <h3 style="margin-top: 40px;">Add Manual Memory</h3>
    <form method="POST" style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
        <input type="hidden" name="action" value="add_memory">

        <div style="margin-bottom: 15px;">
            <label style="display: block; font-weight: 600; margin-bottom: 5px;">Memory Type:</label>
            <select name="memory_type" style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;">
                <option value="manual">Manual Note</option>
                <option value="fact">Fact</option>
                <option value="insight">Insight</option>
            </select>
        </div>

        <div style="margin-bottom: 15px;">
            <label style="display: block; font-weight: 600; margin-bottom: 5px;">Memory Text:</label>
            <textarea name="memory_text" rows="4"
                      style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;"
                      placeholder="E.g., 'Found excellent paper on transformer architectures'"
                      required></textarea>
        </div>

        <button type="submit" style="padding: 12px 24px; background: #2196f3; color: white; border: none; border-radius: 4px;">
            Add Manual Memory
        </button>
    </form>

    <div style="margin-top: 30px;">
        <button onclick="window.location.href='/mem0-monitor'">Back to Monitor</button>
    </div>
    '''

    return render_template(content)


@app.get("/mem0-memories", response_class=HTMLResponse)
async def mem0_memories(request: Request):
    """View all mem0 memories for current user"""
    user_id = get_user_id(request)
    memories = mem.get_all_memories(user_id, limit=100)

    memories_html = ""
    if not memories:
        memories_html = '''
        <div class="info">
            <p>No memories stored yet. Complete a research session to start building your memory!</p>
        </div>
        '''
    else:
        for i, memory in enumerate(memories, 1):
            if not isinstance(memory, dict):
                continue
            metadata = memory.get('metadata', {})
            memory_type = metadata.get('type', 'unknown')
            memory_text = memory.get('memory', 'No content')

            if memory_type == 'research_session':
                color, icon = '#2196f3', 'R'
            elif memory_type == 'source_preference':
                color, icon = '#4caf50', 'S'
            else:
                color, icon = '#9e9e9e', 'M'

            memories_html += f'''
            <div style="background: white; border-left: 4px solid {color}; padding: 15px; margin: 12px 0; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                    <div style="font-weight: 600; color: {color};">
                        [{icon}] {memory_type.replace('_', ' ').title()}
                    </div>
                    <div style="font-size: 11px; color: #999;">Memory #{i}</div>
                </div>
                <div style="white-space: pre-wrap; font-size: 13px; line-height: 1.6; color: #333;">
{memory_text}
                </div>
            </div>
            '''

    content = f'''
    <h2>My Research Memories</h2>
    <p>Semantic memories stored by the AI memory system.</p>

    <div style="margin: 20px 0;">
        <button onclick="window.location.href='/mem0-monitor'">Back to Monitor</button>
        <button class="secondary" onclick="window.location.href='/mem0-preferences'">View Preferences</button>
    </div>

    <p><strong>Total Memories:</strong> {len(memories)}</p>

    {memories_html}

    <div style="margin-top: 20px;">
        <button onclick="window.location.href='/mem0-monitor'">Back to Monitor</button>
    </div>
    '''

    return render_template(content)


@app.get("/mem0-preferences", response_class=HTMLResponse)
async def mem0_preferences(request: Request):
    """View learned user preferences"""
    user_id = get_user_id(request)
    preferences = mem.get_user_preferences(user_id)

    prefs_html = ""

    if preferences.get('preferred_domains'):
        prefs_html += '<h3>Preferred Source Domains</h3><div style="margin: 20px 0;">'
        for domain, count in preferences['preferred_domains']:
            prefs_html += f'''
            <div style="background: #e8f5e9; padding: 10px 15px; margin: 6px 0; border-left: 4px solid #4caf50; border-radius: 4px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>{domain}</strong>
                    <span style="background: #4caf50; color: white; padding: 3px 10px; border-radius: 12px; font-size: 12px;">
                        Selected {count} times
                    </span>
                </div>
            </div>
            '''
        prefs_html += '</div>'

    if preferences.get('topics'):
        prefs_html += '<h3>Frequently Researched Topics</h3><div style="margin: 20px 0;">'
        for topic, count in preferences['topics']:
            prefs_html += f'''
            <div style="background: #fff3e0; padding: 10px 15px; margin: 6px 0; border-left: 4px solid #ff9800; border-radius: 4px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>{topic}</strong>
                    <span style="background: #ff9800; color: white; padding: 3px 10px; border-radius: 12px; font-size: 12px;">
                        {count} sessions
                    </span>
                </div>
            </div>
            '''
        prefs_html += '</div>'

    if not prefs_html:
        prefs_html = '''
        <div class="info">
            <p>No preferences learned yet. Complete more research sessions to build your preference profile!</p>
        </div>
        '''

    content = f'''
    <h2>My Research Preferences</h2>
    <p>Learned preferences based on your research history.</p>

    <div style="margin: 20px 0;">
        <button onclick="window.location.href='/mem0-monitor'">Back to Monitor</button>
        <button class="secondary" onclick="window.location.href='/mem0-memories'">View Memories</button>
    </div>

    {prefs_html}

    <div style="margin-top: 20px;">
        <button onclick="window.location.href='/mem0-monitor'">Back to Monitor</button>
    </div>
    '''

    return render_template(content)


@app.get("/analytics", response_class=HTMLResponse)
async def analytics(request: Request):
    """View overall research analytics"""
    stats = db.get_research_stats()
    favorite_sources = db.get_favorite_sources(min_selections=2)

    total_sessions = stats.get('total_sessions', 0)
    completed_sessions = stats.get('completed_sessions', 0)
    total_sources = stats.get('total_sources', 0)
    selected_sources = stats.get('selected_sources', 0)

    completion_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
    selection_rate = (selected_sources / total_sources * 100) if total_sources > 0 else 0

    topics_html = ""
    if stats.get('top_topics'):
        for topic in stats['top_topics']:
            topics_html += f'''
            <div style="background: #e8f5e9; padding: 10px 15px; margin: 6px 0; border-left: 4px solid #4caf50; border-radius: 4px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>{topic['topic']}</strong>
                    <span style="background: #4caf50; color: white; padding: 3px 10px; border-radius: 12px; font-size: 12px;">
                        {topic['count']} sessions
                    </span>
                </div>
            </div>
            '''

    content = f'''
    <h2>Research Analytics</h2>

    <div style="margin: 20px 0;">
        <button onclick="window.location.href='/history'">Back to History</button>
        <button class="secondary" onclick="window.location.href='/'">Home</button>
    </div>

    <h3>Overall Statistics</h3>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin: 20px 0;">
        <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; text-align: center;">
            <div style="font-size: 32px; font-weight: 600; color: #1976d2;">{total_sessions}</div>
            <div style="color: #666; font-size: 13px;">Total Sessions</div>
        </div>
        <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; text-align: center;">
            <div style="font-size: 32px; font-weight: 600; color: #388e3c;">{completed_sessions}</div>
            <div style="color: #666; font-size: 13px;">Completed</div>
        </div>
        <div style="background: #fff3e0; padding: 15px; border-radius: 8px; text-align: center;">
            <div style="font-size: 32px; font-weight: 600; color: #f57c00;">{completion_rate:.0f}%</div>
            <div style="color: #666; font-size: 13px;">Completion Rate</div>
        </div>
        <div style="background: #fce4ec; padding: 15px; border-radius: 8px; text-align: center;">
            <div style="font-size: 32px; font-weight: 600; color: #c2185b;">{total_sources}</div>
            <div style="color: #666; font-size: 13px;">Sources Found</div>
        </div>
        <div style="background: #e0f2f1; padding: 15px; border-radius: 8px; text-align: center;">
            <div style="font-size: 32px; font-weight: 600; color: #00796b;">{selected_sources}</div>
            <div style="color: #666; font-size: 13px;">Sources Selected</div>
        </div>
        <div style="background: #f3e5f5; padding: 15px; border-radius: 8px; text-align: center;">
            <div style="font-size: 32px; font-weight: 600; color: #7b1fa2;">{selection_rate:.0f}%</div>
            <div style="color: #666; font-size: 13px;">Selection Rate</div>
        </div>
    </div>

    <h3>Top Research Topics</h3>
    <div style="margin: 20px 0;">
        {topics_html if topics_html else '<p>No topics found yet.</p>'}
    </div>

    <div style="margin-top: 20px;">
        <button onclick="window.location.href='/history'">Back to History</button>
    </div>
    '''

    return render_template(content)


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "framework": "FastAPI"}


# OpenAPI docs are automatically available at /docs and /redoc
