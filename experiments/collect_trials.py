#!/usr/bin/env python3
"""
collect_trials.py

Fetch high-level ClinicalTrials.gov study metadata using the public Study Fields API.
Outputs a JSON file with a list of study field dicts plus provenance metadata.

Safety: This script collects publicly available metadata only. It does NOT provide
clinical advice, recommendations, or treatment protocols. All outputs require
human verification before use in any decision-making context.

Example:
  python experiments/collect_trials.py --query "aging OR longevity" --max 200 --out experiments/outputs/trials.json
"""

import argparse
import json
import time
import datetime
import sys
import os
from urllib.parse import quote, quote_plus

import requests

API_URL = "https://clinicaltrials.gov/api/query/study_fields"

DEFAULT_FIELDS = ",".join([
    "NCTId",
    "BriefTitle",
    "OfficialTitle",
    "Condition",
    "InterventionName",
    "OverallStatus",
    "StudyType",
    "Phase",
    "EnrollmentCount",
    "StartDate",
    "CompletionDate",
    "LocationCountry"
])

def fetch_study_fields(expr, max_results=100, fields=DEFAULT_FIELDS, batch_size=100, sleep=0.1, proxies=None):
    """
    Fetch study fields using the Study Fields API.

    Use requests' params dict (requests will handle correct encoding).
    Normalize common CLI forms such as replacing '+' with spaces when
    the expression contains no spaces (the script earlier double-encoded
    plus signs causing 404s). Add a conservative User-Agent and Accept
    headers since some servers reject unknown clients; raise on HTTP
    errors so callers can log and handle them.

    New behavior:
    - Accepts an optional `proxies` dict to route requests through a proxy.
    - All requests.get calls will pass the proxies arg when provided.
    """
    results = []
    start = 1

    # Normalize simple "plus-joined" expressions produced by some shells
    # e.g. user passed: aging+OR+longevity -> convert to "aging OR longevity"
    if "+" in expr and " " not in expr:
        expr = expr.replace("+", " ")

    # lightweight headers to mimic a real client
    headers = {
        "User-Agent": "c2s-scale-longevity-experiment/0.1 (https://github.com/stancsz/c2s-scale-lab)",
        "Accept": "application/json, text/plain, */*"
    }

    while len(results) < max_results:
        end = min(start + batch_size - 1, max_results)
        params = {
            "expr": expr,
            "fields": fields,
            "min_rnk": start,
            "max_rnk": end,
            "fmt": "json"
        }

        # First attempt: let requests build the query string (it encodes spaces as '+').
        # Retry through several header variants and an explicit percent-encoded URL if
        # a 404 is encountered. Capture the last network exception to raise if nothing works.
        resp = None
        last_exception = None

        header_variants = [
            headers,
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*"
            },
            {
                "User-Agent": "curl/7.88.1",
                "Accept": "application/json, text/plain, */*"
            }
        ]

        # Try each header variant; for each, try requests params form first, then a percent-encoded alt URL.
        for hdr in header_variants:
            try:
                resp = requests.get(API_URL, params=params, headers=hdr, timeout=60, proxies=proxies)
            except requests.RequestException as e:
                last_exception = e
                resp = None
                continue

            # If server returned 404 for this header, try a small connectivity test and then a percent-encoded alt URL
            if resp is not None and resp.status_code == 404:
                try:
                    test_params = {"expr": "heart", "min_rnk": "1", "max_rnk": "1", "fmt": "json"}
                    test_resp = requests.get(API_URL, params=test_params, headers=hdr, timeout=10, proxies=proxies)
                    if test_resp.status_code == 200:
                        # build percent-encoded expression URL and retry
                        enc_expr = quote(expr, safe="")
                        alt_url = f"{API_URL}?expr={enc_expr}&fields={quote(fields, safe=',')}&min_rnk={start}&max_rnk={end}&fmt=json"
                        try:
                            resp = requests.get(alt_url, headers=hdr, timeout=60, proxies=proxies)
                        except requests.RequestException as e:
                            last_exception = e
                            resp = None
                except requests.RequestException:
                    # connectivity test failed for this header; try next variant
                    resp = None

            # If we have a non-404 response, stop trying other headers
            if resp is not None and resp.status_code != 404:
                break

        # If we never got any response object, raise the last exception (or a generic error)
        if resp is None:
            if last_exception:
                raise last_exception
            else:
                raise requests.HTTPError(f"No response from {API_URL}")

        # Raise for any remaining HTTP error codes so caller can handle/log them
        resp.raise_for_status()

        # Parse JSON response (StudyFieldsResponse is expected for study_fields endpoint)
        data = resp.json()
        study_fields = data.get("StudyFieldsResponse", {}).get("StudyFields", [])

        # If we didn't get study fields back, break early
        if not study_fields:
            break

        results.extend(study_fields)

        # If fewer returned than requested, we've reached the end
        if len(study_fields) < (end - start + 1):
            break

        start = end + 1
        time.sleep(sleep)

    return results[:max_results]

