# Interactive AI Assistant Guide

## Overview

Your research application now has a fully interactive AI assistant that learns your preferences and provides personalized guidance throughout your research workflow!

## New Interactive Features

### 1. Personalized Homepage Greeting

**What You'll See:**
- Custom greeting based on your research history
- Session count ("You've completed 5 research sessions")
- Recently researched topics
- Personalized suggestions

**First Time:**
```
👋 Welcome! Start your first research session below.
Try researching a topic you're curious about. I'll learn your preferences as you go!
```

**After Several Sessions:**
```
👋 Welcome back! You've completed 12 research sessions.
Recently researched: quantum computing, machine learning. Ready for more?
```

### 2. AI-Powered Topic Suggestions

**What It Does:**
- Analyzes your research history
- Suggests related topics you might want to explore
- One-click to start researching suggested topics

**Example:**
```
💡 Suggested Topics:
[Quantum Cryptography] [Quantum Error Correction] [Topological Quantum Computing]
```

**How It Works:**
- Click any suggested topic → auto-fills the search box
- Based on semantic analysis of your past research
- Gets smarter as you complete more sessions

### 3. AI Coaching Tips

**Throughout Your Workflow:**
- Homepage tips for getting started
- Query generation tips
- Source selection guidance
- Completion celebration and next steps

**Example Tips:**
- "🎯 Be specific with your topic for better results"
- "✅ Review generated queries - you can deselect any that don't fit"
- "⭐ Sources from your preferred domains are highlighted"
- "🎉 Great job! Your preferences have been saved"

### 4. AI Query Analysis

**After Query Generation:**
- AI reviews your generated queries
- Provides friendly feedback
- Suggests improvements
- Checks coverage and diversity

**Example Analysis:**
```
💡 These queries should help find sources from your preferred domains: mit.edu, arxiv.org, ieee.org

🤖 AI Analysis:
These queries cover a good range! You've got foundational knowledge (basics),
technical implementation (algorithms), and practical applications (hardware).
One suggestion: Consider adding a query about recent breakthroughs (2024-2025)
to capture cutting-edge research.
```

### 5. Smart Source Highlighting

**Preferred Domains** (Green Highlight):
- Sources from domains you frequently select
- Auto-checked by default
- Visual indicator: Green border + background
- Banner: "⭐ You frequently select sources from arxiv.org"

**Avoided Domains** (Red Highlight):
- Sources from domains you typically skip
- Un-checked by default
- Visual indicator: Red border + background
- Banner: "⚠️ You typically skip sources from spam-site.com"

**Example:**
```
⭐ 12 sources from your preferred domains!
These sources are highlighted based on your selection history.

⚠️ 3 sources from domains you typically skip
You usually don't select these - consider reviewing carefully.
```

### 6. Personalized Completion Insights

**After PDF Generation:**
- Session statistics
- Comparison to your history
- Learning progress updates
- Next research suggestions

**Example Insights:**
```
📊 Your Research Insights:
• This is your session #15!
• Great curation! You selected 24% of sources.
• I'm learning your preferences - I've identified 8 domains you prefer!

🎯 Suggested Next Research:
Quantum Machine Learning Applications
[Start this research →]

🤖 What's Next:
• Great job! Your preferences have been saved
• Visit Analytics to see your research trends
• Mem0 is learning - future searches will be even better
```

### 7. Next Research Recommendations

**AI-Powered Suggestions:**
- Analyzes your research topics
- Identifies complementary research areas
- One-click to start suggested research

**How It Works:**
1. Completes analysis of your past topics
2. Finds research gaps
3. Suggests specific next topics
4. Click button → starts new session with suggested topic

## How the AI Learns

### Preference Learning

**What Gets Tracked:**
1. **Source Domains**: Which domains you select/reject
2. **AI Modes**: Your preferred enhancement levels
3. **Topics**: Frequently researched subjects
4. **Patterns**: Your research behavior over time

**Learning Process:**
```
Session 1: Just tracking
Session 2-3: Starting to identify patterns
Session 4-5: Confident preferences emerge
Session 6+: Strong personalization kicks in
```

### Memory System

**Two Types of Memories:**

**Research Session Memories:**
```
Topic: quantum computing
AI Mode: quality
Sources Selected: 15 out of 50
Top Queries: quantum basics, quantum algorithms, quantum hardware
Date: 2025-11-19
```

**Source Preference Memories:**
```
Selected: Introduction to Quantum Computing - MIT
Domain: mit.edu
AI Score: 85/100
For Topic: quantum computing
```

### Smart Defaults

**After You Research:**
- Remembers your preferred AI enhancement level
- Auto-selects your typical settings
- Adapts to your research style

**Example:**
- You always use "Quality" mode → becomes default
- You prefer 10 queries → pre-selected
- You like academic focus → auto-selected

## Interactive Workflow

### Step 1: Homepage

**You See:**
- Personalized greeting
- Topic suggestions (clickable)
- AI coaching tips
- Quick access buttons

**AI Actions:**
- Analyzes your history
- Generates topic suggestions
- Provides contextual tips

### Step 2: Query Generation

**You See:**
- Generated queries
- AI analysis of query quality
- Tips for review
- Coaching guidance

**AI Actions:**
- Reviews query diversity
- Checks coverage
- Suggests improvements
- References your preferences

### Step 3: Source Selection

**You See:**
- Highlighted preferred sources (green)
- Flagged rejected domains (red)
- Count of preferred sources
- Selection tips

