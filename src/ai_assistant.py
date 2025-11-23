"""
AI Assistant Module
Provides personalized suggestions and interactive guidance
based on user's research history and preferences
"""
import os
from openai import OpenAI
import memory_layer as mem

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def get_personalized_greeting(user_id):
    """Generate a personalized greeting based on user's history"""
    preferences = mem.get_user_preferences(user_id)
    memories = mem.get_all_memories(user_id, limit=10)

    if not memories:
        return {
            'greeting': "👋 Welcome! Start your first research session below.",
            'suggestion': "Try researching a topic you're curious about. I'll learn your preferences as you go!"
        }

    # Get recent topics
    topics = [m.get('metadata', {}).get('topic') for m in memories if isinstance(m, dict) and m.get('metadata', {}).get('topic')]
    recent_topics = list(set(topics))[:3]

    # Get preferred AI mode
    ai_modes = preferences.get('ai_modes', [])
    preferred_mode = ai_modes[0][0] if ai_modes else 'basic'

    # Get session count
    session_count = sum(1 for m in memories if isinstance(m, dict) and m.get('metadata', {}).get('type') == 'research_session')

    greeting = f"👋 Welcome back! You've completed {session_count} research sessions."

    if recent_topics:
        suggestion = f"Recently researched: {', '.join(recent_topics[:2])}. Ready for more?"
    else:
        suggestion = f"Your preferred AI mode is {preferred_mode}. Keep up the great research!"

    return {
        'greeting': greeting,
        'suggestion': suggestion
    }

def get_topic_suggestions(user_id, current_topic=None):
    """Suggest related topics based on research history"""
    preferences = mem.get_user_preferences(user_id)
    memories = mem.get_all_memories(user_id, limit=20)

    if not memories:
        return []

    # Extract all topics
    topics = preferences.get('topics', [])

    if not topics:
        return []

    # Get AI to suggest related topics
    topic_list = ', '.join([t[0] for t in topics[:5]])

    prompt = f"""Based on these research topics: {topic_list}

Suggest 3 new related research topics that would be interesting to explore next.
{'Current topic being researched: ' + current_topic if current_topic else ''}

Format: Return only a JSON array of topic strings.
Example: ["topic 1", "topic 2", "topic 3"]
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=100
        )

        import json
        suggestions = json.loads(response.choices[0].message.content)
        return suggestions[:3]
    except:
        return []

def get_smart_defaults(user_id):
    """Get smart default settings based on user preferences"""
    preferences = mem.get_user_preferences(user_id)

    defaults = {
        'num_queries': 7,
        'results_per_query': 30,
        'max_sources': 50,
        'query_focus': 'balanced',
        'ai_enhancement': 'basic',
        'min_quality_score': 60,
        'max_to_score': 30
    }

    # Adjust based on preferences
    ai_modes = preferences.get('ai_modes', [])
    if ai_modes:
        # Most used AI mode
        defaults['ai_enhancement'] = ai_modes[0][0]

    return defaults

def analyze_queries(user_id, topic, queries):
    """Provide AI feedback on generated queries"""
    preferences = mem.get_user_preferences(user_id)

    # Get user's past successful queries (from selected sources)
    memories = mem.get_all_memories(user_id, limit=50)

    # Build context
    context = "Based on your research history, here's my analysis:\n\n"

    # Check if queries align with user's style
    preferred_domains = preferences.get('preferred_domains', [])

    if preferred_domains:
        top_domains = ', '.join([d[0] for d in preferred_domains[:3]])
        context += f"💡 These queries should help find sources from your preferred domains: {top_domains}\n\n"

    # AI analysis of query quality
    prompt = f"""Analyze these research queries for the topic "{topic}":

{chr(10).join([f'{i+1}. {q}' for i, q in enumerate(queries)])}

Provide brief, friendly analysis:
1. Are these queries diverse enough?
2. Any gaps in coverage?
3. One specific suggestion to improve

Keep it under 100 words, be encouraging and specific."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150
        )

        analysis = response.choices[0].message.content
        return context + "🤖 AI Analysis:\n" + analysis
    except:
        return context + "Queries look good! Happy researching!"

def highlight_preferred_sources(user_id, sources):
    """Add markers to sources from preferred domains"""
    preferences = mem.get_user_preferences(user_id)
    preferred_domains = {d[0] for d, _ in preferences.get('preferred_domains', [])}
    rejected_domains = {d[0] for d, _ in preferences.get('rejected_domains', [])}

    for source in sources:
        url = source.get('url', '')

        # Check if from preferred domain
        for domain in preferred_domains:
            if domain in url:
                source['is_preferred'] = True
                source['preference_note'] = f"⭐ You frequently select sources from {domain}"
                break

        # Check if from rejected domain
        for domain in rejected_domains:
            if domain in url:
                source['is_rejected'] = True
                source['preference_note'] = f"⚠️ You typically skip sources from {domain}"
                break

    return sources

