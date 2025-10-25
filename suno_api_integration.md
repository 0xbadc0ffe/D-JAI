# Suno API Integration Guide

This document captures the workflow and conventions we follow to talk to [Suno API](https://docs.sunoapi.org/) from D‑JAI. It is aimed at agents or developers who need to hook new functionality into the music‑generation pipeline.

---

## 1. Environment Variables

| Variable        | Example Value                           | Notes                                                                                   |
|-----------------|-----------------------------------------|-----------------------------------------------------------------------------------------|
| `SUNO_API_URL`  | `https://api.sunoapi.org/api/v1`        | Base REST URL. Stick to `/api/v1`.                                                      |
| `SUNO_API_KEY`  | `suno_sk_...`                           | Bearer token issued by Suno. Keep it out of version control.                           |
| `GPT_API_URL`   | _existing_                              | Already used for lyrics/metadata generation. No change needed.                          |
| `GPT_API_KEY`   | _existing_                              | Ditto.                                                                                  |
| `CALLBACK_URL`  | (optional) `https://.../callbacks/suno` | Suno can push task updates; we currently poll but exposing this avoids polling delay.   |

Store the variables in `src/.env` and load via `dotenv` (already wired in `src/app.py`).

---

## 2. Core Endpoints

All endpoints require `Authorization: Bearer <SUNO_API_KEY>` and `Content-Type: application/json`.

### 2.1 Create a Generation Task

```
POST {SUNO_API_URL}/generate
Body:
{
  "prompt": "Lyrics or textual idea",
  "customMode": true,
  "style": "Electronic Dance",
  "title": "Digital Dreams",
  "instrumental": false,
  "model": "V4_5",
  "callBackUrl": "https://your-server.com/music-callback"
}
```

Response (success):

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "taskId": "suno_task_abc123"
  }
}
```

Save the `taskId`; no audio URL is returned yet.

### 2.2 Poll Task Status

```
GET {SUNO_API_URL}/generate/record-info?taskId=<TASK_ID>
```

Successful completion payload:

```json
{
  "code": 200,
  "data": {
    "taskId": "suno_task_abc123",
    "status": "SUCCESS",
    "response": {
      "data": [
        {
          "id": "audio_123",
          "audio_url": "https://cdn.sunoapi.org/generated-music.mp3",
          "title": "Generated Song",
          "tags": "folk, acoustic",
          "duration": 180.5
        }
      ]
    }
  }
}
```

Statuses to watch: `PENDING`, `PROCESSING`, `SUCCESS`, `FAILED`. Retry polling every 4–5 seconds with a 2–3 minute cap.

### 2.3 (Optional) Helper Endpoints

| Endpoint                         | Use Case                                      |
|----------------------------------|-----------------------------------------------|
| `POST /lyrics`                   | Generate lyrics only.                         |
| `POST /generate/extend`          | Extend/continue an existing `audioId`.        |
| `POST /generate/cover`           | Transform uploads to a new style.             |
| `POST /vocal-removal/generate`   | Separate vocals/instrumental.                 |
| `GET /get-credits`               | Check available credits/quota.                |

We currently rely on `/generate` + `/generate/record-info`, but planning for these calls keeps future work smoother.

---

## 3. Integration Steps Inside `src/app.py`

1. **Load Suno credentials**  
   ```python
   SUNO_API_URL = os.getenv("SUNO_API_URL")
   SUNO_API_KEY = os.getenv("SUNO_API_KEY")
   ```

2. **Submit generation request**  
   Replace the direct `requests.post(f"{SUNO_API_URL}/api/custom_generate", ...)` call with the `/generate` body shown above. Include knobs surfaced by the UI (lyrics, title, genres mapped to `style`/`tags`, etc.).

3. **Poll for completion**  
   Write a helper such as `wait_for_suno_task(task_id)` that loops on `/generate/record-info`. On `SUCCESS`, pull the first `audio_url`; on `FAILED`, raise an exception so the UI can notify the user.

4. **Download the MP3**  
   Use the returned `audio_url` in `download_song`. Remove the current CDN guessing logic (`https://cdn1.suno.ai/{song_id}.mp3`).

5. **Logging**  
   - Log the `taskId`, payload subset, and status transitions to aid debugging.  
   - When task fails, capture `response.get("error")` if provided.

6. **Callbacks (optional)**  
   If you expose a reachable HTTPS endpoint, set `callBackUrl`. Suno will push the same payload as the polling response, letting you skip repeated GETs. Make sure to verify signatures/IPs before trusting the data.

---

## 4. Error Handling & Retries

- **HTTP errors**: Retry on `429`/`5xx` with exponential backoff (max ~5 attempts). Abort on `4xx` (bad payload, invalid key).
- **Task FAIL state**: Inspect `response.error_code` or similar metadata, return a friendly message to the UI, and optionally requeue with tighter prompts.
- **Timeouts**: If a task stays `PROCESSING` beyond 3 minutes, cancel and notify the user. Suno charges credits even on failures, so avoid infinite loops.
- **Network hiccups**: Wrap `requests` calls with a short timeout (10–15s) to avoid blocking the Flask worker.

---

## 5. Testing Checklist

1. Ensure `.env` contains valid `SUNO_API_URL`/`SUNO_API_KEY`.
2. Run `python src/app.py`, fill the Create Song form, and confirm:  
   - Task ID logged.  
   - Polling returns `SUCCESS`.  
   - MP3 appears in `queue/` and `log/queue.log`.  
3. Start `python src/streamer.py` to verify the downloaded track plays and announcements still work.
4. Trigger an invalid request (e.g., empty prompt) to validate error surfaces in the UI.

---

## 6. Reference Snippets

Python helper sketch (drop into `src/app.py` or a dedicated module):

```python
import time
import requests

def suno_generate(prompt, **kwargs):
    payload = {
        "prompt": prompt,
        "customMode": True,
        "model": kwargs.get("model", "V4_5"),
        "instrumental": kwargs.get("instrumental", False),
        "title": kwargs.get("title"),
        "style": kwargs.get("style"),
        "callBackUrl": kwargs.get("callback_url"),
    }
    resp = requests.post(
        f"{SUNO_API_URL}/generate",
        headers={"Authorization": f"Bearer {SUNO_API_KEY}"},
        json={k: v for k, v in payload.items() if v is not None},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 200:
        raise RuntimeError(f"Suno rejected request: {data}")
    return data["data"]["taskId"]

def wait_for_suno_task(task_id, interval=5, max_wait=180):
    deadline = time.time() + max_wait
    while time.time() < deadline:
        resp = requests.get(
            f"{SUNO_API_URL}/generate/record-info",
            params={"taskId": task_id},
            headers={"Authorization": f"Bearer {SUNO_API_KEY}"},
            timeout=10,
        )
        resp.raise_for_status()
        payload = resp.json()["data"]
        status = payload["status"]
        if status == "SUCCESS":
            tracks = payload["response"]["data"]
            return tracks[0]["audio_url"]
        if status == "FAILED":
            raise RuntimeError(f"Suno task failed: {payload}")
        time.sleep(interval)
    raise TimeoutError("Suno task timed out")
```

Use `suno_generate` inside `generate_song`, then feed the resulting `audio_url` to `download_song`.

---

_Last updated: 2025-10-25. Keep this file in sync with upstream API changes noted on docs.sunoapi.org._
