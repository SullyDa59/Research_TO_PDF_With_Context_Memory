"""
Memory Layer using Mem0
Provides intelligent semantic memory for the research application
with comprehensive tracking and monitoring
"""
import os
import json
from datetime import datetime
from urllib.parse import urlparse
from mem0 import Memory
import sqlite3

# Base directory for data storage
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Mem0 usage tracking database
TRACKING_DB = os.path.join(DATA_DIR, 'mem0_usage_tracking.db')

# Initialize mem0 with local Qdrant vector store
config = {
    "version": "v1.1",
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "research_memory",
            "path": os.path.join(DATA_DIR, "research_memory_vectors"),  # Local storage
            "on_disk": True  # Store on disk for persistence
        }
    },
    "llm": {
        "provider": "openai",
        "config": {
            "model": "gpt-4o-mini",
            "temperature": 0.1,
            "max_tokens": 500
        }
    },
    "embedder": {
        "provider": "openai",
        "config": {
            "model": "text-embedding-3-small"
        }
    }
}

# Initialize memory
try:
    memory = Memory.from_config(config)
    print("✓ Mem0 initialized successfully")
except Exception as e:
    print(f"⚠️  Mem0 initialization warning: {e}")
    memory = None

# ============================================================================
# USAGE TRACKING SYSTEM
# ============================================================================

