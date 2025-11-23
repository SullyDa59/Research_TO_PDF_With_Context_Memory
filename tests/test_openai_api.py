"""
Quick test script to verify OpenAI API key is working
"""
import os
from openai import OpenAI

def test_openai_api():
    """Test OpenAI API connection and quota"""
    
    # Check if API key is set
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable is not set")
        return False
    
    print(f"✓ API key found (starts with: {api_key[:10]}...)")
    
    # Try to make a minimal API call
    try:
        client = OpenAI(api_key=api_key)
        
        print("\n🔍 Testing API connection with minimal request...")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cheapest model
            messages=[{"role": "user", "content": "Say 'test'"}],
            max_tokens=5
        )
        
        result = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        
        print(f"✅ API Connection Successful!")
        print(f"   Response: {result}")
        print(f"   Tokens used: {tokens_used}")
        print(f"   Model: {response.model}")
        
        # Test with a slightly larger request
        print("\n🔍 Testing with slightly larger request...")
        
        response2 = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "What is 2+2? Answer in one word."}],
            max_tokens=10
        )
        
        result2 = response2.choices[0].message.content
        tokens_used2 = response2.usage.total_tokens
        cost = (tokens_used2 / 1_000_000) * 0.15  # gpt-4o-mini pricing
        
        print(f"✅ Second Test Successful!")
        print(f"   Response: {result2}")
        print(f"   Tokens used: {tokens_used2}")
        print(f"   Estimated cost: ${cost:.6f}")
        
        print("\n" + "="*60)
        print("✅ OpenAI API is working correctly!")
        print("="*60)
        print("\nYour API key has quota and is functional.")
        print("If you're getting quota errors in the app, it might be:")
        print("  1. Quota was exhausted after this test")
        print("  2. Different quota limits for different models")
        print("  3. Rate limiting (too many requests)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ API Test Failed!")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        
        if "insufficient_quota" in str(e):
            print("\n⚠️  QUOTA ISSUE DETECTED")
            print("Your OpenAI account has insufficient quota/credits.")
            print("\nTo fix:")
            print("1. Visit: https://platform.openai.com/account/billing")
            print("2. Add credits to your account")
            print("3. Wait a few minutes and try again")
        elif "invalid_api_key" in str(e):
            print("\n⚠️  INVALID API KEY")
            print("Your API key appears to be invalid.")
            print("Check that OPENAI_API_KEY is set correctly.")
        
        return False

if __name__ == "__main__":
    print("="*60)
    print("OpenAI API Connection Test")
    print("="*60)
    test_openai_api()
