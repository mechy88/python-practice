# Project Plan

## Phase 1: Environment & Architecture (Day 1)

> **Goal:** Set up the "Linux command" feel required by the project.

- **Project Initialization:** Create your directory structure with a virtual environment (`venv`).
- **CLI Skeleton:** Use `argparse` to define your command line options:
    - `--today`: Flag to fetch the latest files.
    - `--date YYYY-MM-DD`: Option to fetch historical files.
    - `--config`: Option to point to a custom configuration file.
- **Logging Setup:** Configure the `logging` module to output `INFO` to stdout and `DEBUG` to a `downloader.log` file.

---

## Phase 2: The Scraper Engine (Day 2)

> **Goal:** Handle the SGX website's specific data.

- **URL Mapping:** Identify the URL structure for the four required files:
    - `WEBPXTICK_DT`
    - `TickData_structure`
    - `TC_*.txt`
    - `TC_structure.dat`
- **Request Handling:**
    - Use `requests` for direct file downloads.
    - Use `Playwright` or `Selenium` if the SGX derivatives page requires clicking buttons to reveal download links.
- **File Management:** Create a naming convention that includes the date so files don't overwrite each other (e.g., `data/2026-02-02/TC_20260202.txt`).

---

## Phase 3: Reliability & Recovery Logic (Day 3)

> **Goal:** Handle failures gracefully (heavy emphasis in requirements).

### The "Recovery Plan" Logic

| Type | Description |
|------|-------------|
| **Manual Recovery** | If a user inputs a past date, the script specifically targets that day's files. |
| **Automatic Recovery** | A "Backfill" function checks the last 5 days in your local folder; if a file is missing, it automatically attempts to download it. |

- **Integrity Checks:** After downloading, log the file size. If a file is 0KB, log a `WARNING` and trigger a retry.

---

## Phase 4: Refinement & Testing (Day 4)

- **Error Handling:** Use `try-except` blocks for network timeouts or "File Not Found" errors on the SGX side.
- **Edge Case Testing:**
    - What happens if it's a weekend/holiday and SGX doesn't publish? *(Your script should log this gracefully.)*
    - Can it download "older files" not on the front page? *(Test if your URL-guessing logic works.)*

---

## Phase 5: Documentation & Submission (Day 5)

- **README:** Explain how to install dependencies and run the command (e.g., `python main.py --today`).
- **Code Cleanup:** Ensure your Python code follows **PEP 8** standards.
- **Final Package:** Create the `.zip` or `.tar.gz` and email it to `careers@dytechlab.com` with the specific subject line requested.

---

## Suggested Directory Structure

```
/miguel_pajarillo_project
│
├── main.py            # Entry point (CLI logic)
├── scraper.py         # SGX-specific download logic
├── utils.py           # Logging config & recovery helpers
├── requirements.txt   # List of libraries
└── README.md          # Instructions
```