import json
from pathlib import Path
import yaml

# Get the script's directory and navigate to project root
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
COUNTRIES_FILE = DATA_DIR / "countries.json"
CHANNELS_FILE = DATA_DIR / "channels.json"
OUTPUT_FILE_ROOT = PROJECT_ROOT / "options.yml"
OUTPUT_FILE_DATA = DATA_DIR / "options.yml"


def load_countries():
    """Load countries data from JSON file"""
    if not COUNTRIES_FILE.exists():
        print(f"Error: {COUNTRIES_FILE} not found")
        print("Please run the fetch script first to download countries data")
        return None

    with open(COUNTRIES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get("data", [])


def load_channels():
    """Load channels data from JSON file"""
    if not CHANNELS_FILE.exists():
        print(f"Error: {CHANNELS_FILE} not found")
        print("Please run the fetch script first to download channels data")
        return None

    with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_options_yml():
    print("=" * 60)
    print("TV Plan Options Generator")
    print("=" * 60)

    # Load data
    countries = load_countries()
    channels_data = load_channels()

    if not countries or not channels_data:
        print("\nFailed to load required data. Exiting.")
        return

    print(f"\nLoaded {len(countries)} countries")
    print(f"Loaded channel data for {len(channels_data)} countries")

    # Create a mapping of country_id to country info
    country_map = {country["id"]: country for country in countries}

    # Build channel options
    channel_options = []
    total_channels = 0

    for country_id, country_channels in channels_data.items():
        if country_id not in country_map:
            print(f"Warning: Country ID {country_id} not found in countries data")
            continue

        country = country_map[country_id]
        country_display_name = country.get("display_name", country.get("name", "Unknown"))

        channels = country_channels.get("data", [])

        for channel in channels:
            channel_id = channel.get("id")
            channel_display_name = channel.get("display_name", channel.get("name", "Unknown"))

            if channel_id:
                # Format: "Country - Channel Name": channel_id
                option_key = f"{country_display_name} - {channel_display_name}"
                value = f"{channel_id}|{channel_display_name}"
                channel_options.append({option_key: value})
                total_channels += 1

    # Sort options alphabetically by key (case insensitive)
    channel_options.sort(key=lambda x: list(x.keys())[0].lower())

    print(f"\nGenerated {total_channels} channel options")
    # Create the custom fields
    custom_fields = []
    about_field = {
        'keyname': 'about',
        'name': 'About This Plugin',
        'field_type': 'author_bio',
        'description': f"Display TV program schedules from {len(channels_data)} countries with {total_channels} channels available.<br /><br />\n"
                       f"<strong>Features:</strong><br />\n"
                       f"● Live TV schedule with current and upcoming programs<br />\n"
                       f"● Support for channels from multiple countries<br />\n"
                       f"● Highlights currently airing programs<br />\n"
                       f"<strong>Setup Requirements:</strong><br />\n"
                       f"● Free API key from <a href='https://tv-plan.org/#/apiarea'>TV-Plan.org</a> (takes less than a minute)<br />\n"
                       f"● Each channel uses one API call per refresh<br />\n"
                       f"● Recommended: 5 channels with hourly refresh or evening-only schedule<br />\n"
        ,
        'github_url': 'https://github.com/ExcuseMi/trmnl-tv-guide.plugin',
        'learn_more_url': 'https://tv-plan.org/#/apiarea'
    }
    custom_fields.append(about_field)

    # API Key field
    api_key_field = {
        'keyname': 'api_token',
        'field_type': 'string',
        'name': 'TV-Plan API Token',
        'description': 'Enter your API token from <a href="https://tv-plan.org/api-v1.php#/apiarea">TV-Plan.org</a>. An API token is required to fetch TV program data.',
        'placeholder': 'Enter your TV-Plan API token',
    }
    custom_fields.append(api_key_field)

    # Channels field
    channels_field = {
        'keyname': 'channels',
        'field_type': 'select',
        'name': f'TV Channels: {len(channel_options)}',
        'description': 'Select the TV channels you want to track. Channels are organized by country and sorted alphabetically.',
        'multiple': True,
        'help_text': 'Use <kbd>⌘</kbd>+<kbd>click</kbd> (Mac) or <kbd>ctrl</kbd>+<kbd>click</kbd> (Windows) to select multiple items. Use <kbd>Shift</kbd>+<kbd>click</kbd> to select a whole range at once.',
        'options': channel_options
    }
    custom_fields.append(channels_field)
    # Time format field
    time_format_field = {
        'keyname': 'time_format',
        'field_type': 'select',
        'name': 'Time Format',
        'description': 'Choose how times are displayed on your TV guide.',
        'options': [
            {'24-hour (23:00)': '24'},
            {'12-hour (11:00 PM)': '12'}
        ],
        'default': '24',
        'optional': True
    }
    custom_fields.append(time_format_field)

    show_title_bar_field = {
        'keyname': 'show_title_bar',
        'field_type': 'select',
        'name': 'Show Title Bar',
        'description': 'Display or hide the "TV Guide" title bar at the bottom of the screen.',
        'options': [
            {'Show': 'true'},
            {'Hide': 'false'}
        ],
        'default': 'true',
        'optional': True
    }
    custom_fields.append(show_title_bar_field)

    # Use custom YAML representer to format the output properly
    def represent_dict_order(dumper, data):
        return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

    yaml.add_representer(dict, represent_dict_order)


    print(f"\nWriting to: {OUTPUT_FILE_DATA.absolute()}")

    with open(OUTPUT_FILE_DATA, 'w', encoding='utf-8') as f:
        yaml.dump(custom_fields, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=1000)

    print(f"✓ Successfully created {OUTPUT_FILE_DATA}")

    # Print summary
    print(f"\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total countries: {len(countries)}")
    print(f"Countries with channels: {len(channels_data)}")
    print(f"Total channels: {total_channels}")

    # Show sample of channels
    print(f"\nSample channels (first 5):")
    for i, option in enumerate(channel_options[:5]):
        key = list(option.keys())[0]
        value = list(option.values())[0]
        print(f"  {i + 1}. {key} (ID: {value})")


if __name__ == "__main__":
    create_options_yml()