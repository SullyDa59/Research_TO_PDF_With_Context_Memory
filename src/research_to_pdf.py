import os
import textwrap
import requests
from bs4 import BeautifulSoup
from weasyprint import HTML
from openai import OpenAI

# ---------- CONFIG ----------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Set OPENAI_API_KEY env variable first")

client = OpenAI(api_key=OPENAI_API_KEY)

# ---------- SEARCH PROVIDER OPTIONS ----------
# Option 1: Tavily (good for research, has free tier)
# pip install tavily-python
# TAVILY_API_KEY in env
def search_web_tavily(query: str, num_results: int = 10):
    """Search using Tavily API"""
    try:
        from tavily import TavilyClient
        tavily_key = os.environ.get("TAVILY_API_KEY")
        if not tavily_key:
            raise RuntimeError("Set TAVILY_API_KEY env variable")

        tavily = TavilyClient(api_key=tavily_key)
        response = tavily.search(query=query, max_results=num_results)

        results = []
        for item in response.get('results', []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", "")
            })
        return results
    except ImportError:
        raise RuntimeError("Install tavily-python: pip install tavily-python")


# Option 2: SerpAPI (Google results, paid but reliable)
# pip install google-search-results
# SERPAPI_API_KEY in env
def search_web_serpapi(query: str, num_results: int = 10):
    """Search using SerpAPI"""
    try:
        from serpapi import GoogleSearch
        serpapi_key = os.environ.get("SERPAPI_API_KEY")
        if not serpapi_key:
            raise RuntimeError("Set SERPAPI_API_KEY env variable")

        params = {
            "q": query,
            "api_key": serpapi_key,
            "num": num_results
        }
        search = GoogleSearch(params)
        results_data = search.get_dict()

        results = []
        for item in results_data.get("organic_results", [])[:num_results]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", "")
            })
        return results
    except ImportError:
        raise RuntimeError("Install google-search-results: pip install google-search-results")


# Option 3: DuckDuckGo (free, no API key needed)
# pip install duckduckgo-search
def search_web_duckduckgo(query: str, num_results: int = 10):
    """Search using DuckDuckGo (free, no API key)"""
    try:
        from ddgs import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=num_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", "")
                })
        return results
    except ImportError:
        raise RuntimeError("Install ddgs: pip install ddgs")


# Choose your search provider here
def search_web(query: str, num_results: int = 10):
    """
    Main search function - change this to use your preferred provider

    Uncomment one of these:
    """
    return search_web_duckduckgo(query, num_results)  # Free, no API key
    # return search_web_tavily(query, num_results)      # Good for research
    # return search_web_serpapi(query, num_results)     # Most reliable, paid

    # raise NotImplementedError(
    #     "Choose a search provider by uncommenting one of the options above in search_web()"
    # )


def generate_search_queries(topic: str, num_queries: int = 3):
    """
    Use OpenAI to generate a few good search queries for the topic.
    Enhanced to produce more diverse and targeted queries.
    """
    prompt = f"""You are helping to research a topic for deep study and comprehensive understanding.

Topic: {topic}

Generate {num_queries} diverse, high-quality web search queries that cover different aspects of this topic.

Your queries should include a mix of:
1. Academic/scholarly sources (research papers, academic journals, educational institutions)
2. Practical guides and tutorials (how-to guides, implementation examples)
3. Recent developments and news (latest trends, recent breakthroughs, 2024-2025 updates)
4. Comprehensive overviews (definitive guides, complete introductions, foundational knowledge)
5. Expert analysis and opinions (thought leaders, industry experts, detailed analysis)
6. Technical documentation (official docs, technical specifications, API references)
7. Real-world applications and case studies (use cases, success stories, practical examples)

Each query should be:
- Specific and targeted to find authoritative sources
- Optimized for search engines (natural language but focused)
- Likely to return in-depth, long-form content
- Diverse enough to cover different facets of the topic

Output exactly {num_queries} search queries, one per line, with NO bullets, numbers, or extra formatting.
Just the raw search query text on each line."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert research assistant specializing in generating highly effective, diverse search queries that retrieve comprehensive information from multiple authoritative sources across academic, practical, and industry domains."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,  # Increased for more diverse queries
        max_tokens=500
    )

    text = response.choices[0].message.content
    # Split into lines, strip empties, remove any numbering/bullets
    queries = []
    for line in text.split("\n"):
        line = line.strip()
        # Remove common prefixes like "1.", "- ", etc.
        import re
        line = re.sub(r'^\d+[\.\)]\s*', '', line)  # Remove "1. " or "1) "
        line = re.sub(r'^[-•*]\s*', '', line)       # Remove "- " or "• "
        if line:
            queries.append(line)

    return queries[:num_queries]


def generate_search_queries_advanced(topic: str, num_queries: int = 7, focus: str = "balanced"):
    """
    Advanced version with customizable focus for different research needs.

    Args:
        topic: Research topic
        num_queries: Number of queries to generate
        focus: Type of sources to prioritize (balanced, academic, practical, recent, technical, comprehensive)
    """
    focus_instructions = {
        "balanced": """Generate a balanced mix covering:
