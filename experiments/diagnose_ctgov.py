import requests
import json
import sys
import datetime
import os

OUT_PATH = "experiments/outputs/ctgov_diagnostic.json"

def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    url = "https://clinicaltrials.gov/api/query/study_fields"
    params = {
        "expr": "aging OR longevity",
        "fields": "NCTId,BriefTitle,OfficialTitle,Condition,InterventionName,OverallStatus,StudyType,Phase,EnrollmentCount,StartDate,CompletionDate,LocationCountry",
        "min_rnk": "1",
        "max_rnk": "1",
        "fmt": "json",
    }
    headers = {
        "User-Agent": "c2s-scale-longevity-experiment/0.1",
        "Accept": "application/json, text/plain, */*",
    }

    result = {
        "collected_at": now_iso(),
        "request": {"url": url, "params": params, "headers": headers},
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        result["status_code"] = resp.status_code
        result["final_url"] = resp.url
        # headers may contain non-serializable objects; convert to dict of strings
        result["response_headers"] = dict(resp.headers)
        # store a reasonably-sized snippet of the body for inspection
        text = resp.text or ""
        result["text_snippet"] = text[:5000]
        # If JSON returned, try to parse and include top-level keys (safe)
        try:
            parsed = resp.json()
            if isinstance(parsed, dict):
                result["json_top_keys"] = list(parsed.keys())
        except Exception:
            result["json_top_keys"] = None

        with open(OUT_PATH, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, ensure_ascii=False)

        print("WROTE", OUT_PATH)
        print("STATUS", resp.status_code)
        print("URL", resp.url)
    except Exception as exc:
        result["error"] = repr(exc)
        with open(OUT_PATH, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, ensure_ascii=False)
        print("ERROR", repr(exc))
        print("WROTE", OUT_PATH)
        sys.exit(2)

if __name__ == "__main__":
    main()
