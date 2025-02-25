import requests
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

def expand_redirect(url: str, timeout=5) -> str:
    """
    Follows redirects to get the final destination URL.
    """
    try:
        # Use GET if HEAD might be blocked or doesn't provide final info
        response = requests.get(url, allow_redirects=True, timeout=timeout)
        return response.url
    except requests.RequestException as e:
        print(f"Error expanding redirect for {url}: {e}")
        return url  # fallback to original

def confirm_same_destination(original_url: str, modified_url: str) -> bool:
    """
    Return True if original_url and modified_url resolve to the same final URL.
    """
    original_final = expand_redirect(original_url)
    modified_final = expand_redirect(modified_url)
    # Compare the final resolved URLs.
    # You could also compare response codes, content hashes, etc. if you want to be safer.
    return original_final == modified_final

def clean_tracking_params(url: str, removable_keys=None) -> str:
    """
    Removes known tracking/analytics query parameters from the URL.
    Then checks if it still leads to the same final page.
    
    If removing a parameter changes the final destination, we restore it.
    """
    if removable_keys is None:
        # Example known tracking parameters:
        removable_keys = ["utm_source", "utm_medium", "utm_campaign", "itm_source", "utm_term", "utm_content"]

    parsed = urlparse(url)
    query_params = parse_qs(parsed.query, keep_blank_values=True)

    # We'll build a mutable dict from query_params
    cleaned_params = dict(query_params)  # copy so we can remove keys

    for key in list(cleaned_params.keys()):
        if key in removable_keys:
            # Temporarily remove this key
            removed_value = cleaned_params.pop(key)
            
            # Rebuild the "trimmed" URL
            trimmed_query = urlencode(cleaned_params, doseq=True)
            trimmed_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                trimmed_query,
                parsed.fragment
            ))
            
            # Check if it still leads to the same final destination
            if not confirm_same_destination(url, trimmed_url):
                # If it's different, restore the parameter
                cleaned_params[key] = removed_value
    
    # Build the final cleaned URL
    final_query = urlencode(cleaned_params, doseq=True)
    cleaned_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        final_query,
        parsed.fragment
    ))
    return cleaned_url

def main():
    original_url = "https://www.youtube.com/watch?v=abc123#channel"
    
    print("Original:", original_url)
    
    # Clean tracking params
    cleaned_url = clean_tracking_params(original_url)
    
    print("Cleaned URL:", cleaned_url)
    
    # Show final expansion for each
    original_expanded = expand_redirect(original_url)
    cleaned_expanded = expand_redirect(cleaned_url)
    print("Original expanded final:", original_expanded)
    print("Cleaned expanded final:", cleaned_expanded)

    if original_expanded == cleaned_expanded:
        print("\nSuccess! Removing tracking parameters didn't change final destination.")
    else:
        print("\nWarning: The final destination changed. We restored any essential params.")

if __name__ == "__main__":
    main()