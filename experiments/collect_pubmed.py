#!/usr/bin/env python3
"""
collect_pubmed.py

Fetch PubMed article metadata and abstracts using NCBI E-utilities (esearch + efetch).
Outputs a JSON file containing a list of article metadata entries.

Safety: This script fetches publicly available bibliographic metadata and abstracts only.
It does NOT provide clinical advice or treatment protocols. All outputs require human
verification before use in any decision-making context.

Example:
  python experiments/collect_pubmed.py --query "aging interventions" --max 200 --out experiments/outputs/pubmed.json --email you@example.com
"""

import argparse
import json
import time
import datetime
import sys
import requests
import xml.etree.ElementTree as ET
import os

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

def esearch_ids(term, max_results=200, retmax=100, email=None, sleep=0.34):
    ids = []
    start = 0
    while len(ids) < max_results:
        params = {
            "db": "pubmed",
            "term": term,
            "retstart": start,
            "retmax": min(retmax, max_results - len(ids)),
            "retmode": "json",
        }
        if email:
            params["email"] = email
        r = requests.get(ESEARCH_URL, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        batch = data.get("esearchresult", {}).get("idlist", [])
        if not batch:
            break
        ids.extend(batch)
        if len(batch) < params["retmax"]:
            break
        start += len(batch)
        time.sleep(sleep)
    return ids[:max_results]

def efetch_articles(id_list, batch_size=100, email=None, sleep=0.34):
    articles = []
    for i in range(0, len(id_list), batch_size):
        batch = id_list[i:i+batch_size]
        params = {
            "db": "pubmed",
            "id": ",".join(batch),
            "retmode": "xml",
        }
        if email:
            params["email"] = email
        r = requests.get(EFETCH_URL, params=params, timeout=60)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        for pubmed_article in root.findall(".//PubmedArticle"):
            try:
                medline = pubmed_article.find("MedlineCitation")
                pmid_elem = medline.find("PMID")
                pmid = pmid_elem.text if pmid_elem is not None else None

                article = medline.find("Article")
                title_elem = article.find("ArticleTitle")
                title = "".join(title_elem.itertext()).strip() if title_elem is not None else None

                abstract_text = []
                abstract = article.find("Abstract")
                if abstract is not None:
                    for abstract_text_elem in abstract.findall("AbstractText"):
                        # abstract_text_elem may have 'Label' attributes
                        text = "".join(abstract_text_elem.itertext()).strip()
                        if text:
                            abstract_text.append(text)
                abstract_joined = "\n\n".join(abstract_text) if abstract_text else None

                journal = article.find("Journal")
                journal_title = journal.find("Title").text if journal is not None and journal.find("Title") is not None else None

                pub_date = None
                journal_issue = journal.find("JournalIssue") if journal is not None else None
                if journal_issue is not None:
                    pub_date_elem = journal_issue.find("PubDate")
                    if pub_date_elem is not None:
                        parts = []
                        for tag in ("Year", "Month", "Day"):
                            el = pub_date_elem.find(tag)
                            if el is not None and el.text:
                                parts.append(el.text)
                        if parts:
                            pub_date = "-".join(parts)

                authors = []
                author_list = article.find("AuthorList")
                if author_list is not None:
                    for a in author_list.findall("Author"):
                        lastname = a.find("LastName")
                        forename = a.find("ForeName")
                        if lastname is not None and forename is not None:
                            authors.append(f"{forename.text} {lastname.text}")
                        elif a.find("CollectiveName") is not None:
                            authors.append(a.find("CollectiveName").text)

                doi = None
                article_ids = pubmed_article.find("PubmedData/ArticleIdList")
                if article_ids is not None:
                    for aid in article_ids.findall("ArticleId"):
                        if aid.attrib.get("IdType") == "doi":
                            doi = aid.text

                record = {
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract_joined,
                    "journal": journal_title,
                    "pub_date": pub_date,
                    "authors": authors,
                    "doi": doi,
                }
                articles.append(record)
            except Exception:
                # skip problematic entries but continue processing others
                continue
        time.sleep(sleep)
    return articles

def main():
    parser = argparse.ArgumentParser(description="Fetch PubMed metadata and abstracts using NCBI E-utilities.")
    parser.add_argument("--query", "-q", required=True, help='Search term (e.g. "aging interventions")')
    parser.add_argument("--max", "-m", type=int, default=200, help="Maximum number of articles to fetch")
    parser.add_argument("--out", "-o", default="experiments/outputs/pubmed.json", help="Output JSON path")
    parser.add_argument("--email", type=str, default=None, help="Contact email to include in requests (recommended by NCBI)")
    parser.add_argument("--retmax", type=int, default=100, help="Batch size for esearch/efetch (max 100)")
    args = parser.parse_args()

    ids = []
    try:
        ids = esearch_ids(args.query, max_results=args.max, retmax=args.retmax, email=args.email)
    except requests.RequestException as e:
        print(f"Network or API error during esearch: {e}", file=sys.stderr)
        sys.exit(2)

    articles = []
    if ids:
        try:
            articles = efetch_articles(ids, batch_size=args.retmax, email=args.email)
        except requests.RequestException as e:
            print(f"Network or API error during efetch: {e}", file=sys.stderr)
            sys.exit(2)

    output = {
        "provenance": {
            "source": "pubmed",
            "esearch_url": ESEARCH_URL,
            "efetch_url": EFETCH_URL,
            "query": args.query,
            "requested_max": args.max,
            "fetched_count": len(articles),
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        },
        "articles": articles
    }

    out_path = args.out
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2, ensure_ascii=False)

    print(f"Wrote {len(articles)} PubMed articles to {out_path}")

if __name__ == "__main__":
    main()
