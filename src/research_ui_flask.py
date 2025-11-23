from flask import Flask, render_template_string, request, send_file, jsonify, session
import os
import secrets
import json
from datetime import datetime
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

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Initialize database on startup
print("Initializing database...")
db.init_database()

# User ID tracking for mem0
def get_user_id():
    """Get or create user ID for memory tracking"""
    if 'user_id' not in session:
        session['user_id'] = secrets.token_hex(8)
    return session['user_id']

def build_html_from_markdown(topic, markdown_content):
    """Build HTML document from markdown content (for AI agent)"""
    try:
        import markdown
        html_body = markdown.markdown(markdown_content)
    except ImportError:
        # Fallback: preserve formatting with pre-wrap
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

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
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
            <h1>📚 Research to PDF</h1>
            <p>Turn any topic into a comprehensive research PDF for NotebookLM</p>
        </div>

        <div id="app">
            {{ content | safe }}
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
</html>
'''

@app.route('/')
def index():
    user_id = get_user_id()

    # Get personalized greeting
    greeting_data = ai.get_personalized_greeting(user_id)
    topic_suggestions = ai.get_topic_suggestions(user_id)
    smart_defaults = ai.get_smart_defaults(user_id)
    coaching_tips = ai.get_ai_coaching(user_id, 'start')

    content = f'''
    <!-- Personalized Greeting -->
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
        <h2 style="margin: 0 0 10px 0; color: white;">{greeting_data['greeting']}</h2>
        <p style="margin: 0; opacity: 0.9;">{greeting_data['suggestion']}</p>
    </div>

    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h2 style="margin: 0;">Step 1: Enter Your Research Topic</h2>
        <div>
            <button type="button" class="secondary" onclick="window.location.href='/history'">📜 History</button>
            <button type="button" class="secondary" onclick="window.location.href='/analytics'">📊 Analytics</button>
            <button type="button" class="secondary" onclick="window.location.href='/mem0-monitor'">🧠 Mem0</button>
        </div>
    </div>

    <!-- Topic Suggestions -->
    {'''
    <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #4caf50;">
        <strong>💡 Suggested Topics:</strong>
        <div style="margin-top: 10px;">''' +
        ''.join([f'''
            <button type="button" class="secondary" style="margin: 5px; background: #4caf50;"
                    onclick="document.getElementsByName('topic')[0].value = '{suggestion}'">
                {suggestion}
            </button>''' for suggestion in topic_suggestions]) +
        '''
        </div>
    </div>''' if topic_suggestions else ''
    }

    <!-- AI Coaching Tips -->
    <div style="background: #fff3cd; padding: 12px 15px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #ffc107;">
        <strong>🤖 AI Tips:</strong>
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
                            <strong style="color: #2e7d32;">🤖 AI-Powered Web Search (Default)</strong>
                            <div style="font-size: 13px; color: #555; margin-top: 4px;">
                                AI uses your mem0 context to generate smart queries, then searches the web for relevant URLs to download.
                            </div>
                        </div>
                    </label>
                </div>

                <div style="margin: 10px 0;">
                    <label style="display: flex; align-items: start; padding: 12px; background: #fff; border: 2px solid #ddd; border-radius: 6px; cursor: pointer;">
                        <input type="radio" name="research_mode" value="web_search" onclick="document.getElementById('webSearchConfig').style.display='block'" style="margin: 4px 10px 0 0;">
                        <div>
                            <strong>🔍 Web Search Mode</strong>
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
                    <small style="color: #666;">AI generates queries based on your mem0 research history and preferences</small>
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

                <small style="color: #666;">🤖 Uses gpt-4o-mini + your mem0 context to generate personalized search queries. Very affordable (~$0.001 per search)!</small>
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
                    <small style="color: #666;">More queries = more diverse sources but slower</small>
                </div>

                <div style="margin: 15px 0;">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Results per Query:</label>
                    <select name="results_per_query" style="width: 100%; padding: 8px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;">
                        <option value="10">10 results</option>
                        <option value="20">20 results</option>
                        <option value="30" selected>30 results</option>
                        <option value="50">50 results</option>
                    </select>
                    <small style="color: #666;">More results = better coverage but longer processing time</small>
                </div>

                <div style="margin: 15px 0;">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Max Total Sources:</label>
                    <select name="max_sources" style="width: 100%; padding: 8px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;">
                        <option value="30">30 sources</option>
                        <option value="50" selected>50 sources</option>
                        <option value="75">75 sources</option>
                        <option value="100">100 sources</option>
                    </select>
                    <small style="color: #666;">Maximum unique sources to display after deduplication</small>
                </div>

                <div style="margin: 15px 0;">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Query Focus:</label>
                    <select name="query_focus" style="width: 100%; padding: 8px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;">
                        <option value="balanced" selected>Balanced (mix of all types)</option>
                        <option value="academic">Academic (research papers, scholarly articles)</option>
                        <option value="practical">Practical (guides, tutorials, how-tos)</option>
                        <option value="recent">Recent (latest news, 2024-2025 updates)</option>
                        <option value="technical">Technical (documentation, specifications)</option>
                        <option value="comprehensive">Comprehensive (overview, foundational)</option>
                    </select>
                    <small style="color: #666;">Prioritize certain types of sources in queries</small>
                </div>

                <div style="margin: 20px 0; padding: 20px; background: #e3f2fd; border-radius: 8px; border-left: 4px solid #2196f3;">
                    <h3 style="margin-top: 0; font-size: 18px; color: #1976d2;">🤖 AI Quality Enhancement</h3>

                    <div style="margin: 15px 0;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">AI Enhancement Level:</label>
                        <select name="ai_enhancement" style="width: 100%; padding: 8px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;">
                            <option value="none">None (Fastest, free search only)</option>
                            <option value="basic" selected>Basic (AI query generation only)</option>
                            <option value="quality">Quality Filtering (AI scores & filters sources)</option>
                            <option value="premium">Premium (AI scoring + summaries + refinement)</option>
                        </select>
                        <small style="color: #666;">
                            <strong>None:</strong> No OpenAI usage<br>
                            <strong>Basic:</strong> ~$0.0003 per session<br>
                            <strong>Quality:</strong> ~$0.01-0.03 per session<br>
                            <strong>Premium:</strong> ~$0.05-0.15 per session
                        </small>
                    </div>

                    <div style="margin: 15px 0;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">Minimum Quality Score:</label>
                        <select name="min_quality_score" style="width: 100%; padding: 8px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;">
                            <option value="0">0 - No filtering (keep all sources)</option>
                            <option value="40">40 - Low bar (remove obvious spam)</option>
                            <option value="60" selected>60 - Moderate (balanced quality)</option>
                            <option value="70">70 - High (strict quality standards)</option>
                            <option value="80">80 - Very High (only top-tier sources)</option>
                        </select>
                        <small style="color: #666;">Only applies when AI Enhancement is "Quality" or "Premium"</small>
                    </div>

                    <div style="margin: 15px 0;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">Max Sources to AI Score:</label>
                        <select name="max_to_score" style="width: 100%; padding: 8px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;">
                            <option value="10">10 sources (~20 sec, ~$0.005)</option>
                            <option value="20">20 sources (~40 sec, ~$0.01)</option>
                            <option value="30" selected>30 sources (~60 sec, ~$0.02)</option>
                            <option value="50">50 sources (~100 sec, ~$0.03)</option>
                        </select>
                        <small style="color: #666;">
                            Limits AI scoring to prevent timeouts. Remaining sources included unscored.
                        </small>
                    </div>
                </div>
            </div>
        </div>

        <button type="submit">Start Research →</button>

        <script>
            // Toggle between AI Agent and Web Search configs
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
    return render_template_string(HTML_TEMPLATE, content=content)

@app.route('/start_research', methods=['POST'])
def start_research():
    """Route research to either AI Agent or Web Search based on mode"""
    research_mode = request.form.get('research_mode', 'ai_agent')
    topic = request.form.get('topic', '').strip()

    if not topic:
        return index()

    if research_mode == 'ai_agent':
        # Use AI Research Agent
        return ai_research_route()
    else:
        # Use Web Search (forward to generate_queries)
        return generate_queries()

