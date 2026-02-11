import json
import logging
from typing import Any, Dict

import azure.functions as func

# Python v2 programming model (worker indexing)
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


def _json_response(payload: Dict[str, Any], status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps(payload, ensure_ascii=False),
        status_code=status_code,
        mimetype="application/json",
        headers={"Cache-Control": "no-store"},
    )


@app.route(route="copilot", methods=["POST"])
def copilot(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/copilot?code=<function_key>
    Body: { "prompt": "..." }
    Returns: { "ok": true, "result": "..." }
    """
    try:
        body = req.get_json()
        if not isinstance(body, dict):
            body = {"_value": body}
    except ValueError:
        body = {}

    prompt = body.get("prompt") or req.params.get("prompt")
    if not prompt:
        return _json_response(
            {
                "ok": False,
                "error": "Missing required field 'prompt' in JSON body (or query string).",
                "received": body or None,
            },
            status_code=400,
        )

    logging.info("copilot called; prompt_length=%s", len(str(prompt)))

    # TODO: Replace with your Python logic.
    result_text = f"Received prompt of length {len(str(prompt))}."

    return _json_response({"ok": True, "result": result_text})

