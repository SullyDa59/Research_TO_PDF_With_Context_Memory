#!/usr/bin/env python3
"""
Check OpenAI usage and verify API calls are being made
"""
import os
from openai import OpenAI

# Check API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("❌ ERROR: OPENAI_API_KEY not set")
    exit(1)

print("=" * 60)
print("OpenAI Account & Usage Check")
print("=" * 60)

print(f"\n1. API Key Status:")
print(f"   ✓ API key is set")
print(f"   ✓ Key starts with: {OPENAI_API_KEY[:20]}...")
print(f"   ✓ Key length: {len(OPENAI_API_KEY)} characters")

# Initialize client
client = OpenAI(api_key=OPENAI_API_KEY)

print(f"\n2. Testing API Connection:")
try:
    # Make a minimal API call
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Say 'test'"}
        ],
        max_tokens=5
    )

    print(f"   ✓ API call successful!")
    print(f"   ✓ Model: {response.model}")
    print(f"   ✓ Tokens used: {response.usage.total_tokens}")
    print(f"     - Input: {response.usage.prompt_tokens}")
    print(f"     - Output: {response.usage.completion_tokens}")

    # Calculate cost
    input_cost = response.usage.prompt_tokens * 0.00015 / 1000
    output_cost = response.usage.completion_tokens * 0.0006 / 1000
    total_cost = input_cost + output_cost

    print(f"\n3. Cost for this test:")
    print(f"   Input cost: ${input_cost:.6f}")
    print(f"   Output cost: ${output_cost:.6f}")
    print(f"   Total: ${total_cost:.6f}")

    print(f"\n4. Where to check usage:")
    print(f"   → Go to: https://platform.openai.com/usage")
    print(f"   → Select today's date")
    print(f"   → Look for model: gpt-4o-mini")
    print(f"   → You should see at least {response.usage.total_tokens} tokens")

    print(f"\n5. Why you might not see it:")
    print(f"   • Dashboard updates can take 5-30 minutes")
    print(f"   • Very small amounts (<$0.01) may not display immediately")
    print(f"   • Usage might be grouped hourly or daily")
    print(f"   • Check 'Costs' tab instead of 'Usage' tab")

    print(f"\n6. Current token usage from THIS test:")
    print(f"   {response.usage.total_tokens} tokens = ${total_cost:.6f}")
    print(f"   (This should appear in your dashboard within 30 minutes)")

except Exception as e:
    print(f"   ❌ API call failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("✅ Your OpenAI API is working correctly")
print("=" * 60)
print("\nIf you still don't see usage after 30 minutes:")
print("1. Make sure you're logged into the correct OpenAI account")
print("2. Check if your API key belongs to a different organization")
print("3. Visit: https://platform.openai.com/settings/organization")