@app.route('/ai_research', methods=['POST'])
def ai_research_route():
    """Generate search queries using AI agent + mem0 context, then search web"""
    topic = request.form.get('topic', '').strip()
    num_queries = int(request.form.get('ai_num_queries', 7))
    results_per_query = int(request.form.get('ai_results_per_query', 30))
    max_sources = int(request.form.get('ai_max_sources', 50))
    user_id = get_user_id()

    if not topic:
        return index()

    # Save to session
    session['topic'] = topic
    session['num_queries'] = num_queries
    session['results_per_query'] = results_per_query
    session['max_sources'] = max_sources
    session['research_mode'] = 'ai_web_search'

    # Generate smart queries using AI + mem0
    queries = ai_agent.generate_smart_search_queries(user_id, topic, num_queries=num_queries)

    if not queries:
        content = '''
        <div class="error">Failed to generate search queries. Please try again.</div>
        <button onclick="window.location.href='/'">← Start Over</button>
        '''
        return render_template_string(HTML_TEMPLATE, content=content)

    # Save queries to session
    session['queries'] = queries

    # Display AI-generated queries with editing capabilities
    content = f'''
    <h2>🤖 AI-Generated Search Queries</h2>
    <p>Using your mem0 context and OpenAI, I've generated {len(queries)} optimized search queries for: <strong>{topic}</strong></p>

    <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50;">
        <h3 style="margin-top: 0; color: #2e7d32;">✓ Review and Edit Queries</h3>
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
                {"".join([f'''
                <div class="query-item" style="display: flex; align-items: center; gap: 10px; margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 6px;">
                    <input type="checkbox" class="query-checkbox" name="use_query_{i}" checked onchange="updateQueryCount()"
                           style="transform: scale(1.3); cursor: pointer;">
                    <div style="flex: 1;">
                        <input type="text" name="query_{i}" value="{q.replace('"', '&quot;')}"
                               style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
                               placeholder="Edit query...">
                    </div>
                    <button type="button" onclick="removeQuery(this)" class="secondary" style="padding: 6px 12px;">✕</button>
                </div>
                ''' for i, q in enumerate(queries)])}
            </div>

            <button type="button" onclick="addNewQuery()" class="secondary" style="margin-top: 10px;">
                ➕ Add New Query
            </button>
        </div>

        <div style="margin: 20px 0;">
            <button type="submit" style="padding: 12px 24px; background: #4caf50; color: white; border: none; border-radius: 4px; font-size: 16px; font-weight: 600; cursor: pointer;">
                🔍 Search Web with Selected Queries
            </button>
            <button type="button" class="secondary" onclick="window.location.href='/'">← Start Over</button>
        </div>
    </form>

    <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; border-left: 4px solid #2196f3;">
        <strong>💡 Tips:</strong>
        <ul style="margin: 8px 0 0 0; padding-left: 20px; font-size: 14px;">
            <li>Edit any query to refine your search</li>
            <li>Uncheck queries you don't want to use</li>
            <li>Add custom queries for specific topics</li>
            <li>Use search operators like "site:", quotes, OR for better results</li>
        </ul>
    </div>

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
                <button type="button" onclick="removeQuery(this)" class="secondary" style="padding: 6px 12px;">✕</button>
            `;
            queriesList.appendChild(newItem);
            queryCounter++;
            updateQueryCount();

            // Focus the new input
            newItem.querySelector('input[type="text"]').focus();
        }}
    </script>
    '''

    return render_template_string(HTML_TEMPLATE, content=content)

@app.route('/generate_queries', methods=['POST'])
def generate_queries():
    topic = request.form.get('topic', '').strip()
    if not topic:
        return index()

    # Get configurable parameters from form
    num_queries = int(request.form.get('num_queries', 7))
    results_per_query = int(request.form.get('results_per_query', 30))
    max_sources = int(request.form.get('max_sources', 50))
    query_focus = request.form.get('query_focus', 'balanced')
    ai_enhancement = request.form.get('ai_enhancement', 'basic')
    min_quality_score = int(request.form.get('min_quality_score', 60))
    max_to_score = int(request.form.get('max_to_score', 30))

    session['topic'] = topic
    session['num_queries'] = num_queries
    session['results_per_query'] = results_per_query
    session['max_sources'] = max_sources
    session['query_focus'] = query_focus
    session['ai_enhancement'] = ai_enhancement
    session['min_quality_score'] = min_quality_score
    session['max_to_score'] = max_to_score

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
        session['session_id'] = session_id
        print(f"✓ Saved session to database (ID: {session_id})")

        # Generate diverse queries for comprehensive research
        from research_to_pdf import generate_search_queries_advanced

        # Use AI or simple queries based on enhancement level
        if ai_enhancement == 'none':
            # Simple hardcoded queries, no AI
            queries = [
                f"{topic} guide",
                f"{topic} tutorial",
                f"{topic} overview",
                f"{topic} documentation",
                f"{topic} examples"
            ][:num_queries]
        else:
            queries = generate_search_queries_advanced(topic, num_queries=num_queries, focus=query_focus)

        session['queries'] = queries

        # Save queries to database
        db.save_queries(session_id, queries)
        print(f"✓ Saved {len(queries)} queries to database")

        # Get AI analysis of queries
        user_id = get_user_id()
        query_analysis = ai.analyze_queries(user_id, topic, queries)
        coaching_tips = ai.get_ai_coaching(user_id, 'queries')

        content = f'''
        <h2>Step 2: Review and Select Search Queries</h2>
        <p><strong>Topic:</strong> {topic}</p>
        <p><strong>Generated:</strong> {len(queries)} queries</p>

        <!-- AI Analysis -->
        <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2196f3;">
            <div style="white-space: pre-wrap; font-size: 14px; line-height: 1.6;">{query_analysis}</div>
        </div>

        <!-- AI Tips -->
        <div style="background: #fff3cd; padding: 12px 15px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #ffc107;">
            <strong>🤖 Query Tips:</strong>
            <ul style="margin: 8px 0 0 0; padding-left: 20px; font-size: 14px;">
                {chr(10).join([f'<li>{tip}</li>' for tip in coaching_tips])}
            </ul>
        </div>

        <div style="margin: 20px 0;">
            <button type="button" class="secondary" onclick="selectAllQueries(true)">✓ Select All</button>
            <button type="button" class="secondary" onclick="selectAllQueries(false)">✗ Deselect All</button>
            <span id="selectedCount" style="margin-left: 20px; font-weight: 600; color: #007bff;">
                {len(queries)} queries selected
            </span>
        </div>

        <h3>Select Queries to Search:</h3>
        <form method="POST" action="/search_web" id="queryForm">
        '''

        import html as html_module
        for i, query in enumerate(queries, 1):
            escaped_query = html_module.escape(query, quote=True)
            content += f'''
            <div class="query-item" style="display: flex; align-items: center; gap: 10px;">
                <input type="checkbox" class="query-checkbox" name="selected_queries"
                       value="{escaped_query}" checked onchange="updateQueryCount()"
                       style="transform: scale(1.3); cursor: pointer;">
                <div style="flex: 1;">
                    <strong>{i}.</strong> {query}
                </div>
            </div>
            '''

        # Add AI enhancement info if applicable
        ai_mode = session.get('ai_enhancement', 'basic')
        max_to_score_val = session.get('max_to_score', 30)

        if ai_mode in ['quality', 'premium']:
            estimated_time = max_to_score_val * 2  # ~2 seconds per source
            content += f'''
            <div style="margin: 20px 0; padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
                <strong>⚠️ AI Quality Mode Enabled</strong><br>
                <small>Searching will take approximately <strong>{estimated_time} seconds</strong> to score {max_to_score_val} sources with AI.
                Please be patient - your browser will show a loading indicator.</small>
            </div>
            '''

        # Calculate estimated time for progress bar
        num_selected_queries = len(session.get('queries', []))
        estimated_seconds = 10  # Base time for searching
        if ai_mode in ['quality', 'premium']:
            estimated_seconds += max_to_score_val * 2  # 2 seconds per AI score

        content += f'''
            <div style="margin-top: 20px;">
                <button type="submit" id="searchButton">Search Web →</button>
                <button type="button" class="secondary" onclick="window.location.href='/'">← Back</button>
            </div>
            <div id="loadingContainer" style="display: none; margin-top: 20px;">
                <div style="padding: 20px; background: #e3f2fd; border-radius: 8px;">
                    <div style="text-align: center; font-size: 20px; margin-bottom: 15px;">
                        🤖 <span id="loadingStatus">Searching and scoring sources...</span>
                    </div>

                    <!-- Progress Bar -->
                    <div style="background: #fff; border-radius: 10px; height: 30px; margin: 20px 0; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);">
                        <div id="progressBar" style="background: linear-gradient(90deg, #007bff, #0056b3); height: 100%; width: 0%; transition: width 0.5s ease; display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; font-size: 14px;">
                            <span id="progressText">0%</span>
                        </div>
                    </div>

                    <div style="text-align: center; font-size: 14px; color: #666;">
                        <div id="progressMessage">Starting search...</div>
                        <div style="margin-top: 10px;">
                            <strong>Estimated time:</strong> <span id="timeRemaining">{estimated_seconds}s</span>
                        </div>
                        <div style="margin-top: 10px; font-size: 12px;">
                            Do not close this window. Check terminal for detailed progress.
                        </div>
                    </div>
                </div>
            </div>
        </form>

        <script>
        const ESTIMATED_TOTAL_TIME = {estimated_seconds};  // seconds
        let progressInterval;
        let startTime;

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

        function updateProgress() {{
            const elapsed = (Date.now() - startTime) / 1000;
            const progress = Math.min((elapsed / ESTIMATED_TOTAL_TIME) * 100, 95);  // Cap at 95% until done
            const remaining = Math.max(ESTIMATED_TOTAL_TIME - elapsed, 0);

            document.getElementById('progressBar').style.width = progress + '%';
            document.getElementById('progressText').textContent = Math.round(progress) + '%';
            document.getElementById('timeRemaining').textContent = Math.round(remaining) + 's';

            // Update status message based on progress
            if (progress < 20) {{
                document.getElementById('progressMessage').textContent = 'Searching web sources...';
            }} else if (progress < 50) {{
                document.getElementById('progressMessage').textContent = 'AI scoring sources...';
            }} else if (progress < 80) {{
                document.getElementById('progressMessage').textContent = 'Filtering results...';
            }} else {{
                document.getElementById('progressMessage').textContent = 'Finalizing results...';
            }}
        }}

        // Show loading bar when form is submitted
        document.getElementById('queryForm').addEventListener('submit', function() {{
            document.getElementById('loadingContainer').style.display = 'block';
            document.getElementById('searchButton').disabled = true;
            document.getElementById('searchButton').textContent = 'Searching...';

            // Start progress animation
            startTime = Date.now();
            progressInterval = setInterval(updateProgress, 500);  // Update every 500ms
        }});

        // Initialize count on load
        updateQueryCount();
        </script>
        '''

        return render_template_string(HTML_TEMPLATE, content=content)

    except Exception as e:
        content = f'''
        <div class="error">Error generating queries: {str(e)}</div>
        <button onclick="window.location.href='/'">← Back</button>
        '''
        return render_template_string(HTML_TEMPLATE, content=content)

