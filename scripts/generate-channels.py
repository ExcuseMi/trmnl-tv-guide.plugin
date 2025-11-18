import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import requests
from dotenv import load_dotenv

# Configuration
COUNTRIES_MAX_AGE_DAYS = 7

# Get the script's directory and navigate to project root
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
COUNTRIES_FILE = DATA_DIR / "countries.json"
CHANNELS_FILE = DATA_DIR / "channels.json"

# Create directory if it doesn't exist
DATA_DIR.mkdir(exist_ok=True)

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise ValueError("API_KEY not found in .env file")


def get_utc_timestamp():
    """Return current UTC timestamp in ISO format"""
    return datetime.utcnow().isoformat() + "Z"


def is_data_stale(timestamp_str, max_age_days):
    """Check if data is older than max_age_days"""
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", ""))
        age = datetime.utcnow() - timestamp
        return age > timedelta(days=max_age_days)
    except (ValueError, AttributeError):
        return True


def fetch_countries():
    """Fetch countries from API and save to file"""
    print("Fetching countries...")
    url = f"https://tv-plan.org/api-v1.php?apitoken={API_KEY}&resource=countries"

    try:
        response = requests.get(url)
        response.raise_for_status()
        countries = response.json()

        data = {
            "data": countries,
            "timestamp": get_utc_timestamp()
        }

        with open(COUNTRIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(countries)} countries")
        return countries
    except requests.RequestException as e:
        print(f"Error fetching countries: {e}")
        return None


def load_countries():
    """Load countries from file or fetch if stale/missing"""
    if COUNTRIES_FILE.exists():
        with open(COUNTRIES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not is_data_stale(data.get("timestamp", ""), COUNTRIES_MAX_AGE_DAYS):
            print(f"Using cached countries (age: {data.get('timestamp')})")
            return data["data"]
        else:
            print("Countries data is stale, refreshing...")

    return fetch_countries()


def load_channels_data():
    """Load all existing channel data with timestamps"""
    if CHANNELS_FILE.exists():
        with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def fetch_channels_for_country(country_id, country_name, all_channels_data):
    """Fetch channels for a specific country and update the channels.json file"""
    print(f"Fetching channels for {country_name} (ID: {country_id})...")
    url = f"https://tv-plan.org/api-v1.php?apitoken={API_KEY}&resource=channelsOfCountry&countryId={country_id}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        channels = response.json()

        # Update the data for this country
        all_channels_data[country_id] = {
            "data": channels,
            "timestamp": get_utc_timestamp()
        }

        # Save the entire channels.json file
        with open(CHANNELS_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_channels_data, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(channels)} channels for {country_name}")
        return True
    except requests.RequestException as e:
        print(f"Error fetching channels for {country_name}: {e}")
        if "429" in str(e) or "rate limit" in str(e).lower():
            print("Rate limit reached. Run the script again later to continue.")
            return False
        return None


def main():
    print("=" * 50)
    print("TV Plan Data Fetcher")
    print("=" * 50)

    # Load or fetch countries
    countries = load_countries()
    if not countries:
        print("Failed to load countries. Exiting.")
        return

    # Load existing channels data
    channels_data = load_channels_data()
    print(f"Found existing data for {len(channels_data)} countries")

    # Categorize countries
    countries_to_fetch = []

    for country in countries:
        country_id = country["id"]
        country_name = country["name"]

        if country_id not in channels_data:
            # No data yet - high priority
            countries_to_fetch.append((country_id, country_name, None))
        else:
            # Has data - check age
            timestamp = channels_data[country_id].get("timestamp", "")
            countries_to_fetch.append((country_id, country_name, timestamp))

    # Sort: None timestamps first (missing data), then by oldest timestamp
    countries_to_fetch.sort(key=lambda x: (x[2] is not None, x[2] or ""))

    # Fetch channels for each country
    for country_id, country_name, timestamp in countries_to_fetch:
        if timestamp is None:
            print(f"\n[NEW] Processing {country_name}...")
        else:
            print(f"\n[UPDATE] Processing {country_name} (last updated: {timestamp})...")

        result = fetch_channels_for_country(country_id, country_name, channels_data)

        if result is False:
            # Rate limit reached
            break

        # Small delay to avoid overwhelming the API
        time.sleep(0.5)

    print("\n" + "=" * 50)
    print("Fetch complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()