#!/usr/bin/env python3
"""
UnixPunks Hunter - Windows Compatible Version
With Schedule Info & Auto-Wait for Next Batch
"""

import requests
import random
import time
import json
import sys
import datetime
import os
from typing import Optional, Dict, Any, List

# Configuration
API = "https://unixpunks.xyz/api"
PROXIES_FILE = "proxies.txt"

# Built-in proxies (used if no proxies.txt file found)
BUILT_IN_PROXIES = [
    "142.111.48.253:7030:pudowlmy:b4o4d06k717e",
    "23.95.150.145:6114:pudowlmy:b4o4d06k717e",
    "45.38.107.97:6014:pudowlmy:b4o4d06k717e",
    "38.154.203.95:5863:pudowlmy:b4o4d06k717e",
    "198.23.243.226:6361:pudowlmy:b4o4d06k717e",
    "84.247.60.125:6095:pudowlmy:b4o4d06k717e",
    "104.239.107.47:5699:pudowlmy:b4o4d06k717e",
    "23.27.208.120:5830:pudowlmy:b4o4d06k717e",
    "23.229.19.94:8689:pudowlmy:b4o4d06k717e",
    "2.57.20.2:6983:pudowlmy:b4o4d06k717e",
]
DEFAULT_DELAY_MS = 200
REQUEST_TIMEOUT = 10
MAX_ATTEMPTS = 50000
SCHEDULE_CHECK_INTERVAL = 30  # seconds between schedule checks