@app.route('/search_web', methods=['POST'])
def search():
    print("\n" + "="*60)
    print("SEARCH_WEB ROUTE CALLED")
    print("="*60)

    # Check if this is auto-search from AI agent mode
    auto_search = request.form.get('auto_search')

    if auto_search:
        # Collect edited/selected queries from AI agent mode
        selected_queries = []
        i = 0
        while True:
            query_key = f'query_{i}'
            use_key = f'use_query_{i}'

            # Check if this query index exists
            if query_key not in request.form:
                break

            # Only include if checkbox is checked
            if use_key in request.form:
                query_text = request.form.get(query_key, '').strip()
                if query_text:
                    selected_queries.append(query_text)

            i += 1

        print(f"AI auto-search mode: using {len(selected_queries)} edited/selected queries")
    else:
        # Get selected queries from form (manual selection)
        selected_queries = request.form.getlist('selected_queries')
        # Filter out empty queries
        selected_queries = [q.strip() for q in selected_queries if q and q.strip()]

    topic = session.get('topic', '')
    results_per_query = session.get('results_per_query', 30)
    max_sources = session.get('max_sources', 50)
    ai_enhancement = session.get('ai_enhancement', 'basic')
    min_quality_score = session.get('min_quality_score', 60)
    max_to_score = session.get('max_to_score', 30)

    print(f"Selected queries: {len(selected_queries)}")
    print(f"Queries: {selected_queries}")
    print(f"AI mode: {ai_enhancement}")
    print(f"Max to score: {max_to_score}")

    if not selected_queries:
        content = '''
        <div class="error">No queries selected. Please select at least one query to search.</div>
        <button onclick="window.history.back()">← Back</button>
        '''
        return render_template_string(HTML_TEMPLATE, content=content)

    # Store selected queries for reference
    session['selected_queries'] = selected_queries

    # Update database with selected queries
    session_id = session.get('session_id')
    if session_id:
        all_queries = session.get('queries', [])
        db.save_queries(session_id, all_queries, selected_queries)
        print(f"✓ Updated query selections in database")

    try:
        # Search across SELECTED queries and deduplicate results
        all_results = []
        seen_urls = set()

        print(f"\nSearching {len(selected_queries)} selected queries...")
        print(f"AI Enhancement: {ai_enhancement}")

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
                        "query": query  # Track which query found this
                    })

        print(f"\nFound {len(all_results)} unique results before AI filtering")

        # Apply AI quality filtering if enabled
        if ai_enhancement in ['quality', 'premium']:
            from research_to_pdf import filter_results_by_quality
            print(f"\n🤖 Applying AI quality filtering...")
            print(f"   Min score: {min_quality_score}")
            print(f"   Max to score: {max_to_score}")
            print(f"   This will take ~{max_to_score * 2} seconds...")
            all_results = filter_results_by_quality(topic, all_results, min_score=min_quality_score, max_to_score=max_to_score)
            print(f"✓ Filtered to {len(all_results)} results")

        # Limit to configured max sources
        urls = all_results[:max_sources]

        # Highlight preferred sources
        user_id = get_user_id()
        urls = ai.highlight_preferred_sources(user_id, urls)

        # Save sources to database
        if session_id:
            db.save_sources(session_id, urls)
            print(f"✓ Saved {len(urls)} sources to database")

        # Apply AI query refinement if Premium mode
        if ai_enhancement == 'premium' and len(urls) > 0:
            from research_to_pdf import refine_queries_from_results
            print(f"\n🤖 Generating refined queries based on initial results...")
            refined_queries = refine_queries_from_results(topic, selected_queries, urls)
            if refined_queries:
                print(f"✓ Generated {len(refined_queries)} refined queries")
                session['refined_queries'] = refined_queries

        session['urls'] = urls

        # Count preferred sources
        preferred_count = sum(1 for u in urls if u.get('is_preferred'))
        rejected_count = sum(1 for u in urls if u.get('is_rejected'))

        # Get coaching tips
        coaching_tips = ai.get_ai_coaching(user_id, 'sources')

        content = f'''
        <h2>Step 3: Select Sources</h2>
        <p><strong>Topic:</strong> {topic}</p>
        <p><strong>Searched:</strong> {len(selected_queries)} queries</p>
        <p>Found <strong>{len(urls)}</strong> unique sources. Select which ones to include:</p>

        {f'''
        <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50;">
            <strong>⭐ {preferred_count} sources from your preferred domains!</strong>
            <p style="margin: 5px 0 0 0; font-size: 14px;">These sources are highlighted based on your selection history.</p>
        </div>''' if preferred_count > 0 else ''}

        {f'''
        <div style="background: #ffebee; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f44336;">
            <strong>⚠️ {rejected_count} sources from domains you typically skip</strong>
            <p style="margin: 5px 0 0 0; font-size: 14px;">You usually don't select these - consider reviewing carefully.</p>
        </div>''' if rejected_count > 0 else ''}

        <!-- AI Tips -->
        <div style="background: #fff3cd; padding: 12px 15px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #ffc107;">
            <strong>🤖 Source Selection Tips:</strong>
            <ul style="margin: 8px 0 0 0; padding-left: 20px; font-size: 14px;">
                {chr(10).join([f'<li>{tip}</li>' for tip in coaching_tips])}
            </ul>
        </div>

        <div style="margin: 20px 0;">
            <button type="button" class="secondary" onclick="selectAll(true)">✓ Select All</button>
            <button type="button" class="secondary" onclick="selectAll(false)">✗ Deselect All</button>
        </div>

        <form method="POST" action="/generate_pdf">
        '''

        for i, url_data in enumerate(urls):
            title = url_data['title']
            url = url_data['url']
            query_source = url_data.get('query', 'Unknown')
            relevance_score = url_data.get('relevance_score')
            score_reasoning = url_data.get('score_reasoning', '')
            is_preferred = url_data.get('is_preferred', False)
            is_rejected = url_data.get('is_rejected', False)
            preference_note = url_data.get('preference_note', '')

            # Pre-select preferred sources, or first 10
            checked = 'checked' if (is_preferred or (i < 10 and not is_rejected)) else ''

            # Truncate long query for display
            query_display = query_source if len(query_source) <= 60 else query_source[:57] + "..."

            # Add preference visual indicator
            border_color = '#4caf50' if is_preferred else ('#f44336' if is_rejected else '#ddd')
            bg_color = '#f1f8f4' if is_preferred else ('#fff5f5' if is_rejected else '#fff')

            # Build score display if AI scoring was used
            score_html = ''
            if relevance_score is not None:
                # Color based on score
                if relevance_score >= 80:
                    score_color = '#4caf50'  # Green
                    score_badge = '🟢'
                elif relevance_score >= 70:
                    score_color = '#8bc34a'  # Light green
                    score_badge = '🟢'
                elif relevance_score >= 60:
                    score_color = '#ffc107'  # Yellow
                    score_badge = '🟡'
                else:
                    score_color = '#ff9800'  # Orange
                    score_badge = '🟠'

                score_html = f'''
                <div style="margin-top: 8px; padding: 8px; background: #f5f5f5; border-radius: 4px; font-size: 12px;">
                    <strong style="color: {score_color};">{score_badge} AI Quality Score: {relevance_score}/100</strong>
                    <div style="color: #666; margin-top: 4px; font-style: italic;">{score_reasoning}</div>
                </div>'''

            content += f'''
            <div class="url-item" style="background: {bg_color}; border-left: 4px solid {border_color};">
                {f'<div style="background: {border_color}; color: white; padding: 6px 12px; margin: -15px -15px 10px -15px; font-size: 13px; font-weight: 600;">{preference_note}</div>' if preference_note else ''}
                <div style="display: flex; align-items: start; gap: 10px;">
                    <input type="checkbox" class="url-checkbox" name="selected_urls" value="{url}" {checked}
                           style="margin-top: 5px; transform: scale(1.3); cursor: pointer;">
                    <div style="flex: 1;">
                        <div class="url-title" style="font-weight: 600; margin-bottom: 5px;">{title}</div>
                        <div style="margin-bottom: 5px;">
                            <a href="{url}" target="_blank" rel="noopener noreferrer"
                               style="color: #007bff; text-decoration: none; font-size: 13px;"
                               onclick="event.stopPropagation();">
                                🔗 {url}
                                <span style="font-size: 11px; color: #666;"> (opens in new tab)</span>
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

        content += '''
        <div style="margin-top: 20px;">
            <button type="submit">Generate PDF →</button>
            <button type="button" class="secondary" onclick="window.location.href='/'">← Start Over</button>
        </div>
        </form>

        <!-- Cancel Session Button -->
        <form method="POST" action="/cancel_session" style="margin-top: 10px;">
            <button type="submit" class="secondary" style="background: #dc3545; border-color: #dc3545;"
                    onclick="return confirm('Cancel this research session? Your preferences will be saved, but no PDF will be generated.')">
                🚫 Cancel Session (Don't Generate PDF)
            </button>
            <small style="display: block; margin-top: 8px; color: #666; font-size: 12px;">
                Cancelling will save your source preferences for learning, but won't create a PDF.
            </small>
        </form>
        '''

        return render_template_string(HTML_TEMPLATE, content=content)

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\n{'='*60}")
        print("ERROR IN SEARCH ROUTE")
        print(f"{'='*60}")
        print(error_details)
        print(f"{'='*60}\n")

        content = f'''
        <div class="error">
            <h3>Error searching:</h3>
            <p>{str(e)}</p>
            <details>
                <summary>Technical Details</summary>
                <pre style="background: #f5f5f5; padding: 10px; overflow: auto;">{error_details}</pre>
            </details>
        </div>
        <button onclick="window.location.href='/'">← Back</button>
        '''
        return render_template_string(HTML_TEMPLATE, content=content)

@app.route('/generate_pdf', methods=['POST'])
def generate():
    topic = session.get('topic', 'research')
    selected_urls = request.form.getlist('selected_urls')

    if not selected_urls:
        content = '''
        <div class="error">No URLs selected. Please select at least one source.</div>
        <button onclick="window.history.back()">← Back</button>
        '''
        return render_template_string(HTML_TEMPLATE, content=content)

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

    session['selected_urls'] = selected_urls

    return render_template_string(HTML_TEMPLATE, content=content)

@app.route('/generate_pdf_process')
def generate_process():
    topic = session.get('topic', 'research')
    selected_urls = session.get('selected_urls', [])
    session_id = session.get('session_id')

    if not selected_urls:
        return index()

    # Update database with final selected URLs
    if session_id:
        all_urls = session.get('urls', [])
        db.save_sources(session_id, all_urls, selected_urls)
        print(f"✓ Updated source selections in database ({len(selected_urls)} selected)")

        # Track source preferences in mem0
        user_id = get_user_id()
        for url_data in all_urls:
            if url_data['url'] in selected_urls:
                mem.add_source_preference(user_id, url_data, "selected", topic)
            # Optionally track rejected sources (commented out to reduce noise)
            # else:
            #     mem.add_source_preference(user_id, url_data, "rejected", topic)

    try:
        sources = []
        for url in selected_urls:
            content_html = fetch_and_clean(url)
            if content_html:
                sources.append((url, content_html))

        if not sources:
            content = '''
            <div class="error">No content could be fetched. Please try different sources.</div>
            <button onclick="window.location.href='/'">← Start Over</button>
            '''
            return render_template_string(HTML_TEMPLATE, content=content)

        # Build PDF
        html_doc = build_html_document(topic, sources)
        safe_topic = "".join(c for c in topic if c.isalnum() or c in (" ", "_", "-")).strip()
        if not safe_topic:
            safe_topic = "research"
        output_pdf = f"{safe_topic.replace(' ', '_')}.pdf"

        html_to_pdf(html_doc, output_pdf)

        # Mark session as completed in database
        if session_id:
            db.mark_session_complete(session_id)
            print(f"✓ Marked session {session_id} as complete")

            # Add to mem0 memory
            user_id = get_user_id()
            mem.add_research_memory(
                user_id=user_id,
                session_data={
                    'session_id': session_id,
                    'topic': topic,
                    'date': datetime.now().isoformat(),
                    'ai_mode': session.get('ai_enhancement', 'basic'),
                    'query_focus': session.get('query_focus', 'balanced'),
                    'num_queries': session.get('num_queries', 0),
                    'total_sources': len(session.get('urls', [])),
                    'selected_sources': len(sources),
                    'top_queries': session.get('selected_queries', [])[:3],
                    'min_quality_score': session.get('min_quality_score', 60)
                }
            )

        session['pdf_path'] = output_pdf
        session['source_count'] = len(sources)

        # Get personalized completion insights
        user_id = get_user_id()
        completion_insights = ai.generate_personalized_summary(user_id, {
            'topic': topic,
            'selected_sources': len(sources),
            'total_sources': len(session.get('urls', []))
        })
        next_research = ai.suggest_next_research(user_id)
        coaching_tips = ai.get_ai_coaching(user_id, 'complete')

        content = f'''
        <h2>✅ Success!</h2>

        <div class="success">
            Your research PDF has been generated successfully!
        </div>

        <p><strong>Topic:</strong> {topic}</p>
        <p><strong>Sources included:</strong> {len(sources)}</p>
        <p><strong>Filename:</strong> <code>{output_pdf}</code></p>

        <!-- Personalized Insights -->
        {'''
        <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2196f3;">
            <strong>📊 Your Research Insights:</strong>
            <ul style="margin: 8px 0 0 0; padding-left: 20px; font-size: 14px;">''' +
            chr(10).join([f'<li>{insight}</li>' for insight in completion_insights]) +
            '''
            </ul>
        </div>''' if completion_insights else ''
        }

        <!-- Next Research Suggestion -->
        {f'''
        <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50;">
            <strong>🎯 Suggested Next Research:</strong>
            <p style="margin: 8px 0 0 0; font-size: 14px;">{next_research}</p>
            <button type="button" class="secondary" style="margin-top: 10px; background: #4caf50;"
                    onclick="window.location.href='/?suggested={next_research.replace("'", "\\'")}'"
>
                Start this research →
            </button>
        </div>''' if next_research else ''}

        <!-- AI Tips -->
        <div style="background: #fff3cd; padding: 12px 15px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #ffc107;">
            <strong>🤖 What's Next:</strong>
            <ul style="margin: 8px 0 0 0; padding-left: 20px; font-size: 14px;">
                {chr(10).join([f'<li>{tip}</li>' for tip in coaching_tips])}
            </ul>
        </div>

        <div style="margin: 20px 0;">
            <button onclick="window.location.href='/download'">📥 Download PDF</button>
            <button class="secondary" onclick="window.location.href='/'">🔄 Research Another Topic</button>
        </div>

        <div class="next-steps">
            <h3>Next Steps:</h3>
            <ul>
                <li><strong>Upload to NotebookLM:</strong> Go to <a href="https://notebooklm.google.com" target="_blank">notebooklm.google.com</a> and upload your PDF</li>
                <li><strong>Generate audio summaries:</strong> Let NotebookLM create podcast-style explanations</li>
                <li><strong>Ask questions:</strong> Chat with your research content</li>
                <li><strong>Create study guides:</strong> Generate notes and flashcards</li>
            </ul>
        </div>
        '''

        return render_template_string(HTML_TEMPLATE, content=content)

    except Exception as e:
        content = f'''
        <div class="error">Error generating PDF: {str(e)}</div>
        <button onclick="window.location.href='/'">← Start Over</button>
        '''
        return render_template_string(HTML_TEMPLATE, content=content)

@app.route('/cancel_session', methods=['POST'])
def cancel_session_route():
    """Cancel current session and save preferences without generating PDF"""
    # Check if cancelling from session details page (historical session)
    session_id_from_form = request.form.get('session_id_to_cancel')

    if session_id_from_form:
        # Cancelling from session details page
        session_id = int(session_id_from_form)
        # Get topic from database
        sess = db.get_session_details(session_id)
        topic = sess.get('topic', 'Unknown')
        user_id = get_user_id()

        # Mark session as cancelled (incomplete)
        db.cancel_session(session_id)
        print(f"✓ Session {session_id} cancelled by user (from history)")

        # Don't clear Flask session since we're not in an active session
    else:
        # Cancelling from active session
        session_id = session.get('session_id')
        topic = session.get('topic', 'Unknown')
        user_id = get_user_id()

        if session_id:
            # Save any selected sources as preferences (even if cancelled)
            urls = session.get('urls', [])
            if urls:
                # Track which sources user was considering
                # (They may have checked some boxes before cancelling)
                for url_data in urls:
                    # Only save if it's a preferred domain (already highlighted)
                    if url_data.get('is_preferred'):
                        mem.add_source_preference(user_id, url_data, "considered", topic)

            # Mark session as cancelled (incomplete)
            db.cancel_session(session_id)
            print(f"✓ Session {session_id} cancelled by user")

        # Clear session data
        session.clear()
        session['user_id'] = user_id  # Keep user_id

    # Show cancellation message
    content = f'''
    <h2>🚫 Session Cancelled</h2>

    <div style="background: #fff3cd; padding: 20px; border-radius: 8px; border-left: 4px solid #ffc107; margin: 20px 0;">
        <strong>Session closed without generating PDF</strong>
        <p style="margin: 10px 0 0 0;">Topic: {topic}</p>
    </div>

    <div class="info">
        <strong>What was saved:</strong>
        <ul>
            <li>Your search queries (for learning patterns)</li>
            <li>Sources found (for preference tracking)</li>
            <li>Your interaction data (to improve suggestions)</li>
        </ul>
        <strong>What was NOT saved:</strong>
        <ul>
            <li>No PDF was generated</li>
            <li>Session marked as incomplete</li>
        </ul>
    </div>

    <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50;">
        <strong>💡 Why save the data?</strong>
        <p style="margin: 5px 0 0 0; font-size: 14px;">
            Even cancelled sessions help the AI learn your preferences! This data helps:
        </p>
        <ul style="margin: 8px 0 0 0; font-size: 14px;">
            <li>Improve topic suggestions</li>
            <li>Better highlight preferred sources</li>
            <li>Understand your research interests</li>
        </ul>
    </div>

    <div style="margin: 30px 0;">
        <button onclick="window.location.href='/'">🏠 Start New Research</button>
        <button class="secondary" onclick="window.location.href='/history'">📜 View History</button>
        <button class="secondary" onclick="window.location.href='/analytics'">📊 View Analytics</button>
    </div>

    <div class="info" style="margin-top: 30px;">
        <strong>💡 Tip:</strong> Cancelled sessions appear in your history as "In Progress" so you can review the queries and sources later if needed.
    </div>
    '''

    return render_template_string(HTML_TEMPLATE, content=content)

@app.route('/download')
def download():
    # Get PDF filename from URL parameter or session (fallback)
    pdf_filename = request.args.get('file') or session.get('pdf_path')

    if not pdf_filename:
        return "PDF filename not specified. Please generate a new one.", 404

    # Security: Only allow filenames, not paths
    pdf_filename = os.path.basename(pdf_filename)

    if pdf_filename and os.path.exists(pdf_filename):
        return send_file(pdf_filename, as_attachment=True)
    else:
        return f"PDF file '{pdf_filename}' not found. Please generate a new one.", 404

@app.route('/history')
def history():
    """View recent research sessions"""
    sessions = db.get_recent_sessions(limit=20)

    content = '''
    <h2>📜 Research History</h2>
    <p>View your past research sessions and their results.</p>

    <div style="margin: 20px 0;">
        <button onclick="window.location.href='/'">← Back to Home</button>
        <button class="secondary" onclick="window.location.href='/analytics'">📊 View Analytics</button>
    </div>
    '''

    if not sessions:
        content += '''
        <div class="info">
            <p>No research sessions found. Start a new research session to build your history!</p>
        </div>
        '''
    else:
        content += f'''
        <div style="margin: 20px 0;">
            <p><strong>{len(sessions)}</strong> recent sessions:</p>
        </div>
        '''

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

            # Determine status badge and color
            if cancelled:
                status_badge = '🚫 Cancelled'
                status_color = '#dc3545'
            elif completed:
                status_badge = '✅ Complete'
                status_color = '#28a745'
            else:
                status_badge = '⏸️ In Progress'
                status_color = '#ffc107'

            content += f'''
            <div class="url-item" style="cursor: pointer; border-left: 4px solid {status_color};"
                 onclick="window.location.href='/session/{session_id}'">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <div class="url-title" style="font-size: 18px; margin-bottom: 8px;">
                            {topic}
                        </div>
                        <div style="font-size: 13px; color: #666; margin-bottom: 8px;">
                            📅 {date} | 🤖 {ai_mode} mode
                        </div>
                        <div style="font-size: 13px; color: #666;">
                            📝 {query_count} queries | 🔗 {source_count} sources | ✓ {selected_count} selected
                        </div>
                    </div>
                    <div style="background: {status_color}; color: white; padding: 5px 12px; border-radius: 4px; font-size: 12px; font-weight: 600;">
                        {status_badge}
                    </div>
                </div>
            </div>
            '''

    content += '''
    <div style="margin-top: 20px;">
        <button onclick="window.location.href='/'">← Back to Home</button>
    </div>
    '''

    return render_template_string(HTML_TEMPLATE, content=content)

@app.route('/session/<int:session_id>')
def view_session(session_id):
    """View details of a specific research session"""
    try:
        sess = db.get_session_details(session_id)
    except:
        content = '''
        <div class="error">Session not found.</div>
        <button onclick="window.location.href='/history'">← Back to History</button>
        '''
        return render_template_string(HTML_TEMPLATE, content=content)

    topic = sess['topic']
    date = sess['date']
    ai_mode = sess.get('ai_mode', 'N/A')
    query_focus = sess.get('query_focus', 'N/A')
    min_quality_score = sess.get('min_quality_score', 'N/A')
    completed = sess['completed']
    cancelled = sess.get('cancelled', 0)
    queries = sess.get('queries', [])
    sources = sess.get('sources', [])

    # Determine status badge
    if cancelled:
        status_badge = '🚫 Cancelled'
    elif completed:
        status_badge = '✅ Complete'
    else:
        status_badge = '⏸️ In Progress'

    # Add cancel button for in-progress sessions (not completed and not cancelled)
    cancel_button_html = ''
    if not completed and not cancelled:
        cancel_button_html = f'''
        <form method="POST" action="/cancel_session" style="display: inline;">
            <input type="hidden" name="session_id_to_cancel" value="{session_id}">
            <button type="submit" class="secondary" style="background: #dc3545; border-color: #dc3545;"
                    onclick="return confirm('Cancel this session? It will be marked as incomplete.')">
                🚫 Cancel Session
            </button>
        </form>
        '''

    content = f'''
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h2 style="margin: 0;">📋 Session Details</h2>
        <div>{cancel_button_html}</div>
    </div>

    <div style="margin: 20px 0;">
        <button onclick="window.location.href='/history'">← Back to History</button>
        <button class="secondary" onclick="window.location.href='/'">🏠 Home</button>
    </div>

    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin-top: 0;">{topic}</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 14px;">
            <div><strong>Date:</strong> {date}</div>
            <div><strong>Status:</strong> {status_badge}</div>
            <div><strong>AI Mode:</strong> {ai_mode}</div>
            <div><strong>Query Focus:</strong> {query_focus}</div>
            <div><strong>Min Quality Score:</strong> {min_quality_score}</div>
            <div><strong>Session ID:</strong> #{session_id}</div>
        </div>
    </div>

    <h3>Generated Queries ({len(queries)})</h3>
    '''

    if queries:
        selected_queries = [q for q in queries if q.get('selected')]
        content += f'<p><strong>{len(selected_queries)}</strong> of {len(queries)} queries were used.</p>'

        for query in queries:
            query_text = query['query_text']
            selected = query.get('selected', 0)
            badge = '✓' if selected else '○'
            badge_color = '#28a745' if selected else '#ccc'

            content += f'''
            <div class="query-item" style="border-left-color: {badge_color};">
                <strong style="color: {badge_color};">{badge}</strong> {query_text}
            </div>
            '''
    else:
        content += '<p>No queries found.</p>'

    content += f'''
    <h3>Sources Found ({len(sources)})</h3>
    '''

    if sources:
        selected_sources = [s for s in sources if s.get('selected')]
        content += f'<p><strong>{len(selected_sources)}</strong> of {len(sources)} sources were included in PDF.</p>'

        for source in sources:
            url = source['url']
            title = source.get('title', 'No title')
            query_source = source.get('query_source', 'Unknown')
            ai_score = source.get('ai_score')
            score_reasoning = source.get('score_reasoning', '')
            selected = source.get('selected', 0)

            badge_color = '#28a745' if selected else '#e0e0e0'

            # Build score display if available
            score_html = ''
            if ai_score is not None:
                if ai_score >= 80:
                    score_color = '#4caf50'
                    score_badge = '🟢'
                elif ai_score >= 70:
                    score_color = '#8bc34a'
                    score_badge = '🟢'
                elif ai_score >= 60:
                    score_color = '#ffc107'
                    score_badge = '🟡'
                else:
                    score_color = '#ff9800'
                    score_badge = '🟠'

                score_html = f'''
                <div style="margin-top: 8px; padding: 8px; background: #f5f5f5; border-radius: 4px; font-size: 12px;">
                    <strong style="color: {score_color};">{score_badge} AI Quality Score: {ai_score}/100</strong>
                    {f'<div style="color: #666; margin-top: 4px; font-style: italic;">{score_reasoning}</div>' if score_reasoning else ''}
                </div>'''

            content += f'''
            <div class="url-item" style="border-left: 4px solid {badge_color};">
                <div class="url-title">{title}</div>
                <div style="margin: 5px 0;">
                    <a href="{url}" target="_blank" rel="noopener noreferrer"
                       style="color: #007bff; text-decoration: none; font-size: 13px;">
                        🔗 {url}
                    </a>
                </div>
                <div style="font-size: 11px; color: #888;">
                    Found by: {query_source[:60]}{'...' if len(query_source) > 60 else ''}
                </div>
                {score_html}
            </div>
            '''
    else:
        content += '<p>No sources found.</p>'

    content += '''
    <div style="margin-top: 20px;">
        <button onclick="window.location.href='/history'">← Back to History</button>
    </div>
    '''

    return render_template_string(HTML_TEMPLATE, content=content)

@app.route('/mem0-monitor')
def mem0_monitor():
    """Mem0 usage monitoring dashboard"""
    user_id = get_user_id()

    # Get statistics
    total_stats = mem.get_total_stats()
    recent_ops = mem.get_recent_operations(limit=20)
    cost_breakdown = mem.get_cost_breakdown()
    usage_stats = mem.get_usage_stats(days=7)

    content = f'''
    <h2>🧠 Mem0 Memory System Monitor</h2>

    <div style="margin: 20px 0;">
        <button onclick="window.location.href='/history'">← Back to History</button>
        <button class="secondary" onclick="window.location.href='/mem0-context'">📝 Manage Context</button>
        <button class="secondary" onclick="window.location.href='/mem0-memories'">💭 View Memories</button>
        <button class="secondary" onclick="window.location.href='/mem0-preferences'">⭐ My Preferences</button>
        <button class="secondary" onclick="location.reload()">🔄 Refresh</button>
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
        <div style="background: #fff3e0; padding: 15px; border-radius: 8px; text-align: center;">
            <div style="font-size: 32px; font-weight: 600; color: #f57c00;">{total_stats['total_searches']}</div>
            <div style="color: #666; font-size: 13px;">Searches</div>
        </div>
        <div style="background: #fce4ec; padding: 15px; border-radius: 8px; text-align: center;">
            <div style="font-size: 32px; font-weight: 600; color: #c2185b;">${total_stats['total_cost']:.4f}</div>
            <div style="color: #666; font-size: 13px;">Total Cost</div>
        </div>
        <div style="background: #f3e5f5; padding: 15px; border-radius: 8px; text-align: center;">
            <div style="font-size: 32px; font-weight: 600; color: #7b1fa2;">{int(total_stats['avg_latency_ms'])}ms</div>
            <div style="color: #666; font-size: 13px;">Avg Latency</div>
        </div>
        <div style="background: #e0f2f1; padding: 15px; border-radius: 8px; text-align: center;">
            <div style="font-size: 32px; font-weight: 600; color: #00796b;">{total_stats['success_rate']:.1f}%</div>
            <div style="color: #666; font-size: 13px;">Success Rate</div>
        </div>
    </div>

    <h3>Cost Breakdown by Operation</h3>
    <div style="margin: 20px 0;">
    '''

    for item in cost_breakdown:
        percentage = (item['count'] / total_stats['total_operations'] * 100) if total_stats['total_operations'] > 0 else 0
        content += f'''
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
            <div style="font-size: 12px; color: #888; margin-top: 4px;">
                Embedding: {item['embedding_tokens']:,} tokens | LLM: {item['llm_tokens']:,} tokens
            </div>
        </div>
        '''

    content += '''
    </div>

    <h3>Recent Operations (Last 20)</h3>
    <div style="margin: 20px 0;">
    '''

    for op in recent_ops:
        success_badge = '✅' if op['success'] else '❌'
        bg_color = '#f8f9fa' if op['success'] else '#ffebee'

        metadata = json.loads(op['metadata']) if op['metadata'] else {}
        meta_display = ''
        if 'topic' in metadata:
            meta_display = f"Topic: {metadata['topic'][:50]}"
        elif 'query' in metadata:
            meta_display = f"Query: {metadata['query'][:50]}"

        content += f'''
        <div style="background: {bg_color}; padding: 10px; margin: 6px 0; border-radius: 4px; font-size: 13px;">
            <div style="display: flex; justify-content: space-between;">
                <div>
                    {success_badge} <strong>{op['operation_type'].upper()}</strong>
                    {f'<span style="color: #888; margin-left: 10px;">{meta_display}</span>' if meta_display else ''}
                </div>
                <div style="color: #666;">
                    {op['timestamp']} | {op['latency_ms']}ms | ${op['estimated_cost']:.5f}
                </div>
            </div>
        </div>
        '''

    content += '''
    </div>

    <h3>7-Day Usage Trend</h3>
    <div style="margin: 20px 0;">
    '''

    if usage_stats:
        for day in usage_stats:
            content += f'''
            <div style="background: #f8f9fa; padding: 12px; margin: 8px 0; border-radius: 4px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div><strong>{day['date']}</strong></div>
                    <div style="font-size: 13px;">
                        {day['operations'] or 0} ops |
                        {day['memories'] or 0} memories |
                        {day['searches'] or 0} searches |
                        ${day['cost'] or 0:.4f} |
                        {int(day['latency_ms'] or 0)}ms avg
                    </div>
                </div>
            </div>
            '''
    else:
        content += '<p>No usage data available yet.</p>'

    content += '''
    </div>

    <div class="info" style="margin-top: 30px;">
        <strong>💡 About Mem0 Monitoring:</strong>
        <ul style="margin: 10px 0; padding-left: 20px;">
            <li><strong>Operations:</strong> Every time mem0 adds a memory or searches, it's tracked here</li>
            <li><strong>Cost Tracking:</strong> Accurate cost estimation based on OpenAI API pricing</li>
            <li><strong>Tokens:</strong> Embedding tokens (text-embedding-3-small @ $0.02/1M) + LLM tokens (gpt-4o-mini @ $0.15/1M)</li>
            <li><strong>Latency:</strong> Time taken for each mem0 operation in milliseconds</li>
            <li><strong>Success Rate:</strong> Percentage of operations that completed without errors</li>
        </ul>
    </div>

    <div style="margin-top: 20px;">
        <button onclick="window.location.href='/history'">← Back to History</button>
    </div>
    '''

    return render_template_string(HTML_TEMPLATE, content=content)

@app.route('/mem0-context', methods=['GET', 'POST'])
def mem0_context():
    """Persistent context management interface"""
    user_id = get_user_id()

    message = ""

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_context':
            context_text = request.form.get('context_text', '').strip()
            context_type = request.form.get('context_type', 'general')

            if context_text:
                context_id = mem.add_persistent_context(user_id, context_text, context_type)
                if context_id:
                    message = f'<div class="success">✓ Persistent context added successfully!</div>'
                else:
                    message = f'<div class="error">✗ Failed to add persistent context.</div>'
            else:
                message = f'<div class="error">✗ Context text cannot be empty.</div>'

        elif action == 'remove_context':
            context_id = request.form.get('context_id')
            if context_id:
                success = mem.remove_persistent_context(user_id, int(context_id))
                if success:
                    message = f'<div class="success">✓ Context removed successfully!</div>'
                else:
                    message = f'<div class="error">✗ Failed to remove context.</div>'

        elif action == 'clear_all':
            count = mem.clear_all_persistent_contexts(user_id)
            message = f'<div class="success">✓ Cleared {count} persistent contexts.</div>'

        elif action == 'add_memory':
            memory_text = request.form.get('memory_text', '').strip()
            memory_type = request.form.get('memory_type', 'manual')

            if memory_text:
                result = mem.add_manual_memory(user_id, memory_text, memory_type)
                if result:
                    message = f'<div class="success">✓ Manual memory added successfully!</div>'
                else:
                    message = f'<div class="error">✗ Failed to add manual memory.</div>'
            else:
                message = f'<div class="error">✗ Memory text cannot be empty.</div>'

    # Get current persistent contexts
    contexts = mem.get_persistent_contexts(user_id)

    content = f'''
    <h2>📝 Persistent Context Management</h2>
    <p>Manage persistent contexts that will be automatically injected into all AI query generations.</p>

    <div style="margin: 20px 0;">
        <button onclick="window.location.href='/mem0-monitor'">← Back to Monitor</button>
        <button class="secondary" onclick="window.location.href='/mem0-memories'">💭 View Memories</button>
    </div>

    {message}

    <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2196f3;">
        <h3 style="margin-top: 0;">ℹ️ What is Persistent Context?</h3>
        <p>Persistent contexts are pieces of information that will be included in <strong>every AI query generation</strong>. This allows you to:</p>
        <ul>
            <li><strong>Set preferences:</strong> "I prefer academic papers over blog posts"</li>
            <li><strong>Define constraints:</strong> "Only search for sources published after 2020"</li>
            <li><strong>Add expertise:</strong> "I'm a PhD researcher in computer science"</li>
            <li><strong>Specify interests:</strong> "Focus on machine learning and deep learning topics"</li>
        </ul>
        <p>These contexts persist across all research sessions until you remove them.</p>
    </div>

    <!-- Current Persistent Contexts -->
    <h3>Current Persistent Contexts ({len(contexts)})</h3>
    '''

    if contexts:
        # Group by type
        context_by_type = {}
        for ctx in contexts:
            ctx_type = ctx['context_type']
            if ctx_type not in context_by_type:
                context_by_type[ctx_type] = []
            context_by_type[ctx_type].append(ctx)

        type_colors = {
            'general': '#90caf9',
            'preference': '#a5d6a7',
            'instruction': '#ffcc80',
            'fact': '#ce93d8',
            'expertise': '#80deea'
        }

        for ctx_type, ctx_list in context_by_type.items():
            color = type_colors.get(ctx_type, '#bdbdbd')
            content += f'''
            <div style="margin: 15px 0;">
                <h4 style="color: #555; text-transform: capitalize;">
                    <span style="background: {color}; padding: 4px 12px; border-radius: 12px; font-size: 13px;">
                        {ctx_type}
                    </span>
                    ({len(ctx_list)})
                </h4>
            '''

            for ctx in ctx_list:
                content += f'''
                <div style="background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 6px; border-left: 4px solid {color};">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="flex: 1; margin-right: 15px;">
                            <div style="font-size: 14px; line-height: 1.5; color: #333;">
                                {ctx['context_text']}
                            </div>
                            <div style="font-size: 12px; color: #888; margin-top: 8px;">
                                Added: {ctx['created_at']}
                            </div>
                        </div>
                        <div>
                            <form method="POST" style="display: inline;">
                                <input type="hidden" name="action" value="remove_context">
                                <input type="hidden" name="context_id" value="{ctx['id']}">
                                <button type="submit" class="secondary" style="padding: 6px 12px; font-size: 13px;"
                                        onclick="return confirm('Remove this context?')">
                                    🗑️ Remove
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
                '''

            content += '</div>'

        # Clear all button
        content += '''
        <div style="margin: 20px 0;">
            <form method="POST" style="display: inline;">
                <input type="hidden" name="action" value="clear_all">
                <button type="submit" class="secondary" style="background: #f44336; color: white;"
                        onclick="return confirm('Remove ALL persistent contexts? This cannot be undone.')">
                    🗑️ Clear All Contexts
                </button>
            </form>
        </div>
        '''
    else:
        content += '''
        <div style="background: #fff3cd; padding: 15px; border-radius: 6px; border-left: 4px solid #ffc107;">
            <p style="margin: 0;">No persistent contexts yet. Add one below to get started!</p>
        </div>
        '''

    # Add context form
    content += '''
    <h3 style="margin-top: 30px;">➕ Add New Persistent Context</h3>
    <form method="POST" style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
        <input type="hidden" name="action" value="add_context">

        <div style="margin-bottom: 15px;">
            <label style="display: block; font-weight: 600; margin-bottom: 5px;">Context Type:</label>
            <select name="context_type" style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;">
                <option value="general">General</option>
                <option value="preference">Preference</option>
                <option value="instruction">Instruction</option>
                <option value="fact">Fact</option>
                <option value="expertise">Expertise</option>
            </select>
            <small style="color: #666;">Choose the type of context you're adding</small>
        </div>

        <div style="margin-bottom: 15px;">
            <label style="display: block; font-weight: 600; margin-bottom: 5px;">Context Text:</label>
            <textarea name="context_text" rows="4"
                      style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px; font-family: inherit;"
                      placeholder="E.g., 'I prefer academic papers and peer-reviewed sources' or 'Focus on recent developments from 2023 onwards'"
                      required></textarea>
            <small style="color: #666;">This will be included in all AI query generations</small>
        </div>

        <button type="submit" style="padding: 12px 24px; background: #4caf50; color: white; border: none; border-radius: 4px; font-size: 15px; font-weight: 600; cursor: pointer;">
            ➕ Add Persistent Context
        </button>
    </form>

    <!-- Manual Memory Addition -->
    <h3 style="margin-top: 40px;">💭 Add Manual Memory</h3>
    <div style="background: #e8f5e9; padding: 15px; border-radius: 6px; border-left: 4px solid #4caf50; margin-bottom: 15px;">
        <p style="margin: 0;"><strong>Note:</strong> Manual memories are added to your mem0 semantic memory store and can be searched/recalled later. Unlike persistent contexts, they are not automatically injected into every query.</p>
    </div>

    <form method="POST" style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
        <input type="hidden" name="action" value="add_memory">

        <div style="margin-bottom: 15px;">
            <label style="display: block; font-weight: 600; margin-bottom: 5px;">Memory Type:</label>
            <select name="memory_type" style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px;">
                <option value="manual">Manual Note</option>
                <option value="fact">Fact</option>
                <option value="insight">Insight</option>
                <option value="reference">Reference</option>
            </select>
        </div>

        <div style="margin-bottom: 15px;">
            <label style="display: block; font-weight: 600; margin-bottom: 5px;">Memory Text:</label>
            <textarea name="memory_text" rows="4"
                      style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px; font-family: inherit;"
                      placeholder="E.g., 'Found excellent paper on transformer architectures at arxiv.org/abs/1706.03762' or 'Machine learning research often uses PyTorch or TensorFlow'"
                      required></textarea>
            <small style="color: #666;">This will be stored in your mem0 memory and can be recalled semantically</small>
        </div>

        <button type="submit" style="padding: 12px 24px; background: #2196f3; color: white; border: none; border-radius: 4px; font-size: 15px; font-weight: 600; cursor: pointer;">
            💾 Add Manual Memory
        </button>
    </form>

    <div style="margin-top: 30px;">
        <button onclick="window.location.href='/mem0-monitor'">← Back to Monitor</button>
    </div>
    '''

    return render_template_string(HTML_TEMPLATE, content=content)

@app.route('/mem0-memories')
def mem0_memories():
    """View all mem0 memories for current user"""
    user_id = get_user_id()
    memories = mem.get_all_memories(user_id, limit=100)

    content = f'''
    <h2>💭 My Research Memories</h2>
    <p>Semantic memories stored by the AI memory system.</p>

    <div style="margin: 20px 0;">
        <button onclick="window.location.href='/mem0-monitor'">← Back to Monitor</button>
        <button class="secondary" onclick="window.location.href='/mem0-preferences'">⭐ View Preferences</button>
    </div>

    <p><strong>Total Memories:</strong> {len(memories)}</p>
    '''

    if not memories:
        content += '''
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

            # Color code by type
            if memory_type == 'research_session':
                color = '#2196f3'
                icon = '📚'
            elif memory_type == 'source_preference':
                color = '#4caf50'
                icon = '⭐'
            else:
                color = '#9e9e9e'
                icon = '💭'

            content += f'''
            <div style="background: white; border-left: 4px solid {color}; padding: 15px; margin: 12px 0; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                    <div style="font-weight: 600; color: {color};">
                        {icon} {memory_type.replace('_', ' ').title()}
                    </div>
                    <div style="font-size: 11px; color: #999;">
                        Memory #{i}
                    </div>
                </div>
                <div style="white-space: pre-wrap; font-size: 13px; line-height: 1.6; color: #333;">
{memory_text}
                </div>
                {f'<div style="margin-top: 10px; font-size: 12px; color: #666;">Topic: {metadata.get("topic", "N/A")}</div>' if metadata.get('topic') else ''}
            </div>
            '''

    content += '''
    <div style="margin-top: 20px;">
        <button onclick="window.location.href='/mem0-monitor'">← Back to Monitor</button>
    </div>
    '''

    return render_template_string(HTML_TEMPLATE, content=content)

@app.route('/mem0-preferences')
def mem0_preferences():
    """View learned user preferences"""
    user_id = get_user_id()
    preferences = mem.get_user_preferences(user_id)

    content = '''
    <h2>⭐ My Research Preferences</h2>
    <p>Learned preferences based on your research history.</p>

    <div style="margin: 20px 0;">
        <button onclick="window.location.href='/mem0-monitor'">← Back to Monitor</button>
        <button class="secondary" onclick="window.location.href='/mem0-memories'">💭 View Memories</button>
    </div>
    '''

    # Preferred domains
    if preferences.get('preferred_domains'):
        content += '''
        <h3>✅ Preferred Source Domains</h3>
        <p>Domains you frequently select from:</p>
        <div style="margin: 20px 0;">
        '''
        for domain, count in preferences['preferred_domains']:
            content += f'''
            <div style="background: #e8f5e9; padding: 10px 15px; margin: 6px 0; border-left: 4px solid #4caf50; border-radius: 4px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>{domain}</strong>
                    <span style="background: #4caf50; color: white; padding: 3px 10px; border-radius: 12px; font-size: 12px;">
                        Selected {count} times
                    </span>
                </div>
            </div>
            '''
        content += '</div>'

    # Rejected domains
    if preferences.get('rejected_domains'):
        content += '''
        <h3>❌ Avoided Source Domains</h3>
        <p>Domains you typically skip:</p>
        <div style="margin: 20px 0;">
        '''
        for domain, count in preferences['rejected_domains']:
            content += f'''
            <div style="background: #ffebee; padding: 10px 15px; margin: 6px 0; border-left: 4px solid #f44336; border-radius: 4px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>{domain}</strong>
                    <span style="background: #f44336; color: white; padding: 3px 10px; border-radius: 12px; font-size: 12px;">
                        Skipped {count} times
                    </span>
                </div>
            </div>
            '''
        content += '</div>'

    # AI modes
    if preferences.get('ai_modes'):
        content += '''
        <h3>🤖 Preferred AI Enhancement Modes</h3>
        <div style="margin: 20px 0;">
        '''
        for mode, count in preferences['ai_modes']:
            content += f'''
            <div style="background: #e3f2fd; padding: 10px 15px; margin: 6px 0; border-left: 4px solid #2196f3; border-radius: 4px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>{mode.title()}</strong>
                    <span style="background: #2196f3; color: white; padding: 3px 10px; border-radius: 12px; font-size: 12px;">
                        Used {count} times
                    </span>
                </div>
            </div>
            '''
        content += '</div>'

    # Topics
    if preferences.get('topics'):
        content += '''
        <h3>📚 Frequently Researched Topics</h3>
        <div style="margin: 20px 0;">
        '''
        for topic, count in preferences['topics']:
            content += f'''
            <div style="background: #fff3e0; padding: 10px 15px; margin: 6px 0; border-left: 4px solid #ff9800; border-radius: 4px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>{topic}</strong>
                    <span style="background: #ff9800; color: white; padding: 3px 10px; border-radius: 12px; font-size: 12px;">
                        {count} sessions
                    </span>
                </div>
            </div>
            '''
        content += '</div>'

    if not any([preferences.get('preferred_domains'), preferences.get('rejected_domains'),
                preferences.get('ai_modes'), preferences.get('topics')]):
        content += '''
        <div class="info">
            <p>No preferences learned yet. Complete more research sessions to build your preference profile!</p>
        </div>
        '''

    content += '''
    <div class="info" style="margin-top: 30px;">
        <strong>💡 How This Works:</strong>
        <ul style="margin: 10px 0; padding-left: 20px;">
            <li>Mem0 tracks which sources you select and which you skip</li>
            <li>It learns your preferred source types, domains, and AI settings</li>
            <li>Future versions will use this to personalize search results</li>
            <li>All learning happens locally on your machine</li>
        </ul>
    </div>

    <div style="margin-top: 20px;">
        <button onclick="window.location.href='/mem0-monitor'">← Back to Monitor</button>
    </div>
    '''

    return render_template_string(HTML_TEMPLATE, content=content)

@app.route('/analytics')
def analytics():
    """View overall research analytics"""
    stats = db.get_research_stats()
    favorite_sources = db.get_favorite_sources(min_selections=2)

    content = '''
    <h2>📊 Research Analytics</h2>

    <div style="margin: 20px 0;">
        <button onclick="window.location.href='/history'">← Back to History</button>
        <button class="secondary" onclick="window.location.href='/'">🏠 Home</button>
    </div>
    '''

    # Overall stats
    total_sessions = stats.get('total_sessions', 0)
    completed_sessions = stats.get('completed_sessions', 0)
    total_sources = stats.get('total_sources', 0)
    selected_sources = stats.get('selected_sources', 0)

    completion_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
    selection_rate = (selected_sources / total_sources * 100) if total_sources > 0 else 0

    content += f'''
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0;">
        <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; text-align: center;">
            <div style="font-size: 36px; font-weight: 600; color: #1976d2;">{total_sessions}</div>
            <div style="color: #666; margin-top: 5px;">Total Sessions</div>
        </div>
        <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; text-align: center;">
            <div style="font-size: 36px; font-weight: 600; color: #388e3c;">{completed_sessions}</div>
            <div style="color: #666; margin-top: 5px;">Completed ({completion_rate:.0f}%)</div>
        </div>
        <div style="background: #fff3e0; padding: 20px; border-radius: 8px; text-align: center;">
            <div style="font-size: 36px; font-weight: 600; color: #f57c00;">{total_sources}</div>
            <div style="color: #666; margin-top: 5px;">Sources Found</div>
        </div>
        <div style="background: #f3e5f5; padding: 20px; border-radius: 8px; text-align: center;">
            <div style="font-size: 36px; font-weight: 600; color: #7b1fa2;">{selected_sources}</div>
            <div style="color: #666; margin-top: 5px;">Sources Used ({selection_rate:.0f}%)</div>
        </div>
    </div>
    '''

    # Top topics
    top_topics = stats.get('top_topics', [])
    if top_topics:
        content += '''
        <h3>Most Researched Topics</h3>
        '''
        for topic_data in top_topics:
            topic = topic_data['topic']
            count = topic_data['count']
            content += f'''
            <div class="query-item">
                <strong>{topic}</strong> <span style="color: #666;">({count} sessions)</span>
            </div>
            '''

    # AI mode usage
    ai_mode_usage = stats.get('ai_mode_usage', [])
    if ai_mode_usage:
        content += '''
        <h3>AI Enhancement Usage</h3>
        '''
        for mode_data in ai_mode_usage:
            mode = mode_data['ai_mode']
            count = mode_data['count']
            content += f'''
            <div class="query-item">
                <strong>{mode}</strong> <span style="color: #666;">({count} sessions)</span>
            </div>
            '''

    # Favorite sources
    if favorite_sources:
        content += f'''
        <h3>Top Sources (Selected Multiple Times)</h3>
        <p>These sources have been selected in multiple research sessions, indicating high quality.</p>
        '''
        for fav in favorite_sources:
            url = fav['url']
            title = fav.get('title', 'No title')
            times_found = fav['times_found']
            times_selected = fav['times_selected']
            avg_score = fav.get('avg_score')

            score_display = f" | Avg AI Score: {avg_score:.0f}/100" if avg_score else ""

            content += f'''
            <div class="url-item">
                <div class="url-title">{title}</div>
                <div style="margin: 5px 0;">
                    <a href="{url}" target="_blank" style="color: #007bff; text-decoration: none;">
                        🔗 {url}
                    </a>
                </div>
                <div style="font-size: 12px; color: #666;">
                    Found {times_found} times | Selected {times_selected} times{score_display}
                </div>
            </div>
            '''

    content += '''
    <div style="margin-top: 20px;">
        <button onclick="window.location.href='/history'">← Back to History</button>
    </div>
    '''

    return render_template_string(HTML_TEMPLATE, content=content)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Research to PDF UI is starting...")
    print("="*60)
    print("\n📱 Open your browser and go to:")
    print("\n    http://localhost:5001")
    print("    or")
    print("    http://127.0.0.1:5001\n")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5001)
