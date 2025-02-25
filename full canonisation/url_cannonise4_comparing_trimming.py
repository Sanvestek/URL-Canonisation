import requests
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

def expand_redirect(url: str, timeout=5) -> str:
    """
    Follows redirects (HTTP 3xx) to get the final landing URL.
    Returns that final URL as a string.
    """
    try:
        resp = requests.get(url, allow_redirects=True, timeout=timeout)
        return resp.url
    except requests.RequestException:
        return url  # fallback if there's a network error

def urls_equivalent(url_a: str, url_b: str) -> bool:
    """
    Determines if url_a and url_b point to the 'same' final destination
    in a lenient way (specifically ignoring trailing slash differences
    in the final expanded URL).
    """
    final_a = expand_redirect(url_a)
    final_b = expand_redirect(url_b)

    # Parse both final expansions
    p_a = urlparse(final_a)
    p_b = urlparse(final_b)

    # Compare scheme (http vs https), netloc (domain), path, and query exactly,
    # BUT let's ignore trailing slash differences in the path.
    # That is: "/some/path" == "/some/path/" if everything else is the same.
    same_scheme = (p_a.scheme == p_b.scheme)
    same_netloc = (p_a.netloc == p_b.netloc)

    # For the path, ignore trailing slash differences:
    path_a = p_a.path.rstrip("/")
    path_b = p_b.path.rstrip("/")
    same_path = (path_a == path_b)

    # Compare query exactly (if you want to be lenient with queries,
    # you'd do something more advanced here).
    same_query = (p_a.query == p_b.query)

    # For fragments (#...), typically the server-side page is unaffected,
    # but we can compare them as well. Usually they're not needed for "final" comparisons.
    # Let's ignore fragment differences for final-destination equivalence:
    # same_fragment = (p_a.fragment == p_b.fragment)  # optionally check or ignore

    return (same_scheme and same_netloc and same_path and same_query)

def canonicalize_url(url: str) -> str:
    """
    Attempts to remove fragments, trailing slashes, and suspected 'tracking' parameters
    from 'url', verifying that each removal does NOT lead to a different final page.
    Returns the 'shortest' possible URL that leads to the same final page.
    """

    parsed = urlparse(url)

    # -----------------------------
    # 1) Remove the fragment (if any)
    # -----------------------------
    if parsed.fragment:
        without_fragment = parsed._replace(fragment="")
        test_url = urlunparse(without_fragment)

        if urls_equivalent(url, test_url):
            # safe to drop the fragment
            parsed = without_fragment

    # -----------------------------
    # 2) Remove trailing slash if it doesn't alter the final page
    # -----------------------------
    # Only remove if path != "/", to avoid removing the slash from root
    if parsed.path.endswith("/") and parsed.path != "/":
        new_path = parsed.path.rstrip("/")
        test_parsed = parsed._replace(path=new_path)
        test_url = urlunparse(test_parsed)

        if urls_equivalent(url, test_url):
            # safe to remove trailing slash
            parsed = test_parsed

    # -----------------------------
    # 3) Remove "known" tracking parameters, one by one
    #    (utm_..., itm_source, etc.)
    # -----------------------------
    remove_candidates = [
        "utm_source", "utm_medium", "utm_campaign",
        "utm_term", "utm_content", "itm_source",
        # Add more if needed
    ]

    # parse_qs returns dict of {param -> [value1, value2, ...]}
    query_params = parse_qs(parsed.query, keep_blank_values=True)

    # We'll attempt to remove each candidate param and check if the final is still the same
    for param in remove_candidates:
        if param in query_params:
            saved_value = query_params.pop(param)  # remove it
            test_query = urlencode(query_params, doseq=True)
            test_parsed = parsed._replace(query=test_query)
            test_url = urlunparse(test_parsed)

            if not urls_equivalent(url, test_url):
                # The final page changed or is detected as different,
                # so restore the parameter
                query_params[param] = saved_value

    # Rebuild final query
    final_query = urlencode(query_params, doseq=True)
    final_parsed = parsed._replace(query=final_query)
    canonical_url = urlunparse(final_parsed)

    return canonical_url

def main():
    # Example URL with trailing slash, a fragment, and 'itm_source'
    original_url = (
        "https://fortune.com/2025/01/08/"
        "trump-canada-us-merger-51st-state/?itm_source=parsely-api"
    )

    print("Original URL:       ", original_url)

    shortest_url = canonicalize_url(original_url)
    print("Shortest Safe URL:  ", shortest_url)

    # Print their expansions, so we can see if the site re-adds anything
    expanded_original = expand_redirect(original_url)
    expanded_shortest = expand_redirect(shortest_url)

    print("Final expanded (original):", expanded_original)
    print("Final expanded (shortest):", expanded_shortest)

if __name__ == "__main__":
    main()