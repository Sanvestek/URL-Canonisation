import requests
from urllib.parse import (
    urlparse, urlunparse, parse_qs, urlencode
)

def expand_redirect(url: str, timeout=5) -> str:
    """
    Follows redirects to get the final destination URL.
    """
    try:
        response = requests.get(url, allow_redirects=True, timeout=timeout)
        return response.url
    except requests.RequestException:
        # If there's any error connecting, just return the original
        return url

def confirm_same_destination(original_url: str, test_url: str) -> bool:
    """
    Return True if original_url and test_url ultimately resolve to the same final URL.
    """
    original_final = expand_redirect(original_url)
    test_final = expand_redirect(test_url)
    return original_final == test_final

def make_url_canonical(url: str) -> str:
    """
    Attempt to remove the fragment, trailing slash, and query parameters
    without changing the final destination page. Return the shortest safe URL.
    """
    parsed = urlparse(url)

    # ---------------------------------------------------------
    # STEP 1: Try removing the fragment if it exists
    # ---------------------------------------------------------
    if parsed.fragment:
        no_fragment_parsed = parsed._replace(fragment="")
        no_fragment_url = urlunparse(no_fragment_parsed)
        
        if confirm_same_destination(url, no_fragment_url):
            # Safe to remove the fragment
            parsed = no_fragment_parsed

    # ---------------------------------------------------------
    # STEP 2: Try removing a trailing slash from the path if present
    # ---------------------------------------------------------
    if parsed.path.endswith("/") and parsed.path != "/":
        trimmed_path = parsed.path.rstrip("/")
        no_slash_parsed = parsed._replace(path=trimmed_path)
        no_slash_url = urlunparse(no_slash_parsed)
        
        if confirm_same_destination(url, no_slash_url):
            # Safe to remove trailing slash
            parsed = no_slash_parsed

    # ---------------------------------------------------------
    # STEP 3: Try removing each query parameter if it doesn't affect the final page
    # ---------------------------------------------------------
    original_query = parse_qs(parsed.query, keep_blank_values=True)
    
    # We'll build a mutable dict from query_params
    cleaned_params = dict(original_query)  # copy for safe iteration

    for key in list(cleaned_params.keys()):
        # Temporarily remove this key (and its values)
        removed_value = cleaned_params.pop(key)

        # Rebuild the "test" URL without the key
        test_parsed = parsed._replace(query=urlencode(cleaned_params, doseq=True))
        test_url = urlunparse(test_parsed)

        # Check if final destinations match
        if not confirm_same_destination(url, test_url):
            # If it changes the destination, restore the parameter
            cleaned_params[key] = removed_value

    # Rebuild the final cleaned URL
    final_parsed = parsed._replace(query=urlencode(cleaned_params, doseq=True))
    cleaned_url = urlunparse(final_parsed)
    return cleaned_url

def main():
    original_url = "https://fortune.com/2025/01/08/trump-canada-us-merger-51st-state/?itm_source=parsely-api"

    print("\nOriginal URL:", original_url)

    canonical_url = make_url_canonical(original_url)
    print("Canonical (shortest) URL:", canonical_url)

    # Just to double-check the final expansions
    print("Original final expansion:", expand_redirect(original_url))
    print("Canonical final expansion:", expand_redirect(canonical_url))

if __name__ == "__main__":
    main()