**AI Actions:**
- Identifies preferred domains
- Auto-selects good sources
- Warns about typically rejected domains
- Provides selection guidance

### Step 4: Completion

**You See:**
- Personalized insights
- Session statistics
- Next research suggestion
- Celebration & tips

**AI Actions:**
- Analyzes session patterns
- Compares to your history
- Suggests next research
- Saves preferences

## Example User Journey

**New User (Session 1):**
```
Homepage: "Welcome! Start your first research session"
Queries: General AI tips about query diversity
Sources: No highlighting (no preferences yet)
Completion: "Great start! I'm learning your preferences"
```

**After 3 Sessions:**
```
Homepage: "Welcome back! You've completed 3 sessions"
Topic Suggestions: [Related Topic 1] [Related Topic 2]
Queries: "These should find sources from domains you've used before"
Sources: 2-3 preferred domains highlighted
Completion: "Session #4! You prefer Quality mode"
```

**After 10 Sessions:**
```
Homepage: "You've completed 10 sessions! Recently: quantum computing, ML"
Topic Suggestions: Smart recommendations based on your interests
Queries: Detailed analysis referencing your patterns
Sources: 5-8 preferred domains highlighted in green
Completion: "This is session #11! I've identified 8 preferred domains!"
Next Research: "Try: Quantum Machine Learning"
```

## AI Cost Impact

**Additional AI Calls:**

**Per Session:**
- Topic suggestions: ~$0.0001-0.0002
- Query analysis: ~$0.0002-0.0003
- Next research suggestion: ~$0.0001-0.0002

**Total Added Cost:** ~$0.0004-0.0007 per session

**Worth It?** YES!
- Dramatically better UX
- Saves you time
- Gets better over time
- Still under $0.001 per session

## Privacy & Data

**What's Stored:**
- Your research topics
- Source selections
- AI mode preferences
- All stored locally in mem0

**What's Sent to OpenAI:**
- Topic text (for suggestions)
- Query text (for analysis)
- Past topics (for recommendations)
- NO personal information
- NO source content

**You Control:**
- All data is local
- Delete anytime
- No tracking beyond your machine

## Customization Options

### Disable AI Assistant Features

**To turn off AI suggestions:**
Edit `ai_assistant.py` and set:
```python
ENABLE_SUGGESTIONS = False  # No topic suggestions
ENABLE_ANALYSIS = False     # No query analysis
ENABLE_HIGHLIGHTS = False   # No source highlighting
```

### Adjust Suggestion Count

**Change number of topic suggestions:**
In `ai_assistant.py`:
```python
def get_topic_suggestions(...):
    # Change from 3 to your preferred number
    return suggestions[:3]  # ← Change this number
```

### Modify Coaching Tips

**Edit tips in `ai_assistant.py`:**
```python
tips = {
    'start': [
        "Your custom tip here",
        "Another tip",
    ],
    ...
}
```

## Troubleshooting

### Not Seeing Suggestions

**Problem:** No topic suggestions on homepage
**Cause:** Need at least 2-3 sessions for patterns
**Solution:** Complete more research sessions

### Slow Query Analysis

**Problem:** Query page takes long to load
**Cause:** AI analysis is processing
**Solution:** Normal! Takes 2-5 seconds for analysis

### Wrong Preferences

**Problem:** Highlighting wrong domains
**Cause:** Learning from early sessions
**Solution:** Complete more sessions to refine, or clear mem0 data

### No Personalization

**Problem:** Everything looks generic
**Cause:** First session or mem0 not saving
**Solution:** Check mem0 monitor (/mem0-monitor) for operation count

## Best Practices

### Get Better Suggestions

1. **Be Consistent**: Research related topics to build patterns
2. **Complete Sessions**: Finish by generating PDFs (saves preferences)
3. **Be Decisive**: Select sources consistently (helps learning)
4. **Give It Time**: 5-10 sessions for strong personalization

### Maximize Learning

1. **Use Topic Suggestions**: Click them to research related areas
2. **Review AI Analysis**: Learn from query feedback
3. **Check Preferences**: Visit /mem0-preferences to see what's learned
4. **Iterate**: The more you research, the smarter it gets

### Optimize Performance

1. **First Session**: Expect generic experience
2. **Sessions 2-5**: Watch patterns emerge
3. **Sessions 6+**: Enjoy full personalization
4. **Ongoing**: Preferences keep improving

## Feature Comparison

**Without AI Assistant:**
- Generic homepage
- No topic suggestions
- No query feedback
- Manual source review
- No learning

**With AI Assistant:**
- Personalized greetings
- Smart topic suggestions
- AI query analysis
- Highlighted preferred sources
- Continuous learning
- Research recommendations
- Personalized insights
- Coaching throughout

## Summary

The AI Assistant transforms your research experience from a tool into an intelligent partner that:

✅ **Learns** your preferences automatically
✅ **Suggests** relevant topics to explore
✅ **Analyzes** your queries for quality
✅ **Highlights** sources you'll likely select
✅ **Recommends** next research directions
✅ **Celebrates** your progress
✅ **Coaches** you throughout the workflow
✅ **Gets Smarter** with every session

**Cost:** Under $0.001 additional per session
**Benefit:** Dramatically better, personalized research experience
**Learning:** Gets better over time automatically

---

**Try it now at http://localhost:5001**

Start a research session and watch the AI assistant help guide you through!