class UnixPunksHunter:
    def __init__(self):
        self.proxies = []
        self.tried_timestamps = set()
        self.attempt_count = 0

    def load_proxies(self) -> None:
        """Load proxies from proxies.txt file or use built-in proxies"""
        raw_proxies = []

        # Try loading from file first
        try:
            if os.path.exists(PROXIES_FILE):
                with open(PROXIES_FILE, 'r', encoding='utf-8') as f:
                    raw_proxies = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
                if raw_proxies:
                    print(f"  Loaded {len(raw_proxies)} proxies from {PROXIES_FILE}")
        except Exception as e:
            print(f"  Error loading {PROXIES_FILE}: {e}")

        # Fall back to built-in proxies if no file found
        if not raw_proxies:
            raw_proxies = BUILT_IN_PROXIES
            print(f"  Using {len(raw_proxies)} built-in proxies")

        # Parse proxy format
        for proxy_line in raw_proxies:
            parts = proxy_line.split(":")
            if len(parts) >= 4:
                host, port, user, pw = parts[0], parts[1], parts[2], ":".join(parts[3:])
                proxy_url = f"http://{user}:{pw}@{host}:{port}"
            else:
                proxy_url = f"http://{proxy_line}"

            self.proxies.append({
                "http": proxy_url,
                "https": proxy_url
            })

        if self.proxies:
            print(f"  Total proxies ready: {len(self.proxies)}")
        else:
            print("  Running in DIRECT mode (no proxies)")
        print()

    def make_request(self, url: str, data: Optional[Dict] = None, silent: bool = False) -> Optional[Dict]:
        """Make HTTP request with proxy rotation and error handling"""
        proxy = random.choice(self.proxies) if self.proxies else None
        proxy_label = proxy['http'][:50].split("@")[-1] if proxy else "DIRECT"

        kwargs = {
            "timeout": REQUEST_TIMEOUT,
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        }

        if proxy:
            kwargs["proxies"] = proxy

        try:
            start_time = time.time()

            if data:
                kwargs["json"] = data
                kwargs["headers"]["Content-Type"] = "application/json"
                response = requests.post(url, **kwargs)
            else:
                response = requests.get(url, **kwargs)

            elapsed_ms = (time.time() - start_time) * 1000

            if not silent:
                print(f"  [{self.attempt_count:4d}] {proxy_label:30s} -> {response.status_code} in {elapsed_ms:.0f}ms", flush=True)

            return response.json()

        except requests.exceptions.ProxyError:
            if not silent:
                print(f"  [{self.attempt_count:4d}] {proxy_label:30s} -> PROXY AUTH FAIL", flush=True)
        except requests.exceptions.Timeout:
            if not silent:
                print(f"  [{self.attempt_count:4d}] {proxy_label:30s} -> TIMEOUT ({REQUEST_TIMEOUT}s)", flush=True)
        except requests.exceptions.ConnectionError:
            if not silent:
                print(f"  [{self.attempt_count:4d}] {proxy_label:30s} -> CONNECTION FAILED", flush=True)
        except Exception as e:
            if not silent:
                print(f"  [{self.attempt_count:4d}] {proxy_label:30s} -> {type(e).__name__}: {str(e)[:50]}", flush=True)

        return None

    def display_schedule(self, schedule: Dict) -> None:
        """Display full schedule information"""
        print()
        print("=" * 70)
        print("  UNIXPUNKS SCHEDULE INFO")
        print("=" * 70)

        # Active batch info
        active_batch = schedule.get("activeBatch")
        if active_batch:
            print(f"  Active Batch: {active_batch}")
        else:
            print(f"  Active Batch: NONE (no batch currently active)")

        # Next batch info
        next_batch = schedule.get("nextBatch")
        next_batch_time = schedule.get("nextBatchTimestamp") or schedule.get("nextBatchTime") or schedule.get("nextBatchAt")

        if next_batch:
            print(f"  Next Batch:   {next_batch}")
        if next_batch_time:
            # Try to convert timestamp to readable date
            try:
                if isinstance(next_batch_time, (int, float)):
                    # Could be seconds or milliseconds
                    if next_batch_time > 9999999999:
                        next_batch_time = next_batch_time / 1000
                    dt = datetime.datetime.fromtimestamp(next_batch_time)
                    now = datetime.datetime.now()
                    diff = dt - now
                    print(f"  Next Batch At: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    if diff.total_seconds() > 0:
                        hours = int(diff.total_seconds() // 3600)
                        minutes = int((diff.total_seconds() % 3600) // 60)
                        seconds = int(diff.total_seconds() % 60)
                        print(f"  Time Until Next: {hours}h {minutes}m {seconds}s")
                    else:
                        print(f"  Status: Should be active NOW!")
                else:
                    print(f"  Next Batch At: {next_batch_time}")
            except:
                print(f"  Next Batch At: {next_batch_time}")

        # Windows info
        windows = schedule.get("windows", [])
        if windows:
            print()
            print(f"  Windows ({len(windows)}):")
            print(f"  {'-' * 60}")
            for i, w in enumerate(windows):
                start_ts = w.get("tsRangeStart", "?")
                end_ts = w.get("tsRangeEnd", "?")
                total = w.get("timestampsCount", "?")
                consumed = w.get("consumedCount", 0)
                remaining = total - consumed if isinstance(total, int) and isinstance(consumed, int) else "?"

                # Convert timestamps to readable dates
                start_str = ""
                end_str = ""
                try:
                    if isinstance(start_ts, (int, float)):
                        ts_val = start_ts / 1000 if start_ts > 9999999999 else start_ts
                        start_str = f" ({datetime.datetime.fromtimestamp(ts_val).strftime('%Y-%m-%d %H:%M')})"
                except:
                    pass
                try:
                    if isinstance(end_ts, (int, float)):
                        ts_val = end_ts / 1000 if end_ts > 9999999999 else end_ts
                        end_str = f" ({datetime.datetime.fromtimestamp(ts_val).strftime('%Y-%m-%d %H:%M')})"
                except:
                    pass

                print(f"  Window {i+1}:")
                print(f"    Range Start:  {start_ts}{start_str}")
                print(f"    Range End:    {end_ts}{end_str}")
                print(f"    Total Codes:  {total}")
                print(f"    Consumed:     {consumed}")
                print(f"    Remaining:    {remaining}")
                print()
        else:
            print("  No windows found in schedule")

        # Show raw schedule for debugging
        print(f"  {'-' * 60}")
        print(f"  Raw API Response Keys: {list(schedule.keys())}")

        # Show any other fields we haven't displayed
        known_keys = {"activeBatch", "nextBatch", "nextBatchTimestamp", "nextBatchTime", "nextBatchAt", "windows"}
        extra_keys = set(schedule.keys()) - known_keys
        if extra_keys:
            print(f"  Additional Fields:")
            for key in extra_keys:
                val = schedule[key]
                val_str = str(val)[:100]
                print(f"    {key}: {val_str}")

        print("=" * 70)
        print()

    def wait_for_batch(self) -> Optional[Dict]:
        """Wait and poll until an active batch is available"""
        print()
        print("  No active batch right now. Entering WATCH MODE...")
        print(f"  Checking every {SCHEDULE_CHECK_INTERVAL} seconds for new batch...")
        print(f"  Press Ctrl+C to stop waiting")
        print()

        check_count = 0
        while True:
            check_count += 1
            now = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"  [{now}] Check #{check_count} - Fetching schedule...", end="", flush=True)

            schedule = self.make_request(f"{API}/schedule", silent=True)

            if schedule and schedule.get("activeBatch"):
                print(f" BATCH FOUND!")
                print(f"\n  NEW BATCH DETECTED!")
                return schedule
            elif schedule:
                next_info = ""
                next_ts = schedule.get("nextBatchTimestamp") or schedule.get("nextBatchTime") or schedule.get("nextBatchAt")
                if next_ts:
                    try:
                        if isinstance(next_ts, (int, float)):
                            if next_ts > 9999999999:
                                next_ts = next_ts / 1000
                            dt = datetime.datetime.fromtimestamp(next_ts)
                            diff = dt - datetime.datetime.now()
                            if diff.total_seconds() > 0:
                                mins = int(diff.total_seconds() // 60)
                                secs = int(diff.total_seconds() % 60)
                                next_info = f" (next in {mins}m {secs}s)"
                    except:
                        pass
                print(f" No active batch{next_info}")
            else:
                print(f" API unreachable")

            time.sleep(SCHEDULE_CHECK_INTERVAL)

    def get_user_input(self) -> tuple:
        """Get delay and wallet address from user"""
        print()
        while True:
            try:
                delay_input = input(f"  Delay between attempts in ms (default {DEFAULT_DELAY_MS}): ").strip()
                delay_ms = float(delay_input) if delay_input else DEFAULT_DELAY_MS
                if delay_ms < 0:
                    print("  Delay must be positive")
                    continue
                break
            except ValueError:
                print("  Please enter a valid number")

        delay_seconds = delay_ms / 1000
        print(f"  Using {delay_ms:.0f}ms delay")
        print()

        while True:
            wallet = input("  Wallet (0x...): ").strip()

            if (len(wallet) == 42 and
                wallet.startswith("0x") and
                all(c in "0123456789abcdefABCDEF" for c in wallet[2:])):
                break
            else:
                print("  Invalid wallet. Must be 42 chars starting with 0x")

        return delay_seconds, wallet

    def hunt_mint_code(self, start_ts: int, end_ts: int, wallet: str, delay: float) -> None:
        """Main hunting loop"""
        print(f"\n  Starting hunt with {delay*1000:.0f}ms delay")
        print("=" * 70)

        while True:
            # Generate random timestamp
            timestamp = random.randint(start_ts, end_ts)
            while timestamp in self.tried_timestamps:
                timestamp = random.randint(start_ts, end_ts)

            self.tried_timestamps.add(timestamp)
            self.attempt_count += 1

            # Make the request
            result = self.make_request(
                f"{API}/find-mint-code",
                data={"timestamp": timestamp, "wallet": wallet}
            )

            if result is None:
                time.sleep(0.2)
                continue

            # SUCCESS!
            if result.get("ok"):
                self.print_success(timestamp, result.get("mintCode", "N/A"))
                break

            # Handle MISS
            elif not result.get("ok") and result.get("error") not in ("rate_limit", "rate_limit_wallet"):
                # Normal miss - just continue
                pass

            # Rate limited
            elif result.get("error") in ("rate_limit", "rate_limit_wallet"):
                retry_ms = result.get("retryInMs", 1000)
                print(f"  RATE LIMITED - retryInMs={retry_ms}", flush=True)
                time.sleep(retry_ms / 1000)
                continue

            # Max attempts check
            if self.attempt_count >= MAX_ATTEMPTS:
                print(f"\n  Stopping after {MAX_ATTEMPTS} attempts")
                break

            time.sleep(delay)

    def print_success(self, timestamp: int, mint_code: str) -> None:
        """Print success message"""
        print(f"\n{'=' * 70}")
        print(f"  HIT at timestamp {timestamp} after {self.attempt_count} tries!")
        print(f"  mintCode: {mint_code}")
        print(f"  Go mint at https://unixpunks.xyz")
        print(f"{'=' * 70}")

    def run(self) -> None:
        """Main execution flow"""
        print()
        print("=" * 70)
        print("  UNIXPUNKS HUNTER - Windows Edition (with Schedule Info)")
        print("=" * 70)
        print()

        # Load proxies
        self.load_proxies()

        # Fetch schedule
        print("  Fetching schedule...")
        schedule = self.make_request(f"{API}/schedule", silent=False)

        if not schedule:
            print("\n  API unreachable. Check your internet connection.")
            input("  Press Enter to exit...")
            return

        # Always display full schedule info
        self.display_schedule(schedule)

        # Check if batch is active
        if not schedule.get("activeBatch"):
            print("  No active batch right now!")
            print()
            choice = input("  Options:\n    [1] Wait for next batch (auto-check every 30s)\n    [2] Exit\n  Choose (1/2): ").strip()

            if choice == "2":
                print("  Goodbye!")
                return

            # Wait for batch
            schedule = self.wait_for_batch()
            if not schedule:
                return

            # Show updated schedule
            self.display_schedule(schedule)

        # Parse active window
        window = schedule["windows"][0]
        start_ts = window["tsRangeStart"]
        end_ts = window["tsRangeEnd"]
        total = window.get("timestampsCount", "?")
        consumed = window.get("consumedCount", 0)

        print(f"  Batch {schedule['activeBatch']} is ACTIVE!")
        print(f"  Range: {start_ts} - {end_ts}")
        print(f"  Winners: {total}")
        print(f"  Consumed: {consumed}")
        if isinstance(total, int) and isinstance(consumed, int):
            print(f"  Remaining: {total - consumed}")
        print()

        # Get user input
        delay, wallet = self.get_user_input()

        print(f"\n  Configuration:")
        print(f"    Wallet:  {wallet}")
        print(f"    Delay:   {delay * 1000:.0f}ms")
        print(f"    Proxies: {len(self.proxies)}")

        input("\n  Press Enter to start hunting...")

        # Hunt!
        try:
            self.hunt_mint_code(start_ts, end_ts, wallet, delay)
        except KeyboardInterrupt:
            print(f"\n\n  Stopped by user after {self.attempt_count} attempts")
            print("  Goodbye!")


if __name__ == "__main__":
    try:
        hunter = UnixPunksHunter()
        hunter.run()
    except KeyboardInterrupt:
        print("\n\n  Goodbye!")
    except Exception as e:
        print(f"\n  Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        input("  Press Enter to exit...")
