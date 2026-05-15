#!/usr/bin/env python3
"""
UnixPunks Hunter - Windows Compatible Version
A script to hunt for mint codes on UnixPunks platform
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
DEFAULT_DELAY_MS = 200
REQUEST_TIMEOUT = 10  # Increased timeout for Windows
MAX_ATTEMPTS = 50000

class UnixPunksHunter:
    def __init__(self):
        self.proxies = []
        self.tried_timestamps = set()
        self.attempt_count = 0
        
    def load_proxies(self) -> None:
        """Load proxies from proxies.txt file"""
        try:
            if os.path.exists(PROXIES_FILE):
                with open(PROXIES_FILE, 'r', encoding='utf-8') as f:
                    raw_proxies = [line.strip() for line in f if line.strip()]
                
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
                print(f"✅ Loaded {len(self.proxies)} proxies from {PROXIES_FILE}")
            else:
                print(f"📝 No {PROXIES_FILE} found — running without proxies")
                
        except Exception as e:
            print(f"❌ Error loading proxies: {e}")
            print("🔄 Continuing without proxies...")
        
        if self.proxies:
            first_proxy = self.proxies[0]['http']
            masked_proxy = first_proxy[:60] + "..." if len(first_proxy) > 60 else first_proxy
            print(f"   First proxy: {masked_proxy}")
        else:
            print("   Running in direct mode (no proxies)")
        print()

    def make_request(self, url: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make HTTP request with proxy rotation and error handling"""
        proxy = random.choice(self.proxies) if self.proxies else None
        proxy_label = proxy['http'][:50].split("@")[-1] if proxy else "DIRECT"
        
        # Prepare request parameters
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
            status_emoji = "✅" if response.status_code == 200 else "❌"
            
            print(f"  [{self.attempt_count:4d}] {proxy_label:30s} → {status_emoji} {response.status_code} ({elapsed_ms:.0f}ms)")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"       HTTP {response.status_code}: {response.text[:100]}")
                
        except requests.exceptions.ProxyError:
            print(f"  [{self.attempt_count:4d}] {proxy_label:30s} → 🚫 PROXY AUTH FAILED")
        except requests.exceptions.Timeout:
            print(f"  [{self.attempt_count:4d}] {proxy_label:30s} → ⏱️  TIMEOUT ({REQUEST_TIMEOUT}s)")
        except requests.exceptions.ConnectionError:
            print(f"  [{self.attempt_count:4d}] {proxy_label:30s} → 🔌 CONNECTION FAILED")
        except Exception as e:
            error_msg = str(e)[:50]
            print(f"  [{self.attempt_count:4d}] {proxy_label:30s} → ❌ {type(e).__name__}: {error_msg}")
            
        return None

    def get_schedule(self) -> Optional[Dict]:
        """Fetch the current minting schedule"""
        print("🔍 Fetching schedule...")
        schedule = self.make_request(f"{API}/schedule")
        
        if not schedule or not schedule.get("activeBatch"):
            print("\n❌ No active batch found or API unreachable.")
            print("💡 Possible solutions:")
            print("   - Check your internet connection")
            print("   - Verify the API is working: https://unixpunks.xyz")
            print("   - Try using proxies (create proxies.txt file)")
            return None
            
        return schedule

    def get_user_input(self) -> tuple[float, str]:
        """Get delay and wallet address from user"""
        print()
        while True:
            try:
                delay_input = input(f"⏱️  Delay between attempts in ms (default {DEFAULT_DELAY_MS}): ").strip()
                delay_ms = float(delay_input) if delay_input else DEFAULT_DELAY_MS
                if delay_ms < 0:
                    print("❌ Delay must be positive")
                    continue
                break
            except ValueError:
                print("❌ Please enter a valid number")
                
        delay_seconds = delay_ms / 1000
        print(f"✅ Using {delay_ms:.0f}ms delay between attempts")
        print()
        
        while True:
            wallet = input("💰 Enter your wallet address (0x...): ").strip()
            
            if (len(wallet) == 42 and 
                wallet.startswith("0x") and 
                all(c in "0123456789abcdefABCDEF" for c in wallet[2:])):
                break
            else:
                print("❌ Invalid wallet address. Must be 42 characters starting with 0x")
                print("   Example: 0x742d35Cc6634C0532925a3b8D400e41b6fB4C7a2")
                
        return delay_seconds, wallet

    def hunt_mint_code(self, start_ts: int, end_ts: int, wallet: str, delay: float) -> None:
        """Main hunting loop"""
        print(f"\n🎯 Starting hunt with {delay*1000:.0f}ms delay")
        print("📊 Live hunting logs:")
        print("=" * 80)
        
        while True:
            # Generate random timestamp that hasn't been tried
            timestamp = random.randint(start_ts, end_ts)
            while timestamp in self.tried_timestamps:
                timestamp = random.randint(start_ts, end_ts)
                
            self.tried_timestamps.add(timestamp)
            self.attempt_count += 1
            
            # Make the mint code request
            result = self.make_request(
                f"{API}/find-mint-code", 
                data={"timestamp": timestamp, "wallet": wallet}
            )
            
            if result is None:
                time.sleep(0.2)  # Brief pause on failed requests
                continue
                
            # Check for success
            if result.get("ok"):
                self.print_success(timestamp, result.get("mintCode", "N/A"))
                break
                
            # Handle rate limiting
            elif result.get("error") in ("rate_limit", "rate_limit_wallet"):
                retry_ms = result.get("retryInMs", 1000)
                print(f"  ⏳ RATE LIMITED — waiting {retry_ms}ms")
                time.sleep(retry_ms / 1000)
                continue
                
            # Check if we've hit the attempt limit
            if self.attempt_count >= MAX_ATTEMPTS:
                print(f"\n🛑 Stopping after {MAX_ATTEMPTS} attempts")
                print("💡 Consider:")
                print("   - Trying again later")
                print("   - Using different proxies")
                print("   - Reducing delay time")
                break
                
            # Normal delay between attempts
            time.sleep(delay)

    def print_success(self, timestamp: int, mint_code: str) -> None:
        """Print success message with mint code"""
        print(f"\n{'=' * 80}")
        print(f"🎉🎉🎉 SUCCESS! Found mint code after {self.attempt_count} attempts! 🎉🎉🎉")
        print(f"⏰ Winning timestamp: {timestamp}")
        print(f"🎫 Mint code: {mint_code}")
        print(f"🌐 Go mint at: https://unixpunks.xyz")
        print(f"{'=' * 80}")

    def run(self) -> None:
        """Main execution flow"""
        print("🚀 UnixPunks Hunter - Windows Edition")
        print("=" * 50)
        
        # Load proxies
        self.load_proxies()
        
        # Get schedule
        schedule = self.get_schedule()
        if not schedule:
            return
            
        # Parse schedule information
        window = schedule["windows"][0]
        start_ts = window["tsRangeStart"]
        end_ts = window["tsRangeEnd"]
        
        print(f"\n📅 Batch {schedule['activeBatch']} is active!")
        print(f"   ⏰ Time range: {start_ts} – {end_ts}")
        print(f"   🏆 Total winners: {window['timestampsCount']}")
        print(f"   ✅ Already claimed: {window['consumedCount']}")
        print(f"   🎯 Remaining: {window['timestampsCount'] - window['consumedCount']}")
        
        # Get user input
        delay, wallet = self.get_user_input()
        
        print(f"\n📋 Hunt Configuration:")
        print(f"   💰 Wallet: {wallet}")
        print(f"   ⏱️  Delay: {delay * 1000:.0f}ms")
        print(f"   🌐 Proxies: {len(self.proxies)} loaded")
        
        input("\n🎯 Press Enter to start hunting...")
        
        # Start hunting
        try:
            self.hunt_mint_code(start_ts, end_ts, wallet, delay)
        except KeyboardInterrupt:
            print(f"\n\n⏹️  Hunt stopped by user after {self.attempt_count} attempts")
            print("👋 Thanks for using UnixPunks Hunter!")


if __name__ == "__main__":
    try:
        hunter = UnixPunksHunter()
        hunter.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        input("Press Enter to exit...")