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
    async with httpx.AsyncClient(verify=False) as client:
        login_url = f"https://{SPLUNK_HOST}/en-US/account/login"
        await client.get(login_url)
        cval = client.cookies.get("cval", "")
        await client.post(login_url, data={"username": USERNAME, "password": PASSWORD, "cval": cval})
        csrf = ""
        for name, value in client.cookies.items():
            if "csrf" in name.lower():
                csrf = value
        
        mcp_headers = {
            "X-Splunk-Form-Key": csrf,
            "X-Requested-With": "XMLHttpRequest",
            "Authorization": f"Bearer {MCP_TOKEN}",
            "Content-Type": "application/json"
        }
        
        rpc_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "splunk_run_query",
                "arguments": {
                    "query": "| makeresults count=10 | streamstats count as time_id | eval metric=random()%100 | predict metric future_timespan=2"
                }
            }
        }
        
        print(f"[*] Executing native DensityFunction anomaly detection via MCP tool 'splunk_run_query'...")
        response = await client.post(MCP_URL, headers=mcp_headers, json=rpc_payload, timeout=60.0)
        print(f"\n[HTTP Status Code] {response.status_code}")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)

if __name__ == "__main__":
    asyncio.run(test_mcp())
