#!/usr/bin/env python3
"""
Free Proxy Fetcher for UnixPunks Hunter
Downloads and tests free proxies, saves working ones to proxies.txt
"""

import requests
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# Free proxy sources (updated regularly)
PROXY_SOURCES = [
    # proxifly - Updated every 5 minutes
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
    # TheSpeedX - Updated daily
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    # clarketm
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    # ShiftyTR
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    # monosans
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    # hookzof
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
]

TEST_URL = "https://unixpunks.xyz/api/schedule"
TEST_TIMEOUT = 5  # seconds
MAX_WORKERS = 20  # concurrent proxy tests


def fetch_proxies():
    """Download proxy lists from multiple sources"""
    all_proxies = set()
    
    print("=" * 60)
    print("  FREE PROXY FETCHER")
    print("=" * 60)
    print()
    print("  Downloading proxy lists...")
    print()
    
    for source_url in PROXY_SOURCES:
        source_name = source_url.split("/")[4] if "github" in source_url else source_url[:50]
        try:
            r = requests.get(source_url, timeout=10)
            if r.status_code == 200:
                lines = [line.strip() for line in r.text.splitlines() if line.strip()]
                # Filter valid proxy format (ip:port)
                valid = []
                for line in lines:
                    parts = line.split(":")
                    if len(parts) >= 2 and parts[0].replace(".", "").isdigit():
                        valid.append(line)
                all_proxies.update(valid)
                print(f"  [OK] {source_name}: {len(valid)} proxies")
            else:
                print(f"  [FAIL] {source_name}: HTTP {r.status_code}")
        except Exception as e:
            print(f"  [FAIL] {source_name}: {str(e)[:40]}")
    
    print(f"\n  Total unique proxies found: {len(all_proxies)}")
    return list(all_proxies)


def test_proxy(proxy_str):
    """Test if a proxy works with the UnixPunks API"""
    proxy_url = f"http://{proxy_str}"
    proxies = {"http": proxy_url, "https": proxy_url}
    
    try:
        r = requests.get(
            TEST_URL,
            proxies=proxies,
            timeout=TEST_TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        if r.status_code == 200:
            elapsed = r.elapsed.total_seconds() * 1000
            return proxy_str, True, elapsed
        else:
            return proxy_str, False, 0
    except:
        return proxy_str, False, 0


def test_proxies(proxy_list, max_test=100):
    """Test proxies concurrently and return working ones"""
    print()
    print(f"  Testing proxies against UnixPunks API...")
    print(f"  Testing up to {max_test} proxies with {MAX_WORKERS} threads...")
    print()
    
    # Limit how many we test
    to_test = proxy_list[:max_test]
    working = []
    tested = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(test_proxy, p): p for p in to_test}
        
        for future in as_completed(futures):
            tested += 1
            proxy_str, success, speed = future.result()
            
            if success:
                working.append((proxy_str, speed))
                print(f"  [{tested:4d}/{len(to_test)}] {proxy_str:25s} -> OK ({speed:.0f}ms)")
            else:
                # Only show every 10th failure to reduce noise
                if tested % 10 == 0:
                    print(f"  [{tested:4d}/{len(to_test)}] Testing... ({len(working)} working so far)")
    
    # Sort by speed (fastest first)
    working.sort(key=lambda x: x[1])
    return working


def save_proxies(working_proxies, filename="proxies.txt"):
    """Save working proxies to file"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# Free proxies - fetched at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total working: {len(working_proxies)}\n")
        f.write(f"# Format: ip:port (sorted by speed, fastest first)\n")
        f.write("#\n")
        for proxy_str, speed in working_proxies:
            f.write(f"{proxy_str}\n")
    
    print(f"\n  Saved {len(working_proxies)} working proxies to {filename}")


def main():
    print()
    
    # Step 1: Fetch proxy lists
    all_proxies = fetch_proxies()
    
    if not all_proxies:
        print("\n  No proxies found. Check your internet connection.")
        input("  Press Enter to exit...")
        return
    
    # Step 2: Ask how many to test
    print()
    max_input = input(f"  How many proxies to test? (default 100, max {len(all_proxies)}): ").strip()
    max_test = int(max_input) if max_input.isdigit() else 100
    max_test = min(max_test, len(all_proxies))
    
    # Step 3: Test proxies
    import random
    random.shuffle(all_proxies)  # Randomize which ones we test
    working = test_proxies(all_proxies, max_test)
    
    # Step 4: Results
    print()
    print("=" * 60)
    print(f"  RESULTS")
    print("=" * 60)
    print(f"  Total tested:  {max_test}")
    print(f"  Working:       {len(working)}")
    print(f"  Success rate:  {len(working)/max_test*100:.1f}%")
    
    if working:
        print(f"\n  Top 5 fastest proxies:")
        for i, (proxy_str, speed) in enumerate(working[:5]):
            print(f"    {i+1}. {proxy_str} ({speed:.0f}ms)")
        
        # Save to file
        save_proxies(working)
        print(f"\n  Now run: python unixpunks_hunter_windows.py")
        print(f"  The script will automatically use proxies.txt!")
    else:
        print(f"\n  No working proxies found.")
        print(f"  Try again later or increase the test count.")
    
    print()
    input("  Press Enter to exit...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Stopped by user.")
    except Exception as e:
        print(f"\n  Error: {e}")
        import traceback
        traceback.print_exc()
        input("  Press Enter to exit...")