- Academic research and scholarly articles
- Practical guides and tutorials
- Recent developments (2024-2025)
- Comprehensive overviews
- Technical documentation
- Expert analysis
- Real-world applications""",

        "academic": """Focus heavily on academic and scholarly sources:
- Research papers and peer-reviewed journals
- University publications and educational resources
- Academic databases and repositories
- Scholarly analysis and literature reviews
- Scientific studies and experiments
- Academic conferences and symposiums
Use terms like: research, study, paper, journal, academic, scholarly, analysis""",

        "practical": """Focus on practical, hands-on resources:
- Step-by-step tutorials and how-to guides
- Implementation examples and code samples
- Best practices and practical tips
- Beginner-friendly introductions
- Real-world applications and use cases
- Developer guides and workshops
Use terms like: tutorial, guide, how to, example, implementation, practical, hands-on""",

        "recent": """Focus on the latest information and recent developments:
- News and updates from 2024-2025
- Latest trends and breakthroughs
- Recent announcements and releases
- Current state of the art
- Emerging technologies and innovations
- Recent expert opinions
Use terms like: 2024, 2025, latest, recent, new, trends, updates, breaking""",

        "technical": """Focus on technical and detailed documentation:
- Official documentation and API references
- Technical specifications and standards
- Architecture and design documents
- Developer documentation
- Technical deep-dives and detailed explanations
- Protocol specifications
Use terms like: documentation, technical, specification, API, reference, architecture, protocol""",

        "comprehensive": """Focus on comprehensive overviews and foundational knowledge:
- Complete guides and definitive resources
- Foundational concepts and principles
- Introduction and overview articles
- Beginner to advanced coverage
- Comprehensive reference materials
- Encyclopedic resources
Use terms like: complete guide, overview, introduction, comprehensive, fundamentals, basics, definitive"""
    }

    focus_instruction = focus_instructions.get(focus, focus_instructions["balanced"])

    prompt = f"""You are helping to research a topic for deep study and comprehensive understanding.

Topic: {topic}

Generate {num_queries} diverse, high-quality web search queries optimized for this focus:

{focus_instruction}

Each query should be:
- Specific and targeted to find authoritative sources
- Optimized for search engines (natural language but focused)
- Likely to return in-depth, long-form content
- Diverse enough to cover different facets of the topic
- Tailored to the specified focus area

Output exactly {num_queries} search queries, one per line, with NO bullets, numbers, or extra formatting.
Just the raw search query text on each line."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"You are an expert research assistant specializing in generating highly effective search queries for {focus} research that retrieve comprehensive information from authoritative sources."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
        max_tokens=600
    )

    text = response.choices[0].message.content
    # Split into lines, strip empties, remove any numbering/bullets
    queries = []
    for line in text.split("\n"):
        line = line.strip()
        # Remove common prefixes like "1.", "- ", etc.
        import re
        line = re.sub(r'^\d+[\.\)]\s*', '', line)  # Remove "1. " or "1) "
        line = re.sub(r'^[-•*]\s*', '', line)       # Remove "- " or "• "
        if line:
            queries.append(line)

    return queries[:num_queries]


