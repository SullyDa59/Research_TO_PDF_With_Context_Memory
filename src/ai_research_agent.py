"""
AI Research Agent Module
Uses OpenAI API + mem0 context to generate research content directly
No web search required - relies on AI knowledge base and user memory
"""
import os
from openai import OpenAI
import memory_layer as mem
import json

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_research_content(user_id, topic, depth='comprehensive'):
    """
    Generate research content using AI + user's memory context

    Args:
        user_id: User identifier for mem0 context
        topic: Research topic
        depth: 'quick', 'comprehensive', or 'deep'

    Returns:
        dict with research sections and sources
    """
    # Get user's preferences and past research
    preferences = mem.get_user_preferences(user_id)
    memories = mem.search_memory(user_id, topic, limit=5)

    # Build context from user's memory
    context = ""
    if preferences.get('preferred_domains'):
        top_domains = [d[0] for d in preferences['preferred_domains'][:3]]
        context += f"User prefers sources from: {', '.join(top_domains)}\n"

    if preferences.get('topics'):
        related_topics = [t[0] for t in preferences['topics'][:3]]
        context += f"User has researched: {', '.join(related_topics)}\n"

    # Check if user has researched similar topics
    if memories:
        context += f"User has {len(memories)} related research sessions\n"

    # Determine content depth
    sections_count = {
        'quick': 3,
        'comprehensive': 5,
        'deep': 8
    }.get(depth, 5)

    # Generate research content
    prompt = f"""You are a research assistant helping with the topic: "{topic}"

User Context:
{context if context else "First-time researcher on this topic"}

Generate comprehensive research content with {sections_count} main sections. For each section:
1. Provide a clear heading
2. Write 2-3 paragraphs of detailed information
3. Include specific facts, concepts, and explanations
4. Cite credible source types (e.g., "According to academic research...", "Industry studies show...")

Format as JSON:
{{
    "title": "Research on {topic}",
    "summary": "2-3 sentence overview",
    "sections": [
        {{
            "heading": "Section title",
            "content": "Detailed paragraphs...",
            "key_points": ["point 1", "point 2", "point 3"]
        }}
    ],
    "recommended_sources": [
        {{
            "title": "Source title",
            "type": "academic paper / industry report / documentation / etc",
            "description": "What this source covers",
            "relevance": "Why it's valuable for this topic"
        }}
    ],
    "next_steps": ["Suggested follow-up research topic 1", "Suggested follow-up research topic 2"]
}}

Make it thorough, accurate, and well-structured."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Track token usage
        tokens_used = response.usage.total_tokens
        # gpt-4o-mini pricing: $0.15/1M input, $0.60/1M output (avg ~$0.20/1M)
        estimated_cost = (tokens_used / 1_000_000) * 0.20

        result['metadata'] = {
            'tokens_used': tokens_used,
            'estimated_cost': estimated_cost,
            'model': 'gpt-4o-mini',
            'mode': 'ai_agent'
        }

        return result

    except Exception as e:
        print(f"Error generating AI research: {e}")
        return {
            'title': f"Research on {topic}",
            'summary': f"AI research generation encountered an error: {str(e)}",
            'sections': [],
            'recommended_sources': [],
            'next_steps': [],
            'error': str(e)
        }

def generate_quick_insights(user_id, topic):
    """
    Generate quick insights for a topic using AI
    Faster, less comprehensive than full research
    """
    preferences = mem.get_user_preferences(user_id)

    prompt = f"""Provide quick research insights on: "{topic}"

Generate 5-7 key insights or facts about this topic. Each should be:
- Concise (1-2 sentences)
- Informative and specific
- Accurate and verifiable

