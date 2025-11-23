"""
Test script to verify all Flask endpoints and functionality
"""
import memory_layer as mem

def test_manual_memory():
    """Test adding a manual memory"""
    print("\n" + "="*60)
    print("Testing Manual Memory Addition")
    print("="*60)

    user_id = "test_user"
    memory_text = "Test manual memory: PyTorch is a deep learning framework"
    memory_type = "fact"

    print(f"Adding manual memory for user: {user_id}")
    print(f"Memory text: {memory_text}")
    print(f"Memory type: {memory_type}")

    result = mem.add_manual_memory(user_id, memory_text, memory_type)

    if result:
        print(f"✅ Manual memory added successfully!")
        print(f"Result: {result}")
        return True
    else:
        print(f"❌ Failed to add manual memory")
        return False

def test_persistent_context():
    """Test adding and retrieving persistent context"""
    print("\n" + "="*60)
    print("Testing Persistent Context")
    print("="*60)

    user_id = "test_user"
    context_text = "I prefer academic papers over blog posts"
    context_type = "preference"

    print(f"Adding persistent context for user: {user_id}")
    print(f"Context: {context_text}")
    print(f"Type: {context_type}")

    context_id = mem.add_persistent_context(user_id, context_text, context_type)

    if context_id:
        print(f"✅ Persistent context added successfully! (ID: {context_id})")

        # Retrieve contexts
        print("\nRetrieving all persistent contexts...")
        contexts = mem.get_persistent_contexts(user_id)
        print(f"Found {len(contexts)} persistent contexts")
        for ctx in contexts:
            print(f"  - [{ctx['context_type']}] {ctx['context_text']}")

        # Test context summary
        print("\nGetting context summary...")
        summary = mem.get_persistent_context_summary(user_id)
        if summary:
            print("Context summary:")
            print(summary)

        return True
    else:
        print(f"❌ Failed to add persistent context")
        return False

def test_user_preferences():
    """Test get_user_preferences function"""
    print("\n" + "="*60)
    print("Testing User Preferences Retrieval")
    print("="*60)

    user_id = "test_user"

    print(f"Getting preferences for user: {user_id}")
    preferences = mem.get_user_preferences(user_id)

    print(f"\nPreferences retrieved:")
    print(f"  - Preferred domains: {len(preferences.get('preferred_domains', []))}")
    print(f"  - Rejected domains: {len(preferences.get('rejected_domains', []))}")
    print(f"  - AI modes: {len(preferences.get('ai_modes', []))}")
    print(f"  - Topics: {len(preferences.get('topics', []))}")

    return True

def main():
    print("="*60)
    print("🧪 Testing Flask Application Endpoints")
    print("="*60)

    tests = [
        ("Manual Memory", test_manual_memory),
        ("Persistent Context", test_persistent_context),
        ("User Preferences", test_user_preferences),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")

    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

if __name__ == "__main__":
    main()
