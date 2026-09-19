"""Upwork job scraping using Selenium.

Note: Upwork actively changes its DOM and guards against automated access, so
this scraper may need selector updates over time.
"""
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

JOBS_URL = (
    "https://www.upwork.com/nx/search/jobs?q={query}"
    "&sort=recency&page=1&per_page={num_jobs}"
)


def scrape_upwork_data(search_query, num_jobs=10, headless=False):
    """Open Upwork search and return a list of job dicts."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    job_listings = []
    try:
        driver.get(JOBS_URL.format(query=search_query, num_jobs=num_jobs))
        time.sleep(5)

        jobs = driver.find_elements(By.CSS_SELECTOR, 'article[data-test="JobTile"]')
        for job in jobs:
            try:
                parsed = _parse_job_tile(job)
                if parsed:
                    job_listings.append(parsed)
            except Exception as exc:
                print(f"Error parsing job listing: {exc}")
                continue
    finally:
        driver.quit()

    return job_listings


def _parse_job_tile(job):
    title_element = job.find_element(By.CSS_SELECTOR, "h2.job-tile-title > a")
    title = title_element.text.strip()
    link = title_element.get_attribute("href")

    description = job.find_element(
        By.CSS_SELECTOR, "div[data-test='JobTileDetails'] > div > div > p"
    ).text.strip()

    job_info = job.find_element(By.CSS_SELECTOR, "ul.job-tile-info-list")
    job_type = job_info.find_element(
        By.CSS_SELECTOR, "li[data-test='job-type-label']"
    ).text.strip()
    experience_level = job_info.find_element(
        By.CSS_SELECTOR, "li[data-test='experience-level']"
    ).text.strip()

    try:
        budget = job_info.find_element(
            By.CSS_SELECTOR, "li[data-test='is-fixed-price']"
        ).text.strip()
    except Exception:
        budget = job_info.find_element(
            By.CSS_SELECTOR, "li[data-test='duration-label']"
        ).text.strip()

    return {
        "title": title,
        "link": link,
        "description": description,
        "job_type": job_type,
        "experience_level": experience_level,
        "budget": budget,
    }