Format as JSON:
{{
    "insights": [
        {{"point": "Insight text", "category": "fundamental/application/trend/etc"}},
    ],
    "one_sentence_summary": "Overall summary"
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print(f"Error generating quick insights: {e}")
        return {
            'insights': [],
            'one_sentence_summary': f"Error: {str(e)}"
        }

def format_research_as_markdown(research_data):
    """Convert AI research data to markdown format for PDF generation"""
    md = f"# {research_data.get('title', 'Research Report')}\n\n"

    # Summary
    if research_data.get('summary'):
        md += f"## Summary\n\n{research_data['summary']}\n\n"

    # Sections
    for section in research_data.get('sections', []):
        md += f"## {section['heading']}\n\n"
        md += f"{section['content']}\n\n"

        if section.get('key_points'):
            md += "**Key Points:**\n"
            for point in section['key_points']:
                md += f"- {point}\n"
            md += "\n"

    # Recommended Sources
    if research_data.get('recommended_sources'):
        md += "## Recommended Sources\n\n"
        for i, source in enumerate(research_data['recommended_sources'], 1):
            md += f"### {i}. {source['title']}\n"
            md += f"**Type:** {source['type']}\n\n"
            md += f"{source['description']}\n\n"
            md += f"*Relevance:* {source['relevance']}\n\n"

    # Next Steps
    if research_data.get('next_steps'):
        md += "## Suggested Next Steps\n\n"
        for step in research_data['next_steps']:
            md += f"- {step}\n"
        md += "\n"

    # Metadata
    if research_data.get('metadata'):
        meta = research_data['metadata']
        md += "---\n\n"
        md += f"*Generated by AI Research Agent*\n\n"
        md += f"Model: {meta.get('model', 'N/A')} | "
        md += f"Tokens: {meta.get('tokens_used', 'N/A')} | "
        md += f"Est. Cost: ${meta.get('estimated_cost', 0):.4f}\n"

    return md

def generate_smart_search_queries(user_id, topic, num_queries=7):
    """
    Generate smart search queries using AI + mem0 context
    Uses user's research history and preferences to create personalized queries

    Args:
        user_id: User identifier for mem0 context
        topic: Research topic
        num_queries: Number of queries to generate

    Returns:
        list of search queries optimized for finding relevant sources
    """
    # Get user's preferences and past research
    preferences = mem.get_user_preferences(user_id)
    memories = mem.search_memory(user_id, topic, limit=5)

    # Build context from user's memory
    context = ""

    # Add persistent contexts first (highest priority)
    persistent_context = mem.get_persistent_context_summary(user_id)
    if persistent_context:
        context += persistent_context + "\n"

    if preferences.get('preferred_domains'):
        top_domains = [d[0] for d in preferences['preferred_domains'][:3]]
        context += f"User's preferred source domains: {', '.join(top_domains)}\\n"

    if preferences.get('topics'):
        related_topics = [t[0] for t in preferences['topics'][:3]]
        context += f"User's research interests: {', '.join(related_topics)}\\n"

    if memories:
        context += f"User has researched {len(memories)} related topics before\\n"

    # Generate smart queries using AI
    prompt = f"""You are a research assistant helping to find web sources on: "{topic}"

User Context:
{context if context else "First-time researcher on this topic"}

Generate {num_queries} highly effective web search queries to find the best sources for this topic.

Requirements:
- Make queries specific and targeted (not too broad)
- Include variety: academic papers, documentation, tutorials, recent developments
- Use search operators when helpful (site:, OR, quotes, etc.)
- Consider user's interests and previous research
- Make queries likely to find high-quality, authoritative sources

Format as JSON:
{{
    "queries": ["query 1", "query 2", ...]
}}

Make each query optimized for finding the most relevant and useful web sources."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,  # Higher for more diverse queries
            max_tokens=800,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        queries = result.get('queries', [])

        # Track token usage
        tokens_used = response.usage.total_tokens
        estimated_cost = (tokens_used / 1_000_000) * 0.20

        print(f"✓ Generated {len(queries)} AI-powered queries (tokens: {tokens_used}, cost: ${estimated_cost:.4f})")

        return queries

    except Exception as e:
        print(f"Error generating AI queries: {e}")
        # Fallback to a simple query
        return [topic]

print("✓ AI Research Agent module loaded successfully")