def init_tracking_db():
    """Initialize usage tracking database"""
    conn = sqlite3.connect(TRACKING_DB)
    cursor = conn.cursor()

    # Track all mem0 operations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mem0_operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            operation_type TEXT NOT NULL,
            user_id TEXT,
            memory_id TEXT,
            tokens_used INTEGER,
            embedding_tokens INTEGER,
            llm_tokens INTEGER,
            estimated_cost REAL,
            latency_ms INTEGER,
            success BOOLEAN DEFAULT 1,
            error_message TEXT,
            metadata TEXT
        )
    """)

    # Track memory statistics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mem0_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            total_operations INTEGER DEFAULT 0,
            total_memories INTEGER DEFAULT 0,
            total_searches INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            total_cost REAL DEFAULT 0.0,
            avg_latency_ms REAL DEFAULT 0.0,
            success_rate REAL DEFAULT 1.0
        )
    """)

    # Persistent contexts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS persistent_contexts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            context_text TEXT NOT NULL,
            context_type TEXT DEFAULT 'general',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            active BOOLEAN DEFAULT 1
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ops_timestamp ON mem0_operations(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ops_user ON mem0_operations(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ops_type ON mem0_operations(operation_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stats_date ON mem0_stats(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contexts_user ON persistent_contexts(user_id)")

    conn.commit()
    conn.close()
    print("✓ Mem0 tracking database initialized")

# Initialize tracking on module load
init_tracking_db()

def track_operation(operation_type, user_id, tokens_used=0, embedding_tokens=0,
                   llm_tokens=0, latency_ms=0, success=True, error_message=None,
                   memory_id=None, metadata=None):
    """Track a mem0 operation for monitoring and cost analysis"""
    # Calculate estimated cost
    # OpenAI pricing: text-embedding-3-small = $0.02/1M tokens, gpt-4o-mini = $0.15/1M input
    embedding_cost = (embedding_tokens / 1_000_000) * 0.02
    llm_cost = (llm_tokens / 1_000_000) * 0.15
    total_cost = embedding_cost + llm_cost

    conn = sqlite3.connect(TRACKING_DB)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO mem0_operations
        (operation_type, user_id, memory_id, tokens_used, embedding_tokens, llm_tokens,
         estimated_cost, latency_ms, success, error_message, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (operation_type, user_id, memory_id, tokens_used, embedding_tokens, llm_tokens,
          total_cost, latency_ms, success, error_message,
          json.dumps(metadata) if metadata else None))

    conn.commit()
    conn.close()

    # Update daily stats
    update_daily_stats()

def update_daily_stats():
    """Update aggregated daily statistics"""
    conn = sqlite3.connect(TRACKING_DB)
    cursor = conn.cursor()

    today = datetime.now().date()

    # Get today's stats
    cursor.execute("""
        SELECT
            COUNT(*) as total_ops,
            SUM(CASE WHEN operation_type = 'add' THEN 1 ELSE 0 END) as total_memories,
            SUM(CASE WHEN operation_type = 'search' THEN 1 ELSE 0 END) as total_searches,
            SUM(tokens_used) as total_tokens,
            SUM(estimated_cost) as total_cost,
            AVG(latency_ms) as avg_latency,
            AVG(CAST(success AS REAL)) as success_rate
        FROM mem0_operations
        WHERE DATE(timestamp) = ?
    """, (today,))

    stats = cursor.fetchone()

    # Upsert stats
    cursor.execute("""
        INSERT OR REPLACE INTO mem0_stats
        (date, total_operations, total_memories, total_searches, total_tokens,
         total_cost, avg_latency_ms, success_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (today, stats[0], stats[1], stats[2], stats[3], stats[4], stats[5], stats[6]))

    conn.commit()
    conn.close()

# ============================================================================
# CORE MEMORY FUNCTIONS
# ============================================================================

def extract_domain(url):
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return url

def add_research_memory(user_id, session_data):
    """Add a completed research session to memory"""
    if not memory:
        return None

    start_time = datetime.now()

    try:
        # Create rich memory text
        memory_text = f"""
Research Session Completed:
Topic: {session_data['topic']}
AI Mode: {session_data.get('ai_mode', 'basic')}
Query Focus: {session_data.get('query_focus', 'balanced')}
Queries Generated: {session_data.get('num_queries', 0)}
Sources Found: {session_data.get('total_sources', 0)}
Sources Selected: {session_data.get('selected_sources', 0)}
Top Queries Used: {', '.join(session_data.get('top_queries', [])[:3])}
Quality Threshold: {session_data.get('min_quality_score', 'N/A')}
Date: {session_data.get('date', datetime.now().isoformat())}
        """.strip()

        # Add to mem0
        result = memory.add(
            messages=memory_text,
            user_id=user_id,
            metadata={
                "type": "research_session",
                "topic": session_data['topic'],
                "date": session_data.get('date', datetime.now().isoformat()),
                "ai_mode": session_data.get('ai_mode'),
                "session_id": session_data.get('session_id')
            }
        )

        # Track operation
        latency = (datetime.now() - start_time).total_seconds() * 1000
        track_operation(
            operation_type="add",
            user_id=user_id,
            tokens_used=len(memory_text.split()),  # Rough estimate
            embedding_tokens=len(memory_text.split()),
            llm_tokens=0,
            latency_ms=int(latency),
            success=True,
            memory_id=result.get('id') if isinstance(result, dict) else None,
            metadata={
                "topic": session_data['topic'],
                "type": "research_session"
            }
        )

        print(f"✓ Added research session to mem0 (topic: {session_data['topic'][:50]}...)")
        return result

    except Exception as e:
        latency = (datetime.now() - start_time).total_seconds() * 1000
        track_operation(
            operation_type="add",
            user_id=user_id,
            latency_ms=int(latency),
            success=False,
            error_message=str(e),
            metadata={"topic": session_data.get('topic')}
        )
        print(f"⚠️  Failed to add to mem0: {e}")
        return None

def add_source_preference(user_id, source, action, topic):
    """Track when user selects or rejects a source"""
    if not memory:
        return None

    start_time = datetime.now()

    try:
        domain = extract_domain(source.get('url', ''))
        ai_score = source.get('ai_score') or source.get('relevance_score')

        memory_text = f"""
User {action} source: {source.get('title', 'Unknown')}
Domain: {domain}
URL: {source.get('url', '')}
For topic: {topic}
AI Quality Score: {ai_score if ai_score else 'N/A'}
Reasoning: {source.get('score_reasoning', 'N/A')}
        """.strip()

        result = memory.add(
            messages=memory_text,
            user_id=user_id,
            metadata={
                "type": "source_preference",
                "action": action,
                "domain": domain,
                "ai_score": ai_score,
                "topic": topic
            }
        )

        latency = (datetime.now() - start_time).total_seconds() * 1000
        track_operation(
            operation_type="add",
            user_id=user_id,
            tokens_used=len(memory_text.split()),
            embedding_tokens=len(memory_text.split()),
            llm_tokens=0,
            latency_ms=int(latency),
            success=True,
            memory_id=result.get('id') if isinstance(result, dict) else None,
            metadata={
                "action": action,
                "domain": domain,
                "type": "source_preference"
            }
        )

        return result

    except Exception as e:
        latency = (datetime.now() - start_time).total_seconds() * 1000
        track_operation(
            operation_type="add",
            user_id=user_id,
            latency_ms=int(latency),
            success=False,
            error_message=str(e)
        )
        print(f"⚠️  Failed to add source preference: {e}")
        return None

def search_memory(user_id, query, limit=10):
    """Search through user's memories semantically"""
    if not memory:
        return []

    start_time = datetime.now()

    try:
        results = memory.search(
            query=query,
            user_id=user_id,
            limit=limit
        )

        latency = (datetime.now() - start_time).total_seconds() * 1000
        track_operation(
            operation_type="search",
            user_id=user_id,
            tokens_used=len(query.split()),
            embedding_tokens=len(query.split()),
            llm_tokens=0,
            latency_ms=int(latency),
            success=True,
            metadata={
                "query": query,
                "results_count": len(results) if results else 0
            }
        )

        return results

    except Exception as e:
        latency = (datetime.now() - start_time).total_seconds() * 1000
        track_operation(
            operation_type="search",
            user_id=user_id,
            latency_ms=int(latency),
            success=False,
            error_message=str(e),
            metadata={"query": query}
        )
        print(f"⚠️  Memory search failed: {e}")
        return []

def get_all_memories(user_id, limit=100):
    """Get all memories for a user"""
    if not memory:
        return []

    start_time = datetime.now()

    try:
        results = memory.get_all(user_id=user_id, limit=limit)

        latency = (datetime.now() - start_time).total_seconds() * 1000
        track_operation(
            operation_type="get_all",
            user_id=user_id,
            latency_ms=int(latency),
            success=True,
            metadata={"results_count": len(results) if results else 0}
        )

        return results

    except Exception as e:
        latency = (datetime.now() - start_time).total_seconds() * 1000
        track_operation(
            operation_type="get_all",
            user_id=user_id,
            latency_ms=int(latency),
            success=False,
            error_message=str(e)
        )
        print(f"⚠️  Failed to get memories: {e}")
        return []

def get_user_preferences(user_id):
    """Extract learned user preferences from memories"""
    if not memory:
        return {
            "preferred_domains": [],
            "ai_modes": [],
            "query_focuses": [],
            "topics": []
        }

    try:
        memories = get_all_memories(user_id, limit=200)

        preferences = {
            "preferred_domains": [],
            "rejected_domains": [],
            "ai_modes": [],
            "query_focuses": [],
            "topics": [],
            "avg_quality_threshold": None
        }

        domain_counts = {}
        rejected_domains = {}
        ai_mode_counts = {}
        focus_counts = {}
        topic_counts = {}

        for mem in memories:
            metadata = mem.get('metadata', {})

            if metadata.get('type') == 'source_preference':
                domain = metadata.get('domain')
                action = metadata.get('action')

                if domain:
                    if action == 'selected':
                        domain_counts[domain] = domain_counts.get(domain, 0) + 1
                    elif action == 'rejected':
                        rejected_domains[domain] = rejected_domains.get(domain, 0) + 1

            elif metadata.get('type') == 'research_session':
                ai_mode = metadata.get('ai_mode')
                if ai_mode:
                    ai_mode_counts[ai_mode] = ai_mode_counts.get(ai_mode, 0) + 1

                topic = metadata.get('topic')
                if topic:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # Sort and extract top preferences
        preferences['preferred_domains'] = sorted(domain_counts.items(),
                                                 key=lambda x: x[1], reverse=True)[:10]
        preferences['rejected_domains'] = sorted(rejected_domains.items(),
                                                key=lambda x: x[1], reverse=True)[:10]
        preferences['ai_modes'] = sorted(ai_mode_counts.items(),
                                        key=lambda x: x[1], reverse=True)
        preferences['topics'] = sorted(topic_counts.items(),
                                      key=lambda x: x[1], reverse=True)[:10]

        return preferences

    except Exception as e:
        print(f"⚠️  Failed to get user preferences: {e}")
        return {
            "preferred_domains": [],
            "rejected_domains": [],
            "ai_modes": [],
            "query_focuses": [],
            "topics": []
        }

# ============================================================================
# PERSISTENT CONTEXT MANAGEMENT
# ============================================================================

def add_persistent_context(user_id, context_text, context_type='general'):
    """
    Add persistent context that will be injected into all AI queries

    Args:
        user_id: User identifier
        context_text: The context text to add
        context_type: Type of context (general, preference, instruction, fact)

    Returns:
        context_id if successful, None otherwise
    """
    if not context_text or not context_text.strip():
        return None

    conn = sqlite3.connect(TRACKING_DB)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO persistent_contexts (user_id, context_text, context_type)
            VALUES (?, ?, ?)
        """, (user_id, context_text.strip(), context_type))

        context_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"✓ Added persistent context for user {user_id} (type: {context_type})")
        return context_id

    except Exception as e:
        conn.close()
        print(f"⚠️  Failed to add persistent context: {e}")
        return None

def get_persistent_contexts(user_id):
    """
    Get all active persistent contexts for a user

    Args:
        user_id: User identifier

    Returns:
        List of context dictionaries
    """
    conn = sqlite3.connect(TRACKING_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, context_text, context_type, created_at
        FROM persistent_contexts
        WHERE user_id = ? AND active = 1
        ORDER BY created_at DESC
    """, (user_id,))

    contexts = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return contexts

def remove_persistent_context(user_id, context_id):
    """
    Remove a persistent context (marks as inactive)

    Args:
        user_id: User identifier
        context_id: Context ID to remove

    Returns:
        True if successful, False otherwise
    """
    conn = sqlite3.connect(TRACKING_DB)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE persistent_contexts
            SET active = 0
            WHERE id = ? AND user_id = ?
        """, (context_id, user_id))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if success:
            print(f"✓ Removed persistent context {context_id} for user {user_id}")
        else:
            print(f"⚠️  Context {context_id} not found or already removed")

        return success

    except Exception as e:
        conn.close()
        print(f"⚠️  Failed to remove persistent context: {e}")
        return False

def clear_all_persistent_contexts(user_id):
    """
    Clear all persistent contexts for a user

    Args:
        user_id: User identifier

    Returns:
        Number of contexts cleared
    """
    conn = sqlite3.connect(TRACKING_DB)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE persistent_contexts
            SET active = 0
            WHERE user_id = ? AND active = 1
        """, (user_id,))

        count = cursor.rowcount
        conn.commit()
        conn.close()

        print(f"✓ Cleared {count} persistent contexts for user {user_id}")
        return count

    except Exception as e:
        conn.close()
        print(f"⚠️  Failed to clear persistent contexts: {e}")
        return 0

def add_manual_memory(user_id, memory_text, memory_type='manual', metadata=None):
    """
    Manually add a memory to the user's mem0 store

    Args:
        user_id: User identifier
        memory_text: The memory text to add
        memory_type: Type of memory (manual, note, fact, etc.)
        metadata: Optional metadata dictionary

    Returns:
        Memory result if successful, None otherwise
    """
    if not memory:
        return None

    if not memory_text or not memory_text.strip():
        return None

    start_time = datetime.now()

    try:
        # Prepare metadata
        mem_metadata = {
            "type": memory_type,
            "manually_added": True,
            "date": datetime.now().isoformat()
        }
        if metadata:
            mem_metadata.update(metadata)

        # Add to mem0
        result = memory.add(
            messages=memory_text.strip(),
            user_id=user_id,
            metadata=mem_metadata
        )

        # Track operation
        latency = (datetime.now() - start_time).total_seconds() * 1000
        track_operation(
            operation_type="add",
            user_id=user_id,
            tokens_used=len(memory_text.split()),
            embedding_tokens=len(memory_text.split()),
            llm_tokens=0,
            latency_ms=int(latency),
            success=True,
            memory_id=result.get('id') if isinstance(result, dict) else None,
            metadata={
                "type": memory_type,
                "manually_added": True
            }
        )

        print(f"✓ Added manual memory for user {user_id} (type: {memory_type})")
        return result

    except Exception as e:
        latency = (datetime.now() - start_time).total_seconds() * 1000
        track_operation(
            operation_type="add",
            user_id=user_id,
            latency_ms=int(latency),
            success=False,
            error_message=str(e),
            metadata={"type": memory_type, "manually_added": True}
        )
        print(f"⚠️  Failed to add manual memory: {e}")
        return None

def get_persistent_context_summary(user_id):
    """
    Get a formatted string of all persistent contexts for injection into AI prompts

    Args:
        user_id: User identifier

    Returns:
        Formatted context string
    """
    contexts = get_persistent_contexts(user_id)

    if not contexts:
        return ""

    context_str = "User's Persistent Context:\n"
    for ctx in contexts:
        context_str += f"- [{ctx['context_type']}] {ctx['context_text']}\n"

    return context_str

# ============================================================================
# MONITORING & ANALYTICS FUNCTIONS
# ============================================================================

def get_usage_stats(days=7):
    """Get mem0 usage statistics for the last N days"""
    conn = sqlite3.connect(TRACKING_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            date,
            total_operations,
            total_memories,
            total_searches,
            total_tokens,
            total_cost,
            avg_latency_ms,
            success_rate
        FROM mem0_stats
        WHERE date >= date('now', '-' || ? || ' days')
        ORDER BY date DESC
    """, (days,))

    stats = cursor.fetchall()
    conn.close()

    return [{
        'date': row[0],
        'operations': row[1],
        'memories': row[2],
        'searches': row[3],
        'tokens': row[4],
        'cost': row[5],
        'latency_ms': row[6],
        'success_rate': row[7]
    } for row in stats]

def get_total_stats():
    """Get total cumulative stats"""
    conn = sqlite3.connect(TRACKING_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) as total_ops,
            SUM(CASE WHEN operation_type = 'add' THEN 1 ELSE 0 END) as total_adds,
            SUM(CASE WHEN operation_type = 'search' THEN 1 ELSE 0 END) as total_searches,
            SUM(tokens_used) as total_tokens,
            SUM(estimated_cost) as total_cost,
            AVG(latency_ms) as avg_latency,
            AVG(CAST(success AS REAL)) * 100 as success_rate
        FROM mem0_operations
    """)

    row = cursor.fetchone()
    conn.close()

    return {
        'total_operations': row[0] or 0,
        'total_adds': row[1] or 0,
        'total_searches': row[2] or 0,
        'total_tokens': row[3] or 0,
        'total_cost': row[4] or 0.0,
        'avg_latency_ms': row[5] or 0.0,
        'success_rate': row[6] or 100.0
    }

def get_recent_operations(limit=50):
    """Get recent mem0 operations for debugging"""
    conn = sqlite3.connect(TRACKING_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM mem0_operations
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))

    operations = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return operations

def get_cost_breakdown():
    """Get detailed cost breakdown"""
    conn = sqlite3.connect(TRACKING_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            operation_type,
            COUNT(*) as count,
            SUM(embedding_tokens) as total_embedding_tokens,
            SUM(llm_tokens) as total_llm_tokens,
            SUM(estimated_cost) as total_cost
        FROM mem0_operations
        GROUP BY operation_type
        ORDER BY total_cost DESC
    """)

    breakdown = cursor.fetchall()
    conn.close()

    return [{
        'operation': row[0],
        'count': row[1],
        'embedding_tokens': row[2] or 0,
        'llm_tokens': row[3] or 0,
        'cost': row[4] or 0.0
    } for row in breakdown]

print("✓ Memory layer module loaded successfully")