def score_result_relevance(topic: str, title: str, url: str) -> dict:
    """
    Use OpenAI to score how relevant a search result is to the topic.
    Returns a dict with score (0-100) and reasoning.
    """
    prompt = f"""You are evaluating the relevance of a search result for a research topic.

Research Topic: {topic}

Search Result:
Title: {title}
URL: {url}

Evaluate this search result on a scale of 0-100 based on:
1. Relevance to the topic (0-40 points)
2. Likely quality and authority (0-30 points)
3. Depth and comprehensiveness (0-30 points)

Consider:
- Is this likely to be authoritative? (educational sites, research, official docs = higher)
- Does it appear to be in-depth? (guides, papers, documentation = higher)
- Is it likely spam or low-quality? (random blogs, ads, listicles = lower)

Respond with ONLY a JSON object in this exact format:
{{"score": 85, "reasoning": "Brief explanation"}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert research evaluator who assesses source quality and relevance."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower for more consistent scoring
            max_tokens=150
        )

        import json
        result = json.loads(response.choices[0].message.content)
        return {
            "score": result.get("score", 50),
            "reasoning": result.get("reasoning", "")
        }
    except Exception as e:
        print(f"Error scoring result: {e}")
        return {"score": 50, "reasoning": "Unable to score"}


def filter_results_by_quality(topic: str, results: list, min_score: int = 60, max_to_score: int = 30) -> list:
    """
    Filter search results using AI to remove low-quality sources.

    Args:
        topic: Research topic
        results: List of search results with 'title' and 'url'
        min_score: Minimum relevance score (0-100) to keep
        max_to_score: Maximum number of results to score (to prevent timeouts)

    Returns:
        Filtered list with scores added
    """
    filtered = []

    # Limit how many we score to prevent timeouts
    results_to_score = results[:max_to_score]
    remaining_results = results[max_to_score:]

    print(f"Scoring {len(results_to_score)} sources (limit: {max_to_score})...")

    for i, result in enumerate(results_to_score, 1):
        title = result.get('title', 'No title')
        url = result.get('url', '')

        print(f"[{i}/{len(results_to_score)}] Scoring: {title[:50]}...")

        # Score the result
        score_data = score_result_relevance(topic, title, url)

        # Add score to result
        result['relevance_score'] = score_data['score']
        result['score_reasoning'] = score_data['reasoning']

        # Keep if meets threshold
        if score_data['score'] >= min_score:
            filtered.append(result)
            print(f"  ✓ Score {score_data['score']}: KEEP")
        else:
            print(f"  ✗ Score {score_data['score']}: FILTERED OUT")

    # Add remaining unscored results without filtering (they won't have scores)
    if remaining_results:
        print(f"\nAdding {len(remaining_results)} unscored results (exceeded max_to_score limit)")
        filtered.extend(remaining_results)

    # Sort by score descending (unscored items will be at the end)
    filtered.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

    return filtered


def summarize_content(topic: str, content: str, url: str) -> str:
    """
    Use OpenAI to create a concise summary of scraped content.
    """
    # Truncate content for API
    content_sample = content[:3000] if len(content) > 3000 else content

    prompt = f"""Summarize the key points from this web content that are relevant to the research topic.

Research Topic: {topic}
Source URL: {url}

Content:
{content_sample}

Provide a concise 3-5 sentence summary focusing on the most important and relevant information for researching this topic. If the content is not relevant, say so."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a research assistant who creates concise, accurate summaries of source material."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=200
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error summarizing content: {e}")
        return "Summary unavailable."


