"""CLI entry point for the Upwork automation pipeline.

Runs the full workflow: scrapes jobs for a search term, classifies them against
the profile in ``files/profile.md``, and appends a personalised cover letter for
every match to ``files/cover_letter.txt``.

Usage:
    python main.py
    python main.py --job-title "LangChain Developer" --num-jobs 15
"""
import argparse

from dotenv import load_dotenv

from src.config import Config
from src.graph import UpworkAutomationGraph
from src.storage import read_profile


def parse_args():
    parser = argparse.ArgumentParser(description="Upwork automation pipeline")
    parser.add_argument(
        "--job-title",
        default=Config.DEFAULT_JOB_TITLE,
        help="Search term to look up on Upwork",
    )
    parser.add_argument(
        "--num-jobs",
        type=int,
        default=Config.DEFAULT_NUM_JOBS,
        help="Number of job listings to scrape",
    )
    return parser.parse_args()


def main():
    load_dotenv()
    args = parse_args()

    profile = read_profile()
    bot = UpworkAutomationGraph(profile, num_jobs=args.num_jobs)
    bot.run(args.job_title)

    print("\nDone. Cover letters saved to files/cover_letter.txt")


if __name__ == "__main__":
    main()