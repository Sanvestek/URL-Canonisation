import requests
from bs4 import BeautifulSoup
from urllib.parse import (
    urlparse, urlunparse, parse_qs, urlencode
)

def strip_ephemeral_content(soup: BeautifulSoup) -> None:
    """
    Remove or sanitize dynamic and tracking-related elements in-place.
    This is fairly aggressive and LinkedIn-specific.
    """

    #
    # 1) Remove all <script> tags entirely
    #
    for s in soup.find_all("script"):
        s.decompose()

    #
    # 2) Remove any 'nonce' attributes from remaining tags
    #
    for tag in soup.find_all(attrs={"nonce": True}):
        del tag["nonce"]

    #
    # 3) Remove known ephemeral <meta> tags that store dynamic tracking or IDs
    #
    ephemeral_meta_names = {
        "bprPageInstance", "clientPageInstanceId", "applicationInstance",
        "requestIpCountryCode", "serviceInstance", "serviceVersion",
        "treeID",  # etc.
    }
    for meta in soup.find_all("meta"):
        if meta.get("name", "") in ephemeral_meta_names:
            meta.decompose()

    #
    # 4) Optionally remove <meta> tags that have a "content" containing dynamic strings
    #    e.g., if you see dynamic timestamps or random IDs. This is site-specific.
    #
    # for meta in soup.find_all("meta"):
    #     content_val = meta.get("content", "")
    #     if "random" in content_val or "token" in content_val:
    #         meta.decompose()

    #
    # 5) Remove certain <link> tags that might hold ephemeral references
    #    For example, if you see a pattern like trk= or refId= in the href.
    #    This is optional and site-specific.
    #
    # for link_tag in soup.find_all("link", href=True):
    #     href_val = link_tag["href"]
    #     if any(param in href_val for param in ["trk=", "refId=", "token="]):
    #         link_tag.decompose()

    #
    # 6) Possibly remove or sanitize other dynamic tags, hidden inputs, or IDs
    #    if you see them differ between the two HTML versions.
    #    e.g., remove <img> with dynamic query tokens, or remove data-* attributes, etc.
    #

def fetch_stripped_html(url: str, timeout=5) -> str:
    """
    Fetches the page from 'url', then strips out ephemeral or dynamic
    LinkedIn-specific elements. Returns the "cleaned" HTML string.
    """
    try:
        resp = requests.get(url, allow_redirects=True, timeout=timeout)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Strip ephemeral dynamic bits
        strip_ephemeral_content(soup)

        # Return the final, cleaned HTML
        return str(soup)

    except requests.RequestException:
        return ""

def pages_equivalent(url_a: str, url_b: str) -> bool:
    """
    Compare two URLs by fetching them and comparing their
    'cleaned' HTML (after removing ephemeral bits).
    """
    cleaned_a = fetch_stripped_html(url_a)
    cleaned_b = fetch_stripped_html(url_b)
    return (cleaned_a == cleaned_b)

def canonicalize_url(url: str) -> str:
    """
    Example function that tries to remove fragments, trailing slash,
    and known tracking parameters. It uses 'pages_equivalent' with
    stripped HTML to confirm the pages remain the same.
    """
    parsed = urlparse(url)

    # 1) Remove fragment if it doesn't alter content
    if parsed.fragment:
        test_parsed = parsed._replace(fragment="")
        test_url = urlunparse(test_parsed)
        if pages_equivalent(url, test_url):
            parsed = test_parsed

    # 2) Remove trailing slash if safe
    if parsed.path.endswith("/") and parsed.path != "/":
        test_parsed = parsed._replace(path=parsed.path.rstrip("/"))
        test_url = urlunparse(test_parsed)
        if pages_equivalent(url, test_url):
            parsed = test_parsed

    # 3) Remove known tracking parameters
    tracking_params = [
        "utm_source","utm_medium","utm_campaign","utm_term","utm_content",
        "itm_source","si","trackingId","refId","midToken","midSig",
        "trkEmail","otpToken","eid","mc_eid","mc_cid","mc_lid","mc_mid","mc_rid",
        "mc_t","mc_uid","trk",
    ]
    q = parse_qs(parsed.query, keep_blank_values=True)

    # We'll remove them all at once, but we could do them one by one if we want finer control
    removed_any = False
    for param in tracking_params:
        if param in q:
            del q[param]
            removed_any = True

    if removed_any:
        test_query = urlencode(q, doseq=True)
        test_parsed = parsed._replace(query=test_query)
        test_url = urlunparse(test_parsed)

        # If the cleaned pages are the same, keep them removed
        if pages_equivalent(url, test_url):
            parsed = test_parsed
        else:
            # Otherwise, revert (or attempt a param-by-param approach).
            pass

    return urlunparse(parsed)

def main():
    original_url = (
        "https://www.linkedin.com/jobs/view/4072276680/?trackingId=HsJTLWIQTGO9o%2FE5pF0S%2Bw%3D%3D&refId=PRPmdWjWTCWNNRYk%2BP9JPw%3D%3D&midToken=AQGfdDCjrLGhkQ&midSig=1Lgo0gvQ3EMrA1&trk=eml-email_jobs_viewed_job_reminder_01-job_card-0-jobcard_body&trkEmail=eml-email_jobs_viewed_job_reminder_01-job_card-0-jobcard_body-null-gilcz4~m5zt912i~s3-null-null&eid=gilcz4-m5zt912i-s3&otpToken=MWIwYzE2ZTYxYTI2Y2RjZGIyMjQwNGVkNDUxOWU3YjI4ZmM3ZDg0MzllYWU4OTYxNzljNDA3Njk0NjVmNTlmMGZmZDBkZjllNzVmMGI5YzY3OWFjZWUwYjE4OTQ5NDI1YzYwOWU2ZGNjMzc2M2RjNjg4YmJmMiwxLDE%3D"
    )
    print("Original URL:", original_url)

    short_url = canonicalize_url(original_url)
    print("Short (canonical) URL:", short_url)

    # Show whether the final stripped HTML is the same or not
    eq = pages_equivalent(original_url, short_url)
    print("Are they the 'same' page (after removing ephemeral HTML)?", eq)

if __name__ == "__main__":
    main()