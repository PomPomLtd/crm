#!/usr/bin/env python3

import csv
import time
import random
import os
import sys
import requests
import signal
import curses
import queue
import threading
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque

# =============================
# Global config & constants
# =============================
API_KEY = "VQxddzhtWBd9ANBGbtLGd3dk"
SEARCH_URL = "https://www.searchapi.io/api/v1/search"
banned_domains = ["onedoc.ch", "comparis.ch", "doktor.ch"]

# We'll communicate progress via a Queue
progress_queue = queue.Queue()

# We track the number of rate limit errors globally
rate_limit_errors = 0

# A global stop_event to indicate we want to shut down (Ctrl+C pressed)
stop_event = threading.Event()

def format_time(seconds: float) -> str:
    """Convert seconds to H:MM:SS format."""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:d}:{m:02d}:{s:02d}"

# ---------------------------------------
# Core logic for fetching and checking
# ---------------------------------------
def fetch_company_url(company_name, city, max_retries=3):
    global rate_limit_errors

    query = company_name
    if city and city.lower() not in company_name.lower():
        query += f" {city}"

    attempt = 0
    while attempt < max_retries:
        if stop_event.is_set():
            # If we’re stopping, just return an empty URL
            return ""
        try:
            params = {
                "engine": "google",
                "q": query,
                "api_key": API_KEY,
                "num": 1
            }
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/115.0 Safari/537.36"
                )
            }
            response = requests.get(SEARCH_URL, params=params, headers=headers, timeout=35)
            if response.status_code in [429, 403]:
                raise requests.exceptions.RequestException(
                    f"Rate limit / Block encountered (status {response.status_code})"
                )
            response.raise_for_status()
            data = response.json()
            if "organic_results" in data and len(data["organic_results"]) > 0:
                return data["organic_results"][0].get("link", "")
            return ""
        except requests.exceptions.RequestException:
            rate_limit_errors += 1
            wait_time = random.uniform(5, 10) * (attempt + 1)
            time.sleep(wait_time)
            attempt += 1
    return ""

