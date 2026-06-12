import os
import asyncio
import traceback
from dotenv import load_dotenv

# Force DEMO_MODE=false for this test
os.environ["DEMO_MODE"] = "false"
load_dotenv(override=True)

from src.splunk.search_client import SearchClient

async def run_tests():
    print(f"=== SPLUNK CLOUD INTEGRATION TEST ===")
    print(f"Host: {os.getenv('SPLUNK_HOST')}")
    print(f"Username: {os.getenv('SPLUNK_USERNAME')}")
    
    client = SearchClient()
    
    print("\n--- 1. Testing Real SPL Search ---")
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
        print(f"❌ FAILED (EXPECTED IF ON TRIAL): CDTSM error: {e}")

    print("\n--- 3. Testing Foundation AI ---")
    try:
        results = await client.execute_search(f"| makeresults | eval prompt=\"Hello\" | apply {os.getenv('FOUNDATION_AI_MODEL', 'foundation-sec-1.1-8b-instruct')}")
        print("✅ SUCCESS: Foundation AI executed.")
        print(f"Results: {results}")
    except Exception as e:
        print(f"❌ FAILED (EXPECTED IF ON TRIAL): Foundation AI error: {e}")

    print("\n--- 4. Testing MCP tools/list ---")
    try:
        import httpx
        mcp_url = os.getenv("MCP_BASE_URL", "").replace("/mcp", "/mcp/tools/list")
        if not mcp_url:
            mcp_url = f"https://{os.getenv('SPLUNK_HOST')}:{os.getenv('SPLUNK_PORT')}/services/mcp/tools/list"
            
        print(f"GET {mcp_url}")
        
        # Use auth
        username = os.getenv("SPLUNK_USERNAME")
        password = os.getenv("SPLUNK_PASSWORD")
        token = os.getenv("SPLUNK_TOKEN")
        
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
            auth = None
        else:
            auth = (username, password)
            
        async with httpx.AsyncClient(verify=False) as http:
            resp = await http.get(mcp_url, headers=headers, auth=auth, timeout=10)
            print(f"Status Code: {resp.status_code}")
            if resp.status_code == 200:
                print("✅ SUCCESS: MCP tools/list executed.")
                print(f"Results: {resp.text[:200]}...")
            else:
                print(f"❌ FAILED: MCP HTTP {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ FAILED: MCP request error: {e}")
        traceback.print_exc()

    print("\n--- 5. Testing HEC Write (port 8088) ---")
    try:
        success = await client.write_event(
            event_data={"message": "TRIDENT-AI real HEC integration test"},
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
