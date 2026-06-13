import asyncio
import json
import os
import httpx
from dotenv import load_dotenv

load_dotenv(override=True)

SPLUNK_HOST = os.getenv("SPLUNK_HOST")
USERNAME = os.getenv("SPLUNK_USERNAME")
PASSWORD = os.getenv("SPLUNK_PASSWORD")
MCP_TOKEN = os.getenv("MCP_TOKEN")
MCP_URL = f"https://{SPLUNK_HOST}/en-US/splunkd/__raw/services/mcp"

async def test_mcp():
    print(f"[*] Initializing connection to the Splunk MCP Server at {MCP_URL}")
    
    async with httpx.AsyncClient(verify=False) as client:
        # Step 1: Login via Web Proxy
        login_url = f"https://{SPLUNK_HOST}/en-US/account/login"
        await client.get(login_url)
        cval = client.cookies.get("cval", "")
        
        payload = {"username": USERNAME, "password": PASSWORD, "cval": cval}
        await client.post(login_url, data=payload)
        
        csrf = ""
        for name, value in client.cookies.items():
            if "csrf" in name.lower():
                csrf = value
                
        print("[+] Authenticated via Splunk Web Proxy")
        
        # Step 2: Prepare JSON-RPC request for run_splunk_query
        mcp_headers = {
            "X-Splunk-Form-Key": csrf,
            "X-Requested-With": "XMLHttpRequest",
            "Authorization": f"Bearer {MCP_TOKEN}",
            "Content-Type": "application/json"
        }
        
        query = "search index=main | head 100 | eval metric=1 | fit DensityFunction metric into demo_model"
        
        rpc_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "run_splunk_query",
                "arguments": {
                    "query": query
                }
            }
        }
        
        print(f"[*] Executing native DensityFunction anomaly detection via MCP tool 'run_splunk_query'...")
        print(f"[*] Query: {query}")
        
        response = await client.post(MCP_URL, headers=mcp_headers, json=rpc_payload, timeout=60.0)
        
        print(f"\n[HTTP Status Code] {response.status_code}")
        
        try:
            data = response.json()
            print("\n[JSON-RPC Response]")
            print(json.dumps(data, indent=2))
        except Exception as e:
            print("\n[Raw Response]")
            print(response.text)

if __name__ == "__main__":
    asyncio.run(test_mcp())