def check_zuweisung(url):
    """
    GET the webpage (timeout=35s) and look for presence of certain German/French keywords.
    Return (flag, triggered_keywords) where flag=1 if any are found.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=35)
        if resp.status_code != 200:
            return 0, []
        content = resp.text.lower()
        german_keywords = ["zuweisung", "überweisung", "zuweiser", "für ärzte"]
        french_keywords = ["référence", "pour médecins"]
        all_keywords = german_keywords + french_keywords

        triggered = [kw for kw in all_keywords if kw.lower() in content]
        flag = 1 if triggered else 0
        return flag, triggered
    except Exception:
        return 0, []

def is_banned_url(url):
    """Check if URL domain matches any banned domain substrings."""
    try:
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        for banned in banned_domains:
            if banned in domain:
                return True
        return False
    except Exception:
        return False

def process_one_row(index, row, last_processed_deque):
    if stop_event.is_set():
        return index, row

    company_name = row.get("name", "").strip()
    city = row.get("city", "").strip()
    if not company_name:
        row["official_website"] = ""
        row["Zuweisung"] = 0
        row["Triggered_Keywords"] = ""
        return index, row

    url = fetch_company_url(company_name, city)
    if url and is_banned_url(url):
        url = ""
        zuweisung_flag, triggered_keywords = 0, []
    else:
        if url:
            zuweisung_flag, triggered_keywords = check_zuweisung(url)
        else:
            zuweisung_flag, triggered_keywords = 0, []

    row["official_website"] = url
    row["Zuweisung"] = zuweisung_flag
    row["Triggered_Keywords"] = ", ".join(triggered_keywords)

    short_url = url if len(url) < 60 else (url[:57] + "...")
    last_processed_deque.append((company_name, short_url))

    return index, row

# ---------------------------------------
# Graceful Worker Thread
# ---------------------------------------
def worker_thread(
    rows_to_process,
    total_rows,
    already_processed_count,
    start_time,
    all_rows,
    output_file
):
    """
    1) Submits tasks to ThreadPoolExecutor
    2) On each finished row, sends PROGRESS to the queue (including the last processed URLs)
    3) Writes the row to CSV immediately after it is processed
    4) If stop_event is set, we do a graceful shutdown
    5) Otherwise, once all tasks done, we send 'DONE'
    """
    updated_rows = [None] * total_rows
    to_process_count = len(rows_to_process)
    row_durations = []
    active_count = 0

    # We'll keep a ring buffer of the last 5 processed items
    last_processed_deque = deque(maxlen=5)

    # Prepare CSV writing:
    # Build fieldnames from the entire dataset
    fieldnames = list(all_rows[0].keys())
    for new_col in ["official_website", "Zuweisung", "Triggered_Keywords"]:
        if new_col not in fieldnames:
            fieldnames.append(new_col)

    # Open the output file once in append mode
    file_is_empty = (not os.path.exists(output_file)) or (os.stat(output_file).st_size == 0)
    csvfile = open(output_file, 'a', newline='', encoding='utf-8')
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    if file_is_empty:
        writer.writeheader()
    write_lock = threading.Lock()

    # Use a thread pool to process each row
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_map = {}
        for (i, row) in rows_to_process:
            f = executor.submit(process_one_row, i, row, last_processed_deque)
            future_map[f] = i

        for future in as_completed(future_map):
            if stop_event.is_set():
                executor.shutdown(wait=False, cancel_futures=True)
                csvfile.close()
                progress_queue.put({"type": "CANCEL"})
                return

            row_start = time.time()
            idx, updated_row = future.result()
            updated_rows[idx] = updated_row

            # Write to CSV immediately
            with write_lock:
                writer.writerow(updated_row)
                csvfile.flush()

            active_count += 1
            row_duration = time.time() - row_start
            row_durations.append(row_duration)

            # Stats for the UI
            elapsed = time.time() - start_time
            avg_time = sum(row_durations) / len(row_durations)
            remaining_active = to_process_count - active_count
            est_remaining_sec = avg_time * remaining_active

            progress_dict = {
                "type": "PROGRESS",
                "processed_this_run": active_count,
                "initial_active": to_process_count,
                "total_rows": total_rows,
                "elapsed": elapsed,
                "avg_time": avg_time,
                "estimated_remaining": est_remaining_sec,
                "rate_limit_errors": rate_limit_errors,
                "already_processed": already_processed_count,
                "last_urls": list(last_processed_deque),
            }
            progress_queue.put(progress_dict)

    csvfile.close()  # Done writing
    done_dict = {
        "type": "DONE",
        "updated_rows": updated_rows,
        "row_durations": row_durations
    }
    progress_queue.put(done_dict)

# ---------------------------------------
# Curses-based dashboard
# ---------------------------------------
def draw_dashboard(stdscr, stats):
    stdscr.erase()  # clear screen

    title_color = curses.color_pair(1)
    highlight_color = curses.color_pair(2)
    progress_bar_color = curses.color_pair(3)
    url_color = curses.color_pair(4)

    stdscr.addstr(0, 0, "=== Real-time Search Progress Dashboard ===", title_color | curses.A_BOLD)

    processed_this_run = stats.get("processed_this_run", 0)
    initial_active = stats.get("initial_active", 0)
    total_rows = stats.get("total_rows", 0)
    already_processed = stats.get("already_processed", 0)
    elapsed = stats.get("elapsed", 0)
    avg_time = stats.get("avg_time", 0.0)
    estimated_remaining = stats.get("estimated_remaining", 0.0)
    rate_errors = stats.get("rate_limit_errors", 0)
    last_urls = stats.get("last_urls", [])

    progress_percent = 100.0
    if initial_active > 0:
        progress_percent = (processed_this_run / initial_active) * 100
    total_processed = already_processed + processed_this_run

    row = 2
    stdscr.addstr(row, 0, f"Total rows in file      : {total_rows}", highlight_color)
    row += 1
    stdscr.addstr(row, 0, f"Already processed       : {already_processed}", highlight_color)
    row += 1
    stdscr.addstr(row, 0, f"Processing this run     : {processed_this_run} / {initial_active} ({progress_percent:.2f}%)", highlight_color)
    row += 1
    stdscr.addstr(row, 0, f"Total processed so far  : {total_processed}", highlight_color)
    row += 1
    stdscr.addstr(row, 0, f"Elapsed time            : {format_time(elapsed)}", highlight_color)
    row += 1
    stdscr.addstr(row, 0, f"Avg time per row        : {avg_time:.2f} s", highlight_color)
    row += 1
    stdscr.addstr(row, 0, f"Estimated time left     : {format_time(estimated_remaining)}", highlight_color)
    row += 1
    stdscr.addstr(row, 0, f"Rate-limit errors       : {rate_errors}", highlight_color)

    row += 2
    bar_width = 50
    filled = int(bar_width * progress_percent / 100)
    bar_str = "[" + ("#" * filled) + ("-" * (bar_width - filled)) + "]"
    stdscr.addstr(row, 0, f"Progress: {bar_str} {progress_percent:.2f}%", progress_bar_color)

    row += 2
    stdscr.addstr(row, 0, "Recently Processed (up to 5):", title_color | curses.A_BOLD)
    row += 1
    for (company, url) in last_urls:
        display_str = f" • {company} => {url}"
        stdscr.addstr(row, 0, display_str, url_color)
        row += 1

    stdscr.refresh()

def curses_dashboard(stdscr, all_rows, rows_to_process, total_rows, already_processed, output_file):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    curses.curs_set(0)  # hide cursor

    start_time = time.time()

    worker = threading.Thread(
        target=worker_thread,
        args=(rows_to_process, total_rows, already_processed, start_time, all_rows, output_file),
        daemon=True
    )
    worker.start()

    current_stats = {
        "type": "PROGRESS",
        "processed_this_run": 0,
        "initial_active": len(rows_to_process),
        "total_rows": total_rows,
        "elapsed": 0.0,
        "avg_time": 0.0,
        "estimated_remaining": 0.0,
        "rate_limit_errors": 0,
        "already_processed": already_processed,
        "last_urls": []
    }

    updated_rows_final = None

    while True:
        if stop_event.is_set():
            break

        try:
            msg = progress_queue.get(timeout=0.1)
            if msg["type"] == "PROGRESS":
                current_stats.update(msg)
            elif msg["type"] == "DONE":
                updated_rows_final = msg["updated_rows"]
                break
            elif msg["type"] == "CANCEL":
                break
        except queue.Empty:
            pass

        draw_dashboard(stdscr, current_stats)

        # If worker finished but no DONE message, break
        if not worker.is_alive() and updated_rows_final is None:
            break

    draw_dashboard(stdscr, current_stats)
    worker.join(timeout=1.0)
    return updated_rows_final, current_stats

# ---------------------------------------
# Signal handler for Ctrl+C
# ---------------------------------------
def handle_sigint(signal_number, frame):
    stop_event.set()

def final_summary(final_stats, total_rows):
    elapsed = final_stats.get("elapsed", 0)
    processed_this_run = final_stats.get("processed_this_run", 0)
    initial_active = final_stats.get("initial_active", 0)
    avg_time = final_stats.get("avg_time", 0)
    estimated_remaining = final_stats.get("estimated_remaining", 0)
    final_rate_errors = final_stats.get("rate_limit_errors", 0)
    already_processed_count = final_stats.get("already_processed", 0)
    progress_percent = (
        (processed_this_run / initial_active) * 100 if initial_active else 100
    )
    total_processed = already_processed_count + processed_this_run

    print("\n======== FINAL SUMMARY ========")
    print(f"Total elements in file   : {total_rows}")
    print(f"Already processed        : {already_processed_count}")
    print(f"Processed this run       : {processed_this_run}/{initial_active} ({progress_percent:.2f}%)")
    print(f"Total processed so far   : {total_processed}")
    print(f"Average time per row     : {avg_time:.2f} s")
    print(f"Estimated time remaining : {format_time(estimated_remaining)}")
    print(f"Total elapsed time       : {format_time(elapsed)}")
    print(f"Rate limit errors        : {final_rate_errors}")
    print("=============================\n")

# ---------------------------------------
# Main entry point
# ---------------------------------------
def main_curses(stdscr):
    input_file = "all_medical_centers.csv"
    output_file = "all_medical_centers_with_urls.csv"

    with open(input_file, newline='', encoding='utf-8') as infile:
        all_rows = list(csv.DictReader(infile))
    total_rows = len(all_rows)

    # Already processed
    processed_names = set()
    if os.path.exists(output_file):
        with open(output_file, newline='', encoding='utf-8') as outfile:
            reader = csv.DictReader(outfile)
            for row in reader:
                if row.get("name"):
                    processed_names.add(row["name"])
    already_processed_count = len(processed_names)

    # Collect those that need processing
    rows_to_process = []
    for i, row in enumerate(all_rows):
        name = row.get("name", "").strip()
        if name not in processed_names:
            rows_to_process.append((i, row))

    updated_rows, final_stats = curses_dashboard(
        stdscr, all_rows, rows_to_process, total_rows, already_processed_count, output_file
    )

    # ----------------------------------------------------------------------
    # If you do NOT want to rewrite all processed rows at the end (because
    # you're already appending them one by one in worker_thread), comment
    # out the block below to avoid duplicate rows in the CSV:
    # ----------------------------------------------------------------------
    """
    if updated_rows is not None:
        # Gather only newly processed
        fieldnames = list(all_rows[0].keys())
        for new_col in ["official_website", "Zuweisung", "Triggered_Keywords"]:
            if new_col not in fieldnames:
                fieldnames.append(new_col)

        newly_processed = []
        for i in range(total_rows):
            if updated_rows[i] is not None:
                newly_processed.append(updated_rows[i])

        if newly_processed:
            file_is_empty = (not os.path.exists(output_file)) or (os.stat(output_file).st_size == 0)
            with open(output_file, 'a', newline='', encoding='utf-8') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                if file_is_empty:
                    writer.writeheader()
                for r in newly_processed:
                    writer.writerow(r)
    """

    if not final_stats:
        final_stats = {
            "processed_this_run": 0,
            "initial_active": len(rows_to_process),
            "avg_time": 0.0,
            "estimated_remaining": 0.0,
            "elapsed": 0.0,
            "rate_limit_errors": rate_limit_errors,
            "already_processed": already_processed_count
        }
    final_summary(final_stats, total_rows)

def main():
    signal.signal(signal.SIGINT, handle_sigint)
    curses.wrapper(main_curses)

if __name__ == "__main__":
    main()
