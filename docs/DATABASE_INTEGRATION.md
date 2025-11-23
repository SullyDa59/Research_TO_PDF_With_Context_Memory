# SQLite Database Integration

## Overview

The Research to PDF Generator now includes a complete SQLite database integration that provides persistent memory storage across research sessions. This allows you to:

- Track all research sessions and their configurations
- Review past queries and sources
- Analyze research patterns and trends
- Build a knowledge base of high-quality sources
- Learn from past selection preferences

## Database Schema

### Tables

**research_sessions**
- Stores each research session with topic, date, AI settings, and completion status
- Tracks: topic, date, num_queries, ai_mode, query_focus, min_quality_score, max_sources, completed

**queries**
- Stores all generated search queries for each session
- Tracks which queries were actually selected and used
- Links to: research_sessions (session_id)

**sources**
- Stores all sources found during research
- Includes AI quality scores and reasoning when applicable
- Tracks which sources were selected for PDF inclusion
- Links to: research_sessions (session_id)

### Database File

All data is stored in a single file: `research_memory.db`
- Automatically created on first run
- Located in the project directory
- Easy to backup (just copy the file)
- Portable across systems

## New Features

### 1. Research History (`/history`)

View all your past research sessions with:
- Topic and date
- AI enhancement mode used
- Number of queries generated and used
- Number of sources found and selected
- Completion status
- Click any session to view full details

Access: Click "View History" button on homepage

### 2. Session Details (`/session/<id>`)

View complete details of any past session:
- All configuration settings used
- Generated queries (marked which were selected)
- All sources found (marked which were included in PDF)
- AI quality scores and reasoning
- Links to all sources for easy review

### 3. Analytics Dashboard (`/analytics`)

Get insights into your research patterns:
- Total sessions and completion rate
- Total sources found and selection rate
- Most researched topics
- AI enhancement mode usage patterns
- Top sources (selected multiple times across sessions)
- Average AI quality scores for frequently used sources

Access: Click "Analytics" button on homepage or history page

## How Data is Saved

### Automatic Saving

The database automatically saves:

1. **Session Start** - When you enter a topic and generate queries
   - Topic, configuration settings, AI mode

2. **Query Generation** - After AI generates search queries
   - All generated queries

3. **Query Selection** - When you select which queries to use
   - Updates selected flag for chosen queries

4. **Source Discovery** - After web search completes
   - All unique sources found
   - AI quality scores (if Quality/Premium mode)
   - Which query found each source

5. **Source Selection** - When you choose sources for PDF
   - Updates selected flag for chosen sources

6. **Session Completion** - After PDF is successfully generated
   - Marks session as completed

### What Gets Tracked

**For Every Session:**
- Topic researched
- Date and time
- Configuration: # queries, results per query, max sources
- AI settings: enhancement level, query focus, quality threshold
- Which queries were generated and used
- Which sources were found and included
- AI quality assessment for each source

## Benefits of the Database

### 1. Research History
- Never lose track of past research
- Review what you've already researched
- Avoid duplicate research efforts

### 2. Quality Learning
- See which sources consistently score high
- Identify authoritative domains for topics
- Build a curated list of trusted sources

### 3. Topic Insights
- Track your research interests over time
- See which topics you research most
- Find gaps in your knowledge base

### 4. Configuration Optimization
- Compare different AI enhancement levels
- See impact of different quality thresholds
- Optimize search parameters based on past results

### 5. Source Reuse
- Quickly find sources used in past research
- Identify frequently selected URLs
- Build a personal research library

## Database Functions (For Developers)

The `database.py` module provides these helper functions:

```python
# Session management
session_id = save_session_start(topic, num_queries, ai_mode, ...)
mark_session_complete(session_id)

# Data storage
save_queries(session_id, queries, selected_queries)
save_sources(session_id, sources, selected_urls)

# Data retrieval
sessions = get_recent_sessions(limit=20)
session = get_session_details(session_id)
stats = get_research_stats()
favorites = get_favorite_sources(min_selections=2)
results = search_history(query)
```

## Privacy and Data Management

### Local Storage Only
- All data is stored locally on your computer
- No data is sent to external services (except OpenAI API for AI features)
- Database file is yours to keep, backup, or delete

### Data Size
- Very efficient storage (< 1MB for hundreds of sessions)
- No storage limits
- Automatic indexing for fast queries

### Backup and Export
- Copy `research_memory.db` to backup
- Move to another computer (database is portable)
- Query directly with any SQLite browser tool

### Delete Data
- Delete specific sessions through the UI (future feature)
- Delete entire database: `rm research_memory.db`
- Database will recreate on next run

## Future Enhancements (Planned)

### Short-term:
- Search functionality in history
- Filter by topic, date, AI mode
- Export session data to JSON/CSV
- Delete individual sessions

### Medium-term:
- AI-powered research suggestions based on history
- Automatic topic clustering
- Source recommendation engine
- Trend analysis over time

### Long-term:
- Vector embeddings for semantic search
- Research pattern recognition
- Automatic query optimization based on history
- Collaborative research (multi-user support)

## Technical Details

### Database Connection
- Uses Python's built-in `sqlite3` module
- Context manager pattern for safe connections
- Automatic commit/rollback on success/error
- Row factory for dictionary-like access

### Performance
- Indexed columns for fast queries
- Efficient JOIN operations
- Minimal overhead (< 100ms per save)
- No impact on research speed

### Error Handling
- Graceful degradation if database fails
- Research continues even if save fails
- Database errors logged to terminal
- Automatic retry on connection issues

## Getting Started

The database is automatically integrated and requires no setup!

1. **Start the app** - Database initializes automatically
2. **Do research** - Everything is saved as you work
3. **View history** - Click "View History" on homepage
4. **Explore analytics** - Click "Analytics" to see insights

## Example Use Cases

### Academic Researcher
- Track research on multiple paper topics
- Build bibliography of authoritative sources
- Compare different search strategies
- Export source lists for citations

### Student
- Organize research for multiple assignments
- Track which sources were most useful
- Review research before exams
- Build personal knowledge base

### Content Creator
- Research multiple article topics
- Find reliable sources consistently
- Track research time and efficiency
- Build content strategy based on data

### Analyst
- Deep dive on specific topics
- Cross-reference multiple research sessions
- Identify information gaps
- Generate research reports

## Support

For issues or questions:
- Check terminal output for database logs
- Database file: `research_memory.db`
- Error messages include full stack traces
- Database schema in `database.py`

---

**Database Status**: ✅ Fully Integrated and Operational

The SQLite database integration is complete and ready to use. Every research session is now automatically saved, tracked, and available for future reference and analysis.