def get_research_insights(user_id, topic):
    """Get AI insights about researching this topic"""
    memories = mem.search_memory(user_id, topic, limit=5)

    if not memories:
        return None

    # Check if user has researched similar topics
    similar_count = len([m for m in memories if isinstance(m, dict) and m.get('metadata', {}).get('type') == 'research_session'])

    if similar_count > 0:
        return {
            'type': 'similar_research',
            'message': f"💡 You've researched similar topics {similar_count} time(s) before. Check your history for related insights!",
            'memories': memories
        }

    return None

def generate_personalized_summary(user_id, session_data):
    """Generate a personalized summary after research completion"""
    preferences = mem.get_user_preferences(user_id)

    # Build personalized message
    messages = []

    # Compare to past sessions
    topics = preferences.get('topics', [])
    if topics:
        total_sessions = sum(count for _, count in topics)
        messages.append(f"📊 This is your session #{total_sessions + 1}!")

    # Source selection rate
    selection_rate = (session_data['selected_sources'] / session_data['total_sources'] * 100) if session_data['total_sources'] > 0 else 0

    if selection_rate > 30:
        messages.append(f"✨ Great curation! You selected {selection_rate:.0f}% of sources.")
    elif selection_rate < 10:
        messages.append(f"🎯 Very selective! Only {selection_rate:.0f}% made the cut.")

    # Learning insight
    preferred_domains = preferences.get('preferred_domains', [])
    if len(preferred_domains) >= 3:
        messages.append(f"🧠 I'm learning your preferences - I've identified {len(preferred_domains)} domains you prefer!")

    return messages

def suggest_next_research(user_id):
    """Suggest what to research next"""
    preferences = mem.get_user_preferences(user_id)
    topics = preferences.get('topics', [])

    if not topics:
        return None

    # Find research gaps
    prompt = f"""Based on these research topics: {', '.join([t[0] for t in topics[:5]])}

Suggest ONE specific follow-up research topic that would complement this research.
Be specific and actionable. Return only the topic name (no explanation)."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=50
        )

        suggestion = response.choices[0].message.content.strip()
        return suggestion
    except:
        return None

def get_interactive_feedback(user_id, action, data):
    """Get real-time feedback during research workflow"""
    feedback = {
        'message': '',
        'tips': [],
        'insights': []
    }

    preferences = mem.get_user_preferences(user_id)

    if action == 'query_generation':
        # Feedback on query generation
        ai_mode = data.get('ai_mode', 'basic')
        if ai_mode == 'none':
            feedback['tips'].append("💡 Tip: Try 'Basic' AI mode for smarter queries (costs ~$0.0003)")

        num_queries = data.get('num_queries', 7)
        if num_queries < 5:
            feedback['tips'].append("📝 More queries = more diverse sources. Consider 7-10 queries!")

    elif action == 'source_selection':
        # Feedback on source selection
        selected = data.get('selected', 0)
        total = data.get('total', 0)

        if selected == 0:
            feedback['message'] = "🤔 No sources selected yet. Click checkboxes to select sources!"
        elif selected < 5:
            feedback['message'] = f"You've selected {selected} sources. More sources = more comprehensive research!"
        else:
            feedback['message'] = f"Great selection! {selected} sources should provide good coverage."

        # Check if using preferred domains
        preferred_count = data.get('preferred_count', 0)
        if preferred_count > 0:
            feedback['insights'].append(f"⭐ {preferred_count} sources from your preferred domains!")

    elif action == 'completion':
        # Feedback on completion
        personalized = generate_personalized_summary(user_id, data)
        feedback['insights'].extend(personalized)

        # Suggest next topic
        next_topic = suggest_next_research(user_id)
        if next_topic:
            feedback['tips'].append(f"🎯 Next research idea: {next_topic}")

    return feedback

def get_ai_coaching(user_id, stage):
    """Get AI coaching tips for different stages of research"""
    tips = {
        'start': [
            "🎯 Be specific with your topic for better results",
            "💡 The AI will learn your preferences over time",
            "📊 Check the Mem0 monitor to see your research patterns"
        ],
        'queries': [
            "✅ Review generated queries - you can deselect any that don't fit",
            "🔍 More queries = more diverse results",
            "💭 The AI learns which queries work best for you"
        ],
        'sources': [
            "⭐ Sources from your preferred domains are highlighted",
            "🔗 Click links to preview before selecting",
            "💎 Quality over quantity - select the best sources"
        ],
        'complete': [
            "🎉 Great job! Your preferences have been saved",
            "📈 Visit Analytics to see your research trends",
            "🧠 Mem0 is learning - future searches will be even better"
        ]
    }

    return tips.get(stage, [])

print("✓ AI Assistant module loaded successfully")
