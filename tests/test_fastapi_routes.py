"""
Test FastAPI routes using TestClient
This replaces the HTTP-based test_all_routes.py for FastAPI
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', 'src'))

from fastapi.testclient import TestClient
from research_ui_fastapi import app
import time

client = TestClient(app)


def test_route(name, url, method="GET", data=None):
    """Test a single route"""
    print(f"\n📍 Testing: {name}")
    print(f"   URL: {url}")
    print(f"   Method: {method}")

    try:
        if method == "GET":
            response = client.get(url)
        elif method == "POST":
            response = client.post(url, data=data)

        status = response.status_code
        if status == 200:
            print(f"   ✅ Status: {status} OK")
            return True
        elif status in [302, 301, 303, 307]:  # Redirect
            print(f"   ⚠️  Status: {status} Redirect")
            return True
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    print("="*70)
    print("🧪 Comprehensive FastAPI Route Testing")
    print("="*70)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    routes = [
        # Main routes
        ("Homepage", "/", "GET"),
        ("History", "/history", "GET"),
        ("Analytics", "/analytics", "GET"),

        # Mem0 routes
        ("Mem0 Monitor", "/mem0-monitor", "GET"),
        ("Mem0 Context Management", "/mem0-context", "GET"),
        ("Mem0 Memories", "/mem0-memories", "GET"),
        ("Mem0 Preferences", "/mem0-preferences", "GET"),

        # Health check
        ("Health Check", "/health", "GET"),

        # OpenAPI docs
        ("API Docs", "/docs", "GET"),

        # Test POST routes
        ("Add Persistent Context", "/mem0-context", "POST", {
            "action": "add_context",
            "context_text": "Test context from FastAPI automated testing",
            "context_type": "general"
        }),

        ("Add Manual Memory", "/mem0-context", "POST", {
            "action": "add_memory",
            "memory_text": "Test memory from FastAPI automated testing",
            "memory_type": "manual"
        }),
    ]

    results = []
    for test_data in routes:
        if len(test_data) == 3:
            name, url, method = test_data
            data = None
        else:
            name, url, method, data = test_data

        success = test_route(name, url, method, data)
        results.append((name, success))

        time.sleep(0.1)  # Small delay between tests

    # Summary
    print("\n" + "="*70)
    print("📊 Test Results Summary")
    print("="*70)

    passed = 0
    failed = 0

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:12} {name}")
        if success:
            passed += 1
        else:
            failed += 1

    print("\n" + "="*70)
    print(f"Total: {passed} passed, {failed} failed out of {len(results)} tests")
    print("="*70)

    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
