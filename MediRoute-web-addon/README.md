
# MediRoute Web Add-on

This add-on turns the existing MediRoute backend into a browser-based educational
simulator. Claude receives the user's text/document, can call the existing
MediRoute Python functions as client tools, and returns the final analysis.

## Important

This is an educational simulator. Do not use it as a real emergency-dispatch
service or expose it publicly with real patient data.

## Install

From the existing project root:

```powershell
python -m pip install -r requirements-web.txt
```

Copy these files/folders from this add-on into the project root:

- `web_api.py`
- `claude_service.py`
- `web/`
- `.env.example` (copy to `.env`)

Put your Anthropic API key in `.env`:

```text
ANTHROPIC_API_KEY=...
CLAUDE_MODEL=claude-sonnet-5
```

Then run:

```powershell
python -m uvicorn web_api:app --reload
```

Open:

http://127.0.0.1:8000

## What it does

1. User enters an emergency description.
2. User can optionally attach a PDF or UTF-8 text document.
3. FastAPI sends the request to Claude.
4. Claude can call MediRoute tools.
5. The existing ambulance, hospital, traffic, A*, priority queue and dispatcher
   logic executes locally.
6. Tool results go back to Claude.
7. Claude produces a final analysis.
8. The browser displays the result.

The first version supports PDF and UTF-8 text uploads. Anthropic's PDF support
also supports charts, tables and visual content.
