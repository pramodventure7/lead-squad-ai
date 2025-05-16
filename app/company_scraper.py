import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def extract_company_info(url):
    """
    Scrapes the homepage of a company to get basic company details and services offered.
    """
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.content, "html.parser")

    # Extract title
    title = soup.title.string.strip() if soup.title else "No title found"

    # Meta description
    description = ""
    desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
    if desc_tag and desc_tag.get("content"):
        description = desc_tag["content"]

    # Get visible services (basic logic, can be improved with LLM later)
    services = []
    for tag in soup.find_all(["h2", "h3", "p", "li"]):
        text = tag.get_text(strip=True)
        if any(word in text.lower() for word in ["solution", "services", "platform", "offering", "consulting"]):
            services.append(text)
        if len(services) > 10:
            break

    return {
        "title": title,
        "description": description,
        "services": services[:10],
    }


def find_job_links(base_url):
    """
    Attempts to find the careers page and extract job listing links.
    """
    try:
        response = requests.get(base_url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        links = soup.find_all("a", href=True)

        # Find careers page link
        career_url = None
        for link in links:
            href = link["href"].lower()
            if "career" in href or "jobs" in href:
                career_url = urljoin(base_url, link["href"])
                break

        # If no direct career link is found, try common career page paths
        if not career_url:
            for path in ["/careers", "/jobs", "/careers/job-openings"]:
                potential_url = urljoin(base_url, path)
                potential_response = requests.get(potential_url, timeout=10)
                if potential_response.status_code == 200:
                    career_url = potential_url
                    break

        job_links = []
        if career_url:
            job_response = requests.get(career_url, timeout=10)
            job_soup = BeautifulSoup(job_response.content, "html.parser")
            job_anchors = job_soup.find_all("a", href=True)

            for a in job_anchors:
                text = a.get_text(strip=True)
                href = a["href"]
                if len(text) > 5 and ("job" in href.lower() or "position" in href.lower()):
                    full_link = urljoin(career_url, href)
                    job_links.append((text, full_link))

        return career_url, job_links

    except Exception as e:
        return None, []


def get_cleaned_text(url):
    """
    Fetches and cleans the content of a given job posting URL.
    """
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.content, "html.parser")
    job_description = soup.find("div", class_="job-description")
    if job_description:
        return job_description.get_text(strip=True)
    return ""