def main():
    parser = argparse.ArgumentParser(description="Fetch ClinicalTrials.gov study fields (metadata only).")
    parser.add_argument("--query", "-q", required=True, help='Search expression (e.g. "aging OR longevity")')
    parser.add_argument("--max", "-m", type=int, default=200, help="Maximum number of studies to fetch")
    parser.add_argument("--out", "-o", default="experiments/outputs/trials.json", help="Output JSON path")
    parser.add_argument("--batch", type=int, default=100, help="Batch size per API call (max 100)")
    parser.add_argument("--sleep", type=float, default=0.1, help="Seconds to sleep between requests")
    parser.add_argument("--proxy", help="HTTP/HTTPS proxy (e.g. http://proxy.example:3128). Overrides environment proxies.")
    parser.add_argument("--use-local-fallback", action="store_true", help="If network calls fail, load studies from a local fallback JSON.")
    parser.add_argument("--local-fallback-path", default="experiments/outputs/trials_fallback.json", help="Path to local fallback JSON file to use when --use-local-fallback is enabled.")
    args = parser.parse_args()

    expr = args.query
    max_results = max(1, args.max)
    batch = max(1, min(100, args.batch))

    # Build proxies dict from CLI or environment
    proxies = None
    if args.proxy:
        proxy_val = args.proxy
        # ensure scheme present
        if not proxy_val.startswith("http://") and not proxy_val.startswith("https://"):
            proxy_val = "http://" + proxy_val
        proxies = {"http": proxy_val, "https": proxy_val}
    else:
        # requests will read environment proxies automatically, but we expose them explicitly
        env_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
        if env_proxy:
            proxies = {"http": env_proxy, "https": env_proxy}

    try:
        studies = fetch_study_fields(expr, max_results=max_results, fields=DEFAULT_FIELDS, batch_size=batch, sleep=args.sleep, proxies=proxies)
    except requests.RequestException as e:
        # Network failure: optionally load local fallback if requested
        print(f"Network or API error while fetching study fields: {e}", file=sys.stderr)
        if args.use_local_fallback:
            fallback_path = args.local_fallback_path
            try:
                with open(fallback_path, "r", encoding="utf-8") as fh:
                    fallback = json.load(fh)
                # Accept either {"studies": [...]} or a raw list of studies
                if isinstance(fallback, dict) and "studies" in fallback:
                    studies = fallback["studies"]
                elif isinstance(fallback, list):
                    studies = fallback
                else:
                    print(f"Local fallback file {fallback_path} did not contain a recognized structure. Proceeding with empty studies list.", file=sys.stderr)
                    studies = []
                print(f"Loaded {len(studies)} studies from local fallback {fallback_path}")
                fallback_used = True
                fallback_path_used = fallback_path
            except Exception as e2:
                print(f"Failed to load local fallback {fallback_path}: {e2}", file=sys.stderr)
                studies = []
                fallback_used = False
                fallback_path_used = None
        else:
            print("Proceeding with empty studies list and writing provenance to the output file.")
            studies = []
            fallback_used = False
            fallback_path_used = None

    output = {
        "provenance": {
            "source": "clinicaltrials.gov",
            "api_url": API_URL,
            "query": expr,
            "fields": DEFAULT_FIELDS,
            "requested_max": max_results,
            "fetched_count": len(studies),
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        "studies": studies
    }

    out_path = args.out
    # ensure parent directory exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2, ensure_ascii=False)

    print(f"Wrote {len(studies)} studies to {out_path}")

if __name__ == "__main__":
    main()
