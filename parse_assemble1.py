import re
from urllib.parse import urlparse

def get_video_id_custom(url: str) -> str:
    """
    This function looks for 'v=' in the URL's query and captures
    everything until it hits &, #, or /.
    """
    parsed = urlparse(url)
    query_str = parsed.query  # e.g., "v=abc123#blah" or "v=abc123&foo=bar"

    # Our regex looks for v= then captures all non-&/#/ characters
    pattern = re.compile(r"v=([^&#/?]+)")
    match = pattern.search(query_str)
    if match:
        # group(1) is what was captured between 'v=' and the special character
        return match.group(1)
    else:
        return ""

# Example usage:
test_urls = [
    "https://www.youtube.com/watch?v=abc123#some_fragment",
    "https://www.youtube.com/watch?v=abc123&feature=share",
    "https://www.youtube.com/watch?v=abc123?0t57y/",
    "https://www.youtube.com/watch?v=abc123?something=else",
    "https://youtu.be/watch?v=abc123&1##",
    "https://www.youtube.com/watch?v=abc123&#crap",
    "https://www.youtube.com/watch?v=Rkuk1XQGHeg&ab_channel=Mda"  # This won't match v=, so we get an empty string
]

for url in test_urls:
    video_id = get_video_id_custom(url)
    print(f"URL: {url}\nExtracted Video ID: {video_id}\n")
