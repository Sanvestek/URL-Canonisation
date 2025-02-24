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

def apply_domain_specific_rules(url: str) -> str:
    """
    Applies special or custom logic for known domains like YouTube, Twitter, etc.
    For example, parse out the YouTube video ID and rebuild a canonical URL.
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Example for YouTube
    if "youtube.com" in domain or "youtu.be" in domain:
        # 1) Extract the video ID from different possible patterns
        query_params = parse_qs(parsed.query)

        # Regular expression to match a valid YouTube video ID
        video_id_pattern = re.compile(r'^[a-zA-Z0-9_-]+')

        # Cases:
        #   - youtube.com/watch?v=VIDEO_ID
        #   - youtube.com/v/VIDEO_ID
        #   - youtu.be/VIDEO_ID
        #   - short links, embedded links, etc.
        if "youtube.com/watch" in parsed.path:
            # Typically: https://www.youtube.com/watch?v=VIDEO_ID
            video_id = query_params.get("v", [""])[0]
        elif parsed.path.startswith("/v/"):
            # Typically: https://www.youtube.com/v/VIDEO_ID
            video_id = parsed.path.split("/")[2]
        elif "youtu.be" in domain:
            # Typically: https://youtu.be/VIDEO_ID
            # The video ID is in the first segment of the path
            video_id = parsed.path.lstrip("/")
        else:
            # Fallback, in case we don't detect anything
            video_id = ""

        # Validate and clean the video ID
        if video_id:
            # Extract only the valid part of the video ID
            match = video_id_pattern.match(video_id)
            if match:
                video_id = match.group(0)
                # Example canonical URL format:
                canonical_youtube = f"https://www.youtube.com/watch?v={video_id}"
                return canonical_youtube

    # For other domains, return the URL unchanged (or add more special cases)
    return url

def main():
    # Some example URLs:
    test_urls = [
      #  "HTTP://www.Example.com:80/path/", 
        "https://www.youtube.com/watch?v=abc123#channel",
      #  "https://youtu.be/abc123",
      #  "http://bit.ly/3kX2Example", 
      #  "https://www.EXAMPLE.com:443/path/?b=2&a=1#section"
    ]

    for original_url in test_urls:
        print(f"\nOriginal URL: {original_url}")
        
        # 1) Expand any redirects (short links, etc.)
        expanded = expand_redirect(original_url)
        print(f" After redirect expansion: {expanded}")

        # 2) Apply domain-specific rules (e.g., for YouTube)
        domain_adjusted = apply_domain_specific_rules(expanded)
        print(f" After domain-specific rules: {domain_adjusted}")

        # 3) Normalize the URL (lowercase, remove default ports, etc.)
        normalized = normalize_url(domain_adjusted)
        print(f" Final normalized URL: {normalized}")

if __name__ == "__main__":
    main()
