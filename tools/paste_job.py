"""Interactive CLI: paste a job description and get a cover letter.

Reads the description from stdin (paste it, press Enter twice to finish),
generates a cover letter and copies it to the clipboard when pyperclip is
available.

Usage:
    python tools/paste_job.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from src.cover_letter import CoverLetterGenerator
from src.storage import save_latest_letter

load_dotenv()


def read_multiline_input():
    """Read lines until an empty line follows a non-empty one."""
    lines = []
    while True:
        line = input()
        if not line and lines and not lines[-1]:
            break
        lines.append(line)
    return "\n".join(lines).strip()


def main():
    print("Paste the full Upwork job description, then press Enter twice:\n")
    job_description = read_multiline_input()

    if not job_description:
        print("No job description provided. Exiting.")
        return 1

    print("\nGenerating cover letter...\n")
    letter = CoverLetterGenerator().generate(job_description)

    print("=" * 70)
    print(letter)
    print("=" * 70)
    print(f"\nLength: {len(letter)} characters")

    try:
        import pyperclip

        pyperclip.copy(letter)
        print("Copied to clipboard - paste it into Upwork.")
    except ImportError:
        pass

    save_latest_letter(letter)
    print("Saved to files/latest_cover_letter.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())