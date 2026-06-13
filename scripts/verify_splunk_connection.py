import os
import asyncio
import traceback
from dotenv import load_dotenv

# Force DEMO_MODE=false for this test
os.environ["DEMO_MODE"] = "false"
load_dotenv(override=True)

from src.splunk.search_client import SearchClient
from src.utils.config import settings

settings.DEMO_MODE = False

async def run_tests():
    print(f"=== SPLUNK CLOUD INTEGRATION TEST ===")
    print(f"Host: {os.getenv('SPLUNK_HOST')}")
    print(f"Username: {os.getenv('SPLUNK_USERNAME')}")
    
    client = SearchClient()
    
    print("\n--- 1. Testing Real SPL Search (via Proxy) ---")
    try:
        results = await client.execute_search("search index=_internal | head 1")
        print("✅ SUCCESS: Real SPL search executed.")
        print(f"Results: {results}")
    except Exception as e:
        print(f"❌ FAILED: SPL search error: {e}")
        traceback.print_exc()

    print("\n--- 2. Testing CDTSM (| apply cdtsm) ---")
    try:
        results = await client.execute_search("| makeresults | eval _time=now(), value=1 | apply cisco_ai_assistant")
        print("✅ SUCCESS: CDTSM model executed.")
        print(f"Results: {results}")
    except Exception as e:
        print(f"❌ FAILED: CDTSM error: {e}")

    print("\n--- 3. Testing Foundation AI ---")
    try:
        results = await client.execute_search(f"| makeresults | eval prompt=\"Hello\" | apply {os.getenv('FOUNDATION_AI_MODEL', 'foundation-sec-1.1-8b-instruct')}")
        print("✅ SUCCESS: Foundation AI executed.")
        print(f"Results: {results}")
    except Exception as e:
        print(f"❌ FAILED: Foundation AI error: {e}")

    print("\n--- Testing HEC Write (port 8088) ---")
    try:
        success = await client.write_event(
            event_data={"message": "TRIDENT-AI real HEC integration test via Python"},
            index="main",
            sourcetype="trident:json"
        )
        if success:
            print("✅ SUCCESS: HEC write executed and returned True.")
        else:
            print("❌ FAILED: HEC write returned False.")
    except Exception as e:
        print(f"❌ FAILED: HEC write error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_tests())
