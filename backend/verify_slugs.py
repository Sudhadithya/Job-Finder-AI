"""
Live ATS slug verification for 19 India-relevant companies.
Run: python verify_slugs.py
"""
import asyncio
import httpx

CANDIDATES = [
    # Greenhouse
    {"name": "Postman",     "ats": "greenhouse", "slug": "postman"},
    {"name": "PhonePe",     "ats": "greenhouse", "slug": "phonepe"},
    {"name": "Groww",       "ats": "greenhouse", "slug": "groww"},
    {"name": "Nutanix",     "ats": "greenhouse", "slug": "nutanix"},
    {"name": "Rubrik",      "ats": "greenhouse", "slug": "rubrik"},
    {"name": "Databricks",  "ats": "greenhouse", "slug": "databricks"},
    {"name": "Confluent",   "ats": "greenhouse", "slug": "confluent"},
    {"name": "Uber",        "ats": "greenhouse", "slug": "uber"},
    {"name": "Adobe",       "ats": "greenhouse", "slug": "adobe"},
    {"name": "ServiceNow",  "ats": "greenhouse", "slug": "servicenow"},
    # Lever
    {"name": "Atlassian",   "ats": "lever",      "slug": "atlassian"},
    {"name": "BrowserStack","ats": "lever",      "slug": "browserstack"},
    {"name": "Razorpay",    "ats": "lever",      "slug": "razorpay"},
    {"name": "Meesho",      "ats": "lever",      "slug": "meesho"},
    {"name": "Freshworks",  "ats": "lever",      "slug": "freshworks"},
    # Custom / big-tech probes
    {"name": "Salesforce",  "ats": "workday",    "slug": "salesforce", "url": "https://salesforce.wd12.myworkdayjobs.com/External_Career_Site/jobs"},
    {"name": "Microsoft",   "ats": "microsoft",  "slug": "microsoft",  "url": "https://gcsservices.careers.microsoft.com/search/api/v1/search?lc=India&l=en_us&pgSz=1"},
    {"name": "Google",      "ats": "google",     "slug": "google",     "url": "https://careers.google.com/api/v3/search/?location=India&page_size=1"},
    {"name": "Amazon",      "ats": "amazon",     "slug": "amazon",     "url": "https://www.amazon.jobs/en/search.json?base_query=software+engineer&loc_query=India&result_limit=1"},
]

def get_url(entry):
    if "url" in entry:
        return entry["url"]
    ats = entry["ats"]
    slug = entry["slug"]
    if ats == "greenhouse":
        return f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    elif ats == "lever":
        return f"https://api.lever.co/v0/postings/{slug}?mode=json"
    elif ats == "ashby":
        return f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    return None

async def probe(client, entry):
    url = get_url(entry)
    if not url:
        return {**entry, "status": "NO_URL", "job_count": 0}
    try:
        r = await client.get(url, timeout=15.0, follow_redirects=True)
        if r.status_code == 200:
            try:
                data = r.json()
                ats = entry["ats"]
                if ats == "greenhouse":
                    count = len(data.get("jobs", []))
                elif ats == "lever":
                    count = len(data) if isinstance(data, list) else 0
                elif ats == "ashby":
                    count = len(data.get("jobs", []))
                elif ats == "microsoft":
                    count = data.get("totalCount", data.get("count", "?"))
                elif ats == "google":
                    count = data.get("count", "?")
                elif ats == "amazon":
                    count = data.get("hits", {}).get("total", "?") if isinstance(data.get("hits"), dict) else "?"
                else:
                    count = "?"
            except Exception:
                count = "JSON_PARSE_ERR"
            return {**entry, "status": "OK", "job_count": count}
        else:
            return {**entry, "status": f"HTTP_{r.status_code}", "job_count": 0}
    except Exception as e:
        return {**entry, "status": f"ERR:{type(e).__name__}", "job_count": 0}

async def main():
    print("\n=== ATS Slug Verification ===\n")
    async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}) as client:
        tasks = [probe(client, entry) for entry in CANDIDATES]
        results = await asyncio.gather(*tasks)

    ok = [r for r in results if r["status"] == "OK"]
    fail = [r for r in results if r["status"] != "OK"]

    print("LIVE BOARDS:")
    for r in ok:
        print(f"  [{r['ats']:12}] {r['name']:15} slug={r.get('slug', ''):20} jobs={r['job_count']}")

    print("\nFAILED:")
    for r in fail:
        print(f"  [{r['ats']:12}] {r['name']:15} status={r['status']}")

asyncio.run(main())