def refine_queries_from_results(topic: str, initial_queries: list, initial_results: list) -> list:
    """
    Use OpenAI to generate refined queries based on initial search results.
    This helps find better sources by learning from what was already found.
    """
    # Sample some result titles
    sample_titles = [r.get('title', '') for r in initial_results[:10]]
    titles_text = "\n".join(f"- {t}" for t in sample_titles)

    prompt = f"""You are refining search queries based on initial results.

Research Topic: {topic}

Initial Queries Used:
{chr(10).join(f"- {q}" for q in initial_queries)}

Sample Results Found:
{titles_text}

Based on these initial results, generate 3 NEW refined search queries that will find:
1. Different angles or aspects not well covered
2. More authoritative or comprehensive sources
3. Complementary information

Output exactly 3 search queries, one per line, with NO bullets, numbers, or extra formatting."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert research assistant who refines search strategies based on initial findings."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=300
        )

        text = response.choices[0].message.content
        queries = []
        for line in text.split("\n"):
            line = line.strip()
            import re
            line = re.sub(r'^\d+[\.\)]\s*', '', line)
            line = re.sub(r'^[-•*]\s*', '', line)
            if line:
                queries.append(line)

        return queries[:3]
    except Exception as e:
        print(f"Error refining queries: {e}")
        return []


def fetch_and_clean(url: str, max_chars: int = 15000):
    """
    Download a page and extract readable text.
    This is simple and not perfect, but good enough for a first version.
    """
    try:
        print(f"Fetching: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, timeout=15, headers=headers)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove script/style/nav/footer, etc.
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript", "svg", "form"]):
        tag.decompose()

    # Basic heuristic: join all <p> and <h1-3> text
    parts = []
    for el in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        text = el.get_text(" ", strip=True)
        if not text:
            continue

        if el.name.startswith("h"):
            parts.append(f"<h3>{text}</h3>")
        elif el.name in ["p", "li"]:
            parts.append(f"<p>{text}</p>")

    content = "\n".join(parts)
    # Truncate to avoid huge PDFs
    if len(content) > max_chars:
        content = content[:max_chars] + "<p>[Truncated]</p>"

    return content


def build_html_document(topic: str, sources: list):
    """
    sources: list of (url, html_body_str)
    """
    html_parts = [
        "<html>",
        "<head>",
        "<meta charset='utf-8'>",
        f"<title>{topic}</title>",
        """
        <style>
        body { font-family: sans-serif; margin: 2em; }
        h1 { font-size: 28px; margin-bottom: 0.5em; }
        h2 { font-size: 22px; margin-top: 1.5em; }
        h3 { font-size: 18px; margin-top: 1em; }
        p { line-height: 1.5; font-size: 14px; }
        hr { margin: 2em 0; }
        .source-url { font-size: 12px; color: #555; }
        </style>
        """,
        "</head>",
        "<body>",
        f"<h1>Research Pack: {topic}</h1>"
    ]

    for i, (url, body_html) in enumerate(sources, start=1):
        html_parts.append("<hr/>")
        html_parts.append(f"<h2>Source {i}</h2>")
        html_parts.append(f"<div class='source-url'>{url}</div>")
        html_parts.append(body_html)

    html_parts.append("</body></html>")
    return "\n".join(html_parts)


def html_to_pdf(html_str: str, output_path: str):
    HTML(string=html_str).write_pdf(output_path)
    print(f"Saved PDF to: {output_path}")


def main():
    topic = input("Enter your research topic: ").strip()
    if not topic:
        print("No topic provided, exiting.")
        return

    print("\nGenerating search queries with OpenAI...")
    queries = generate_search_queries(topic)
    print("Queries:")
    for q in queries:
        print("  -", q)

    # Collect URLs (naive: just take results from first query for now)
    # You can later merge from multiple queries, dedupe, etc.
    print("\nSearching the web for the first query...")
    first_query = queries[0]
    search_results = search_web(first_query, num_results=10)

    urls = []
    for r in search_results:
        url = r.get("url")
        if url and url not in urls:
            urls.append(url)

    urls = urls[:10]
    print("\nSelected URLs:")
    for u in urls:
        print(" -", u)

    # Fetch content
    sources = []
    for u in urls:
        content_html = fetch_and_clean(u)
        if content_html:
            sources.append((u, content_html))

    if not sources:
        print("No content fetched, exiting.")
        return

    # Build HTML + convert to PDF
    html_doc = build_html_document(topic, sources)
    safe_topic = "".join(c for c in topic if c.isalnum() or c in (" ", "_", "-")).strip()
    if not safe_topic:
        safe_topic = "research"
    output_pdf = f"{safe_topic.replace(' ', '_')}.pdf"

    print("\nConverting to PDF with WeasyPrint...")
    html_to_pdf(html_doc, output_pdf)

    print("\nDone!")
    print("You can now upload that PDF into NotebookLM (or your favorite LLM notebook)")
    print("to read, highlight, and generate audio from it.")


if __name__ == "__main__":
    main()
