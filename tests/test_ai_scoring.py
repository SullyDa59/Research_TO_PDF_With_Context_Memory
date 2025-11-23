#!/usr/bin/env python3
"""
Test script to debug AI scoring functionality
"""
import os
from research_to_pdf import score_result_relevance, filter_results_by_quality

# Test with a simple example
topic = "quantum computing"
test_results = [
    {"title": "Quantum Computing Basics - MIT", "url": "https://mit.edu/quantum"},
    {"title": "Introduction to Quantum", "url": "https://example.com/quantum"},
    {"title": "Buy Quantum Computers!", "url": "https://spam.com/buy"}
]

print("=" * 60)
print("Testing AI Scoring Function")
print("=" * 60)

print(f"\nTopic: {topic}")
print(f"Testing {len(test_results)} sources\n")

# Test individual scoring
print("1. Testing individual score_result_relevance()...")
for i, result in enumerate(test_results, 1):
    print(f"\n[{i}] {result['title']}")
    try:
        score_data = score_result_relevance(topic, result['title'], result['url'])
        print(f"    Score: {score_data['score']}/100")
        print(f"    Reasoning: {score_data['reasoning']}")
    except Exception as e:
        print(f"    ERROR: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print("2. Testing filter_results_by_quality()...")
print("=" * 60)

try:
    filtered = filter_results_by_quality(topic, test_results, min_score=60, max_to_score=3)
    print(f"\nFiltered results: {len(filtered)}")
    for result in filtered:
        score = result.get('relevance_score', 'N/A')
        print(f"  - [{score}] {result['title']}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ Test complete!")
print("=" * 60)
