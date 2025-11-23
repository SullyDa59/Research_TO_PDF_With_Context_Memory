# Research Project Enhancements

## Overview
This document details the comprehensive enhancements made to the Research to PDF Generator to provide more potential results and better OpenAI API queries.

## Key Improvements

### 1. Enhanced OpenAI Prompt Engineering
**Location:** `research_to_pdf.py:106-157` and `research_to_pdf.py:160-267`

**Changes:**
- Upgraded system prompt to be more comprehensive and specific
- Increased temperature from 0.7 to 0.8 for more diverse query generation
- Added max_tokens parameter (500-600) for fuller responses
- Enhanced query cleaning with regex to remove numbering and bullets
- Added detailed instructions for 7 different query types:
  - Academic/scholarly sources
  - Practical guides and tutorials
  - Recent developments (2024-2025)
  - Comprehensive overviews
  - Expert analysis
  - Technical documentation
  - Real-world applications

### 2. Increased Search Query Generation
**Location:** `research_ui_flask.py:245` (configurable)

**Changes:**
- Default increased from 3 queries to 7 queries
- Now configurable: 3, 5, 7, or 10 queries via UI
- Generates diverse queries covering different aspects of the topic

### 3. Multi-Query Search with Deduplication
**Location:** `research_ui_flask.py:322-353`

**Changes:**
- **BEFORE:** Only searched the first query
- **AFTER:** Searches across ALL generated queries
- Deduplicates results by URL to avoid redundancy
- Tracks which query found each source
- Configurable results per query (10, 20, 30, or 50)

### 4. Expanded Result Limits
**Location:** `research_ui_flask.py:326-327`, `research_ui_flask.py:352`

**Changes:**
- Results per query: Increased from 15 to 30 (configurable up to 50)
- Max total sources: Increased from 15 to 50 (configurable up to 100)
- Total potential results: Up to 500 sources (10 queries × 50 results)
- After deduplication: Up to 100 unique sources

### 5. Advanced Query Focus System
**Location:** `research_to_pdf.py:160-267`

**New Feature:** `generate_search_queries_advanced()` function

Supports 6 different research focus types:

#### Balanced (Default)
- Mix of all source types
- Comprehensive coverage

#### Academic Focus
- Research papers and peer-reviewed journals
- University publications
- Scholarly analysis
- Scientific studies
- Uses terms: research, study, paper, journal, academic, scholarly

#### Practical Focus
- Step-by-step tutorials
- Implementation examples
- Best practices
- Developer guides
- Uses terms: tutorial, guide, how to, example, implementation

#### Recent Focus
- News from 2024-2025
- Latest trends and breakthroughs
- Current state of the art
- Emerging technologies
- Uses terms: 2024, 2025, latest, recent, new, trends

#### Technical Focus
- Official documentation
- API references
- Technical specifications
- Architecture documents
- Uses terms: documentation, technical, specification, API, reference

#### Comprehensive Focus
- Complete guides
- Foundational concepts
- Overview articles
- Reference materials
- Uses terms: complete guide, overview, introduction, fundamentals

### 6. Configurable UI Parameters
**Location:** `research_ui_flask.py:214-273`

**New Controls:**
1. **Number of Search Queries**
   - Options: 3, 5, 7 (default), 10
   - More queries = more diverse sources

2. **Results per Query**
   - Options: 10, 20, 30 (default), 50
   - More results = better coverage

3. **Max Total Sources**
   - Options: 30, 50 (default), 75, 100
   - Controls final unique sources displayed

4. **Query Focus**
   - Options: Balanced, Academic, Practical, Recent, Technical, Comprehensive
   - Tailors queries to specific research needs

## Performance Comparison

### Before Enhancements
- 3 queries generated
- Only 1 query searched
- 15 results maximum
- Generic query generation
- No customization

### After Enhancements
- Up to 10 queries generated (default 7)
- ALL queries searched with deduplication
- Up to 100 unique sources (default 50)
- Highly targeted query generation with 6 focus types
- Fully configurable search parameters

## Expected Results Increase

### Quick Search (3 queries, 10 results each)
- Potential: ~30 sources
- After dedup: ~25-30 unique sources

### Balanced Search (7 queries, 30 results each - DEFAULT)
- Potential: ~210 sources
- After dedup: ~50-100 unique sources

### Exhaustive Search (10 queries, 50 results each)
- Potential: ~500 sources
- After dedup: ~100-200 unique sources

## Direct OpenAI API Improvements

### Enhanced Prompt Structure
```python
# BEFORE
prompt = f"""Topic: {topic}
Produce {num_queries} high-quality web search queries.
Focus on informative, in-depth sources like guides, research, and long-form articles."""

# AFTER
prompt = f"""Topic: {topic}
Generate {num_queries} diverse, high-quality web search queries that cover different aspects.

Your queries should include a mix of:
1. Academic/scholarly sources
2. Practical guides and tutorials
3. Recent developments (2024-2025)
4. Comprehensive overviews
5. Expert analysis
6. Technical documentation
7. Real-world applications

Each query should be:
- Specific and targeted to find authoritative sources
- Optimized for search engines
- Likely to return in-depth, long-form content
- Diverse enough to cover different facets"""
```

### Better System Message
```python
# BEFORE
"You are a research assistant that generates effective search queries."

# AFTER
"You are an expert research assistant specializing in generating highly effective,
diverse search queries that retrieve comprehensive information from multiple
authoritative sources across academic, practical, and industry domains."
```

### Higher Temperature for Diversity
```python
# BEFORE
temperature=0.7

# AFTER
temperature=0.8  # More creative and diverse queries
```

## Usage Examples

### Example 1: Academic Research
- Topic: "quantum computing"
- Focus: Academic
- Queries: 7
- Results/Query: 30
- Expected: 50+ unique scholarly sources

### Example 2: Practical Learning
- Topic: "machine learning"
- Focus: Practical
- Queries: 5
- Results/Query: 20
- Expected: 40+ tutorials and guides

### Example 3: Latest Trends
- Topic: "AI safety"
- Focus: Recent
- Queries: 7
- Results/Query: 30
- Expected: 50+ recent articles from 2024-2025

## Cost Implications

With GPT-4o-mini pricing (~$0.00015 per 1K input tokens, ~$0.0006 per 1K output tokens):

- **Before:** ~$0.0001 per research session
- **After (default 7 queries):** ~$0.0002 per research session
- **After (exhaustive 10 queries):** ~$0.0003 per research session

Still extremely affordable while providing 10-15x more potential sources!

## Files Modified

1. `research_to_pdf.py`
   - Enhanced `generate_search_queries()` function
   - Added `generate_search_queries_advanced()` function

2. `research_ui_flask.py`
   - Updated UI with configuration options
   - Modified `/generate_queries` route to accept parameters
   - Enhanced `/search_web` route to search all queries with deduplication
   - Updated port from 5000 to 5001

## Testing Recommendations

1. Try different query focuses for the same topic
2. Compare results between 3 queries vs 10 queries
3. Test with various topics (technical, academic, practical)
4. Monitor the diversity and quality of sources returned
5. Adjust parameters based on your specific research needs

## Future Enhancement Ideas

1. Add source quality ranking based on domain authority
2. Implement parallel query searching for faster results
3. Add filtering by date range
4. Include source type detection (PDF, blog, academic paper)
5. Add caching for repeated queries
6. Implement relevance scoring using embeddings
