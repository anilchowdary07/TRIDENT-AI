import requests
import os
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv(override=True)

SPLUNK_WEB_URL = f"https://{os.getenv('SPLUNK_HOST')}"
USERNAME = os.getenv("SPLUNK_USERNAME")
PASSWORD = os.getenv("SPLUNK_PASSWORD")

def test_proxy():
    session = requests.Session()
    login_url = f"{SPLUNK_WEB_URL}/en-US/account/login"
    session.get(login_url, verify=False)
    
    cval = session.cookies.get("cval", "")
    payload = {"username": USERNAME, "password": PASSWORD, "cval": cval}
    session.post(login_url, data=payload, verify=False)
    
    print("All cookies:")
    for c in session.cookies:
        print(c.name, c.value)
        if "csrf" in c.name.lower():
            csrf_token = c.value
            
    search_url = f"{SPLUNK_WEB_URL}/en-US/splunkd/__raw/services/search/jobs?output_mode=json"
    headers = {"X-Splunk-Form-Key": getattr(session.cookies, "splunkweb_csrf_token_443", session.cookies.get("splunkweb_csrf_token", "")), "X-Requested-With": "XMLHttpRequest"}
    
    # Try to find exactly what the csrf token is named
    csrf = ""
    for c in session.cookies:
        if "csrf" in c.name:
            csrf = c.value
    
    headers["X-Splunk-Form-Key"] = csrf
            
    search_payload = {"search": "search index=_internal | head 1", "exec_mode": "oneshot"}
    res = session.post(search_url, headers=headers, data=search_payload, verify=False)
    print(res.status_code)
    try:
        print(res.json())
    except:
        print(res.text)

if __name__ == "__main__":
    test_proxy()
