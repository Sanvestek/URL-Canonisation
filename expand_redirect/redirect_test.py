import requests
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import re

def normalize_url(url: str) -> str:
    """
    Basic URL normalization:
      1) Lowercase the scheme and domain. <-- CASE SENSITIVE URLS???
      2) Remove default ports (80 for HTTP, 443 for HTTPS) if present.
      3) Remove trailing slash if present in the path.
      4) Sort query parameters alphabetically (optional).
    """
    # Parse the URL
    parsed = urlparse(url)

    # Lowercase scheme and netloc #THIS MAY BE DETREMENTENTAL
    # many urls are case sensitive (True?)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Remove default ports from netloc
    if (scheme == "http" and netloc.endswith(":80")):
        netloc = netloc[:-3]  # remove :80
    elif (scheme == "https" and netloc.endswith(":443")):
        netloc = netloc[:-4]  # remove :443

    # Remove trailing slash from path
    path = parsed.path
    if path.endswith("/") and len(path) > 1:
        path = path.rstrip("/")

    # Sort query parameters (optional, but often helpful)
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    # parse_qs returns a dict of {param: [value1, value2]} 
    # We'll flatten them (assuming one value per param) for simplicity
    sorted_query = sorted(query_params.items())
    encoded_query = urlencode(sorted_query, doseq=True)

    # Reconstruct the URL
    normalized = urlunparse((
        scheme,
        netloc,
        path,
        parsed.params,
        encoded_query,
        parsed.fragment
    ))
    return normalized

def remove_fragment(url: str) -> str:
    """
    This function removes the fragment from the URL.
    """
    parsed = urlparse(url)
    # Remove the fragment by setting it to an empty string
    parsed = parsed._replace(fragment='')
    # Reconstruct the URL without the fragment
    url_without_fragment = urlunparse(parsed)
    return url_without_fragment

def expand_redirect(url: str, timeout=5) -> str:
    """
    Follows redirects to get the final destination URL.
    Useful for short-link expansion or tracking final landing pages.
    """
    try:
        response = requests.head(url, allow_redirects=True, timeout=timeout)
        # Some sites respond incorrectly to HEAD, so fallback to GET if needed
        if response.status_code in (405, 400, 403):
            response = requests.get(url, allow_redirects=True, timeout=timeout)
        final_url = response.url
        return final_url
    except requests.RequestException as e:
        print(f"Error expanding redirect for {url}: {e}")
        # If there's an error, return the original URL or handle it as needed
        return url
    

def main():
    # Some example URLs:
    test_urls = [
        "HTTP://www.Example.com:80/path/", 
        "https://www.youtube.com/watch?v=abc123#channel",
        "https://youtu.be/abc123",
        "http://bit.ly/3kX2Example",
        "https://bit.ly/mbmbam", 
        "https://www.EXAMPLE.com:443/path/?b=2&a=1#section"
    ]

    for original_url in test_urls:
        print(f"\nOriginal URL: {original_url}")
        
        # 1) Normailise the URL 
        normalized = normalize_url(original_url)
        print(f" Normalized URL: {normalized}")

        # 2) Remove fragments
        fragment_adjusted = remove_fragment(normalized)
        print(f" After removing fragements: {fragment_adjusted}")

        # 3) Expand any redirects (short links, etc.)
        expanded = expand_redirect(fragment_adjusted)
        print(f" After redirect expansion: {expanded}")

if __name__ == "__main__":
    main()
