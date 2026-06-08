# TRIDENT-AI Setup Guide

## Prerequisites

- **Python** 3.11 or newer
- **Node.js** 18+ and npm
- **Splunk Cloud** trial account with Developer License
- **AWS Account** with Bedrock access (Claude claude-sonnet-4-5 enabled)
- **Splunk MCP Server** (App ID 7931) installed from Splunkbase

## Step 1: Clone & Install

```bash
git clone https://github.com/anilchowdary07/TRIDENT-AI.git
cd TRIDENT-AI
pip install -r requirements.txt
```

## Step 2: Splunk Cloud Setup

1. Sign up for a [Splunk Cloud trial](https://www.splunk.com/en_us/download/splunk-cloud.html)
2. Request a **Developer License** (Settings → Licensing)
3. Install **MCP Server** (App ID 7931) from Splunkbase
4. Install **Splunk AI Toolkit** v5.7.3
5. Create an API token: Settings → Tokens → New Token
6. Note your instance hostname (e.g., `prd-p-xxxxx.splunkcloud.com`)

## Step 3: AWS Bedrock Setup

1. Enable **Claude claude-sonnet-4-5** in your AWS Bedrock console
2. Create IAM credentials or API key with Bedrock access
3. Note your `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and region

## Step 4: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
- `SPLUNK_HOST` — your Splunk Cloud hostname
- `SPLUNK_TOKEN` — your API token
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` — your AWS credentials
- `AWS_REGION` — your Bedrock region (e.g., `us-east-1`)

## Step 5: Create Splunk Indexes

In Splunk Cloud, create these indexes:
- `trident_incidents` — stores incident packages
- `trident_audit` — stores MCP audit trail

Or install the `splunk_app/` package which includes `indexes.conf`.

## Step 6: Generate Demo Data

```bash
python demo/simulate_incident.py
```

This generates sample metrics, security logs, and platform data in `demo/sample_data/`.

## Step 7: Run in Demo Mode

```bash
DEMO_MODE=true python main.py
```

You should see the TRIDENT-AI banner and "Autonomous loop ACTIVE" message.

## Step 8: Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 to see the Dark Ops Command Centre.

## Step 9: Run in Live Mode

Once satisfied with the demo, switch to live mode:
1. Set `DEMO_MODE=false` in `.env`
2. Ensure Splunk Cloud credentials are correct
3. Run: `python main.py`

## Troubleshooting

| Issue | Solution |
|-------|---------|
| `SplunkAuthError` | Check SPLUNK_TOKEN or USERNAME/PASSWORD in .env |
| `BedrockError: throttled` | Wait 60 seconds, Bedrock has rate limits |
| `CDTSM hard limit exceeded` | Ensure holdback + forecast_k ≤ 384 |
| Frontend blank page | Check browser console, ensure npm install completed |
| No incidents appearing | Run `demo/simulate_incident.py` first, set DEMO_MODE=true |
