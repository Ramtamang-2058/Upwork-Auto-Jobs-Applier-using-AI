"""LangGraph pipeline that drives the Upwork automation workflow.

Flow: scrape jobs -> classify against profile -> generate + save cover letters
for every match, until none remain.
"""
from typing import List
from typing_extensions import TypedDict

from langgraph.graph import END, StateGraph

from .config import Config
from .cover_letter import CoverLetterGenerator, JobClassifier
from .scraper import scrape_upwork_data
from .storage import append_cover_letter, save_jobs_to_file

from colorama import Fore, Style


class GraphState(TypedDict):
    job_title: str
    scraped_jobs_list: str
    matches: List[dict]
    job_description: str
    cover_letter: str


class UpworkAutomationGraph:
    def __init__(self, profile, num_jobs=None):
        self.profile = profile
        self.number_of_jobs = num_jobs or Config.DEFAULT_NUM_JOBS
        self.classifier = JobClassifier(profile=profile)
        self.writer = CoverLetterGenerator(profile=profile)
        self.graph = self.build_graph()

    # --- Nodes --------------------------------------------------------------

    def scrape_upwork_jobs(self, state):
        job_title = state["job_title"]
        print(
            Fore.YELLOW
            + f"----- Scraping Upwork jobs for: {job_title} -----\n"
            + Style.RESET_ALL
        )
        job_listings = scrape_upwork_data(job_title, self.number_of_jobs)
        print(
            Fore.GREEN
            + f"----- Scraped {len(job_listings)} jobs -----\n"
            + Style.RESET_ALL
        )
        save_jobs_to_file(job_listings)
        jobs_text = "\n".join(map(str, job_listings))
        return {**state, "scraped_jobs_list": jobs_text}

    def classify_scraped_jobs(self, state):
        print(Fore.YELLOW + "----- Classifying scraped jobs -----\n" + Style.RESET_ALL)
        matches = self.classifier.classify(state["scraped_jobs_list"])
        return {**state, "matches": matches}

    def check_for_job_matches(self, state):
        count = len(state["matches"])
        if count == 0:
            print(Fore.RED + "No job matches\n" + Style.RESET_ALL)
            return "No matches"
        print(Fore.GREEN + f"{count} job matches to process\n" + Style.RESET_ALL)
        return "Process jobs"

    def generate_cover_letter(self, state):
        print(Fore.YELLOW + "----- Generating cover letter -----\n" + Style.RESET_ALL)
        job_description = str(state["matches"][-1])
        cover_letter = self.writer.generate(job_description)
        return {
            **state,
            "cover_letter": cover_letter,
            "job_description": job_description,
        }

    def save_cover_letter(self, state):
        print(Fore.YELLOW + "----- Saving cover letter -----\n" + Style.RESET_ALL)
        append_cover_letter(state["cover_letter"])
        matches = list(state["matches"])
        matches.pop()
        return {**state, "matches": matches}

    # --- Graph --------------------------------------------------------------

    def build_graph(self):
        graph = StateGraph(GraphState)

        graph.add_node("scrape_upwork_jobs", self.scrape_upwork_jobs)
        graph.add_node("classify_scraped_jobs", self.classify_scraped_jobs)
        graph.add_node("generate_cover_letter", self.generate_cover_letter)
        graph.add_node("save_cover_letter", self.save_cover_letter)

        graph.set_entry_point("scrape_upwork_jobs")
        graph.add_edge("scrape_upwork_jobs", "classify_scraped_jobs")
        graph.add_conditional_edges(
            "classify_scraped_jobs",
            self.check_for_job_matches,
            {"Process jobs": "generate_cover_letter", "No matches": END},
        )
        graph.add_edge("generate_cover_letter", "save_cover_letter")
        graph.add_edge("save_cover_letter", "classify_scraped_jobs")

        return graph.compile()

    def run(self, job_title):
        print(
            Fore.BLUE + "----- Running Upwork Jobs Automation -----\n" + Style.RESET_ALL
        )
        return self.graph.invoke({"job_title": job_title})