import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

def fetch_content_signature(url: str, timeout=5):
    try:
        resp = requests.get(url, allow_redirects=True, timeout=timeout)
        status_code = resp.status_code
        soup = BeautifulSoup(resp.text, 'html.parser')
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        # Include more details about the page content
        body_text = soup.body.get_text(strip=True) if soup.body else ""
        return (status_code, title, body_text)
    except requests.RequestException:
        return (None, "", "")

def pages_equivalent(url_a: str, url_b: str) -> bool:
    sig_a = fetch_content_signature(url_a)
    sig_b = fetch_content_signature(url_b)
    return (sig_a == sig_b)

def canonicalize_url(url: str) -> str:
    parsed = urlparse(url)

    # 1) Remove fragment if it doesn't change content
    if parsed.fragment:
        test_parsed = parsed._replace(fragment="")
        test_url = urlunparse(test_parsed)
        if pages_equivalent(url, test_url):
            parsed = test_parsed

    # 2) Remove trailing slash if it doesn't change content
    if parsed.path.endswith("/") and parsed.path != "/":
        test_parsed = parsed._replace(path=parsed.path.rstrip("/"))
        test_url = urlunparse(test_parsed)
        if pages_equivalent(url, test_url):
            parsed = test_parsed

    # 3) Remove everything after the last '/' from right to left until content changes
    path_parts = parsed.path.split('/')
    for i in range(len(path_parts) - 1, 0, -1):
        test_path = '/'.join(path_parts[:i])
        test_parsed = parsed._replace(path=test_path)
        test_url = urlunparse(test_parsed)
        if pages_equivalent(url, test_url):
            parsed = test_parsed
        else:
            break

    # 4) Remove all known tracking params and everything after them
    known_tracking_params = [
        "utm_source", "utm_medium", "utm_campaign",
        "utm_term", "utm_content", "itm_source", "si", "originalSubdomain", "trackingId", "refId", "midToken", "trkEmail", "otpToken",
        "midSig", "trk", "eid", "ref", "cmp", "src", "mc_eid", "mc_cid", "mc_lid", "mc_mid", "mc_rid", "mc_t", "mc_uid", "mc_lid", "mc_eid", "mc_cid",
        # ...
    ]
    q_dict = parse_qs(parsed.query, keep_blank_values=True)
    removed_params = {}

    for param in known_tracking_params:
        if param in q_dict:
            removed_params[param] = q_dict.pop(param)
            break  # Stop after removing the first known tracking parameter

    # Remove everything after the first known tracking parameter
    test_query = urlencode(q_dict, doseq=True)
    test_parsed = parsed._replace(query=test_query)
    test_url = urlunparse(test_parsed)

    # 5) Check if content changes after removing all tracking params
    if not pages_equivalent(url, test_url):
        # Restore parameters one by one if content changes
        for param, value in removed_params.items():
            q_dict[param] = value
            test_query = urlencode(q_dict, doseq=True)
            test_parsed = parsed._replace(query=test_query)
            test_url = urlunparse(test_parsed)

            if pages_equivalent(url, test_url):
                q_dict.pop(param)

    final_query = urlencode(q_dict, doseq=True)
    final_parsed = parsed._replace(query=final_query)
    return urlunparse(final_parsed)

def main():
    original_url = (
        "https://www.linkedin.com/jobs/view/4072276680/?trackingId=HsJTLWIQTGO9o%2FE5pF0S%2Bw%3D%3D&refId=PRPmdWjWTCWNNRYk%2BP9JPw%3D%3D&midToken=AQGfdDCjrLGhkQ&midSig=1Lgo0gvQ3EMrA1&trk=eml-email_jobs_viewed_job_reminder_01-job_card-0-jobcard_body&trkEmail=eml-email_jobs_viewed_job_reminder_01-job_card-0-jobcard_body-null-gilcz4~m5zt912i~s3-null-null&eid=gilcz4-m5zt912i-s3&otpToken=MWIwYzE2ZTYxYTI2Y2RjZGIyMjQwNGVkNDUxOWU3YjI4ZmM3ZDg0MzllYWU4OTYxNzljNDA3Njk0NjVmNTlmMGZmZDBkZjllNzVmMGI5YzY3OWFjZWUwYjE4OTQ5NDI1YzYwOWU2ZGNjMzc2M2RjNjg4YmJmMiwxLDE%3D"
    )

    print("Original URL:", original_url)
    shortest_url = canonicalize_url(original_url)
    print("Canonical (shortest) URL:", shortest_url)

if __name__ == "__main__":
    main()