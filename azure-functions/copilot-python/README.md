# Copilot Studio Python backend (Azure Functions)

This folder contains a minimal **Python Azure Functions** app with an **HTTP-trigger** endpoint intended to be called from a Copilot Studio HTTP-capable connector.

## Endpoint

- Route: `POST /api/copilot`
- Auth: **Function key** (add `?code=<function_key>` to the URL)
- Request: JSON body
- Response: JSON body

## Programming model

This uses the **Python v2 programming model** (`function_app.py`) and requires **worker indexing** to be enabled on the Function App:

- App setting: `AzureWebJobsFeatureFlags=EnableWorkerIndexing`

## Local run (optional)

You can run this locally with Azure Functions Core Tools:

```powershell
cd azure-functions/copilot-python
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
func start
```

Create a `local.settings.json` (not committed) if you want local storage/Azurite configuration.

## Local run (recommended): Docker Compose (Azurite + Functions)

From repo root:

```powershell
copy env.local.example .env.local
docker compose -p frontend-cfa -f docker-compose.functions.yml --env-file .env.local up -d --build
```

Then test:

```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:7071/api/copilot" -ContentType "application/json" -Body (@{ prompt = "hi" } | ConvertTo-Json)
```

