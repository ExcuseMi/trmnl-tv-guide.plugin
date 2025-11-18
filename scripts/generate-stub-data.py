import os
import json
from pathlib import Path
import requests
from dotenv import load_dotenv

# Get the script's directory and navigate to project root
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
STUB_DIR = DATA_DIR / "stub" / "channels"

# Create directories if they don't exist
STUB_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
TEST_CHANNEL_IDS = os.getenv("TEST_CHANNEL_IDS", "")

if not API_KEY:
    raise ValueError("API_KEY not found in .env file")

if not TEST_CHANNEL_IDS:
    raise ValueError("TEST_CHANNEL_IDS not found in .env file")


def fetch_channel_programs(channel_id):
    """Fetch programs for a specific channel"""
    print(f"Fetching programs for channel ID: {channel_id}...")
    url = f"https://tv-plan.org/api-v1.php?apitoken={API_KEY}&resource=programsOfChannel&channelId={channel_id}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        programs = response.json()

        # Save to file
        file_path = STUB_DIR / f"{channel_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(programs, f, indent=2, ensure_ascii=False)

        print(f"✓ Saved {len(programs) if isinstance(programs, list) else 'data'} to {file_path}")
        return True
    except requests.RequestException as e:
        print(f"✗ Error fetching channel {channel_id}: {e}")
        return False


def main():
    print("=" * 60)
    print("TV Plan Test Channels Fetcher")
    print("=" * 60)

    # Parse channel IDs from comma-separated list
    channel_ids = [ch_id.strip() for ch_id in TEST_CHANNEL_IDS.split(",") if ch_id.strip()]

    if not channel_ids:
        print("No channel IDs found in TEST_CHANNEL_IDS")
        return

    print(f"\nFound {len(channel_ids)} channel IDs to fetch: {', '.join(channel_ids)}")
    print(f"Saving to: {STUB_DIR.absolute()}\n")

    # Fetch programs for each channel
    success_count = 0
    for i, channel_id in enumerate(channel_ids, 1):
        print(f"\n[{i}/{len(channel_ids)}] ", end="")
        if fetch_channel_programs(channel_id):
            success_count += 1

    # Print summary
    print(f"\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total channels: {len(channel_ids)}")
    print(f"Successfully fetched: {success_count}")
    print(f"Failed: {len(channel_ids) - success_count}")


if __name__ == "__main__":
    main()