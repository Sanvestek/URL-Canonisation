import requests
import hashlib
from bs4 import BeautifulSoup
from urllib.parse import (
    urlparse, urlunparse, parse_qs, urlencode
)

def get_html_structure_hash(url):
    try:
        response = requests.get(url, timeout=5, allow_redirects=True)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove all text and only keep the structural elements
        for tag in soup.find_all():
            tag.string = ""  # Remove inner text
        
        structure = str(soup)
        return hashlib.sha256(structure.encode("utf-8")).hexdigest()

    except requests.RequestException:
        return None  # Return None if request fails

# Compare two URLs
url1 = "https://www.linkedin.com/jobs/view/4072276680/?trackingId=HsJTLWIQTGO9o%2FE5pF0S%2Bw%3D%3D&refId=PRPmdWjWTCWNNRYk%2BP9JPw%3D%3D&midToken=AQGfdDCjrLGhkQ&midSig=1Lgo0gvQ3EMrA1&trk=eml-email_jobs_viewed_job_reminder_01-job_card-0-jobcard_body&trkEmail=eml-email_jobs_viewed_job_reminder_01-job_card-0-jobcard_body-null-gilcz4~m5zt912i~s3-null-null&eid=gilcz4-m5zt912i-s3&otpToken=MWIwYzE2ZTYxYTI2Y2RjZGIyMjQwNGVkNDUxOWU3YjI4ZmM3ZDg0MzllYWU4OTYxNzljNDA3Njk0NjVmNTlmMGZmZDBkZjllNzVmMGI5YzY3OWFjZWUwYjE4OTQ5NDI1YzYwOWU2ZGNjMzc2M2RjNjg4YmJmMiwxLDE%3D"
url2 = "https://www.linkedin.com/jobs/view/4072276680/"

print(get_html_structure_hash(url1) == get_html_structure_hash(url2))  # True if same structure

#returns an incorrect 'True' result if the request fails (e.g. No internet connection)

#All jobs/view/ posting have same structure, leading to false  'True' outputs