"""
Comprehensive test of all Flask routes via HTTP requests
"""
import requests
import time

BASE_URL = "http://localhost:5001"

def test_route(name, url, method="GET", data=None):
    """Test a single route"""
    print(f"\n📍 Testing: {name}")
    print(f"   URL: {url}")
    print(f"   Method: {method}")

    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, data=data, timeout=10)

        status = response.status_code
        if status == 200:
            print(f"   ✅ Status: {status} OK")
            return True
        elif status in [302, 301]:  # Redirect
            print(f"   ⚠️  Status: {status} Redirect")
            return True
        else:
            print(f"   ❌ Status: {status}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection Error - Server not running?")
        return False
    except requests.exceptions.Timeout:
        print(f"   ❌ Timeout")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("="*70)
    print("🧪 Comprehensive Flask Route Testing")
    print("="*70)
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    routes = [
        # Main routes
        ("Homepage", "/", "GET"),
        ("History", "/history", "GET"),

        # Mem0 routes
        ("Mem0 Monitor", "/mem0-monitor", "GET"),
        ("Mem0 Context Management", "/mem0-context", "GET"),
        ("Mem0 Memories", "/mem0-memories", "GET"),
        ("Mem0 Preferences", "/mem0-preferences", "GET"),

        # Test adding persistent context (POST)
        ("Add Persistent Context", "/mem0-context", "POST", {
            "action": "add_context",
            "context_text": "Test context from automated testing",
            "context_type": "general"
        }),

        # Test adding manual memory (POST)
        ("Add Manual Memory", "/mem0-context", "POST", {
            "action": "add_memory",
            "memory_text": "Test memory from automated testing",
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

        full_url = f"{BASE_URL}{url}"
        success = test_route(name, full_url, method, data)
        results.append((name, success))

        time.sleep(0.5)  # Small delay between tests

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
    else:
        print(f"⚠️  {failed} test(s) failed")

if __name__ == "__main__":
    main()
