import requests
from bs4 import BeautifulSoup
from urllib.parse import (
    urlparse, urlunparse, parse_qs, urlencode
)

def fetch_content_signature(url: str, timeout=5):
    """
    Fetch the given URL (following redirects), parse the final HTML, and
    return a 'signature' that represents the page content.

    For demonstration, we'll include:
      - final_url (the last redirect location)
      - status_code
      - the <title> text (if any)
      - (optionally) a content hash of the HTML

    You can modify this to suit your definition of "same page."
    """
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        final_url = response.url
        status_code = response.status_code

        # Parse some or all of the HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the page title
        title = soup.title.string.strip() if soup.title and soup.title.string else ""

        # Optionally, do a hash of the entire HTML if you want to be thorough
        # import hashlib
        # content_hash = hashlib.sha256(response.text.encode('utf-8')).hexdigest()

        # Return your chosen signature. For now, let's do:
        #   (status_code, final_url, title)
        # If two pages have the same final_url, status_code, and <title>, we'll call them "the same."
        return (status_code, final_url, title)

    except requests.RequestException:
        # If there's a connection error, fallback to something that won't match easily
        return (None, None, None)

def pages_equivalent(url_a: str, url_b: str) -> bool:
    """
    Compare the 'content signatures' of two URLs.
    Returns True if we consider them the same page.
    """
    sig_a = fetch_content_signature(url_a)
    sig_b = fetch_content_signature(url_b)
    return sig_a == sig_b

def canonicalize_url(url: str) -> str:
    """
    Example function that tries to remove fragments, trailing slash,
    and known 'tracking' query parameters, comparing page content
    rather than just final URL strings.
    """

    parsed = urlparse(url)

    # 1) Remove the fragment if possible
    if parsed.fragment:
        no_fragment = parsed._replace(fragment="")
        test_url = urlunparse(no_fragment)
        if pages_equivalent(url, test_url):
            parsed = no_fragment

    # 2) Remove a trailing slash if it's not the root path
    if parsed.path.endswith("/") and parsed.path != "/":
        without_slash = parsed._replace(path=parsed.path.rstrip("/"))
        test_url = urlunparse(without_slash)
        if pages_equivalent(url, test_url):
            parsed = without_slash

    # 3) Remove known tracking parameters, one by one
    tracking_params = [
        "utm_source", "utm_medium", "utm_campaign",
        "utm_term", "utm_content", "itm_source",
        # etc.
    ]

    query_dict = parse_qs(parsed.query, keep_blank_values=True)
    for param in tracking_params:
        if param in query_dict:
            removed_value = query_dict.pop(param)
            test_query = urlencode(query_dict, doseq=True)
            test_parsed = parsed._replace(query=test_query)
            test_url = urlunparse(test_parsed)

            # Compare page content
            if not pages_equivalent(url, test_url):
                # Revert if the content differs
                query_dict[param] = removed_value

    # Rebuild final canonical URL
    final_query = urlencode(query_dict, doseq=True)
    final_parsed = parsed._replace(query=final_query)
    return urlunparse(final_parsed)

def main():
    original_url = (
        "https://fortune.com/2025/01/08/trump-canada-us-merger-51st-state/?itm_source=parsely-api"
    )
    print("Original URL:", original_url)

    short_url = canonicalize_url(original_url)
    print("Canonical (shortest) URL:", short_url)

    sig_original = fetch_content_signature(original_url)
    sig_short = fetch_content_signature(short_url)

    print("\nOriginal URL signature:", sig_original)
    print("Shortest URL signature:", sig_short)

    if sig_original == sig_short:
        print("\nThey appear to be the same content.")
    else:
        print("\nThey appear to differ in some way.")

if __name__ == "__main__":
    main()