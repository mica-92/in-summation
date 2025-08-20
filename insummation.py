from collections import Counter, defaultdict
from datetime import datetime
from mapps import album_colors, taylor_version_mapping, album_mapping, file_names, TAYLOR_QUOTES
import json


import random

def get_random_taylor_quote():
    """
    Returns a random quote from the TAYLOR_QUOTES dictionary
    """
    if not TAYLOR_QUOTES or not TAYLOR_QUOTES.get("quotes"):
        return None
    
    quotes = TAYLOR_QUOTES["quotes"]
    if not quotes:
        return None
        
    return random.choice(quotes)

random_quote = get_random_taylor_quote()

# Add this dictionary at the top of your generate_html_report function

def format_anniversaries(text):
    if text == "No major releases this year":
        return text
    import re
    return re.sub(r'([A-Za-z]+ \d{1,2}(?:, \d{4})?)', r'<strong>\1</strong>', text)

album_info = {
    "Taylor Swift": {
        "image": "TS1.png",
        "release_date": "24.10.2006",
        "taylor_version": "<i>unreleased</i>",
        "era_period": "Oct 2006 - Nov 2008",
        "fun_fact": "debut."
    },
    "Fearless": {
        "image": "TS2.png",
        "release_date": "11.11.2008",
        "taylor_version": "09.04.2021",
        "era_period": "Nov 2008 - Oct 2010 & Apr 2021 - Nov 2021",
        "fun_fact": "next chapter."
    },
    "Speak Now": {
        "image": "TS3.png",
        "release_date": "25.10.2010",
        "taylor_version": "07.07.2023",
        "era_period": "Oct 2010 - Oct 2012 & Jul 2023 - Oct 2023",
        "fun_fact": "I had the time of my life fighting dragons with you."
    },    
    "Red": {
        "image": "TS7.png",
        "release_date": "22.10.2012",
        "taylor_version": "12.11.2021",
        "era_period": "Oct 2012 - Oct 2014 & Apr 2021 - Oct 2022",
        "fun_fact": "loving him was red."
    },
    "1989": {
        "image": "TS4.png",
        "release_date": "27.10.2014",
        "taylor_version": "27.10.2023",
        "era_period": "Oct 2014 -  Nov 2017 & Oct 2023 - Apr 2024",
        "fun_fact": "fell down a rabbit hole."
    },
    "reputation": {
        "image": "TS8.png",
        "release_date": "10.11.2017",
        "taylor_version": "<i>unreleased</i>",
        "era_period": "Oct 2017 - Aug 2019",
        "fun_fact": "and in the death of her reputation she felt truly alive."
    },

    "Lover": {
        "image": "TS5.png",
        "release_date": "23.08.2019",
        "taylor_version": "<i>always was</i>",
        "era_period": "Aug 2019 - Jul 2020",
        "fun_fact": "I wanna be defined by the things that I love."

    },
    "folklore": {
        "image": "TS9.png",
        "release_date": "24.07.2020",
        "taylor_version": "<i>always was</i>",
        "era_period": "Jul 2020 - Dec 2020",
        "fun_fact": "not a lot going on at the moment."
    },
    "evermore": {
        "image": "TS10.png",
        "release_date": "11.12.2020",
        "taylor_version": "<i>always was</i>",
        "era_period": "Dec 2020 - Apr 2021",
        "fun_fact": "folklore's sister album."
    },
    "Midnights": {
        "image": "TS11.png",
        "release_date": "21.10.2022",
        "taylor_version": "<i>always was</i>",
        "era_period": "Oct 2022 -  Jul 2023",
        "fun_fact": "<i>the stories of 13 sleepless nights.</i>"
    },
    "THE TORTURED POETS DEPARTMENT": {
        "image": "TS6.png",
        "release_date": "19.04.2024",
        "taylor_version": "<i>always was</i>",
        "era_period": "Apr 2024 -  Oct 2025",
        "fun_fact": "<i>all's fair in love & poetry.</i>"
    },
    "The Life of a Showgirl": {
        "image": "TS12.png",
        "release_date": "October 21, 2022",
        "era_period": "Oct 2015 - ",
        "fun_fact": ""
    },

    "Other": {
        "image": "TSO.png",
        "release_date": "multiple",
        "taylor_version": "multiple",
        "era_period": "multiples",
        "fun_fact": "soundtracks, features & other shenanigans."
    } 
}

def merge_taylor_versions(song_counter, version_mapping):
    """
    Merge counts of Taylor's Version and non-Taylor's Version songs.
    """
    merged_counter = Counter()
    for song, count in song_counter.items():
        unified_song = version_mapping.get(song, song)
        merged_counter[unified_song] += count
    return merged_counter

def get_time_capsule_songs(results, taylor_version_mapping):
    """Get the most listened song for each year on today's date (August 15th)"""
    today = datetime.now()
    current_month_day = f"{today.month:02d}-{today.day:02d}"
    
    yearly_songs = defaultdict(Counter)
    
    for entry in results['all_data']:
        if not entry.get('ts'):
            continue
            
        dt = datetime.strptime(entry['ts'], "%Y-%m-%dT%H:%M:%SZ")
        entry_month_day = f"{dt.month:02d}-{dt.day:02d}"
        
        if entry_month_day == current_month_day:
            year = dt.year
            artist = entry.get('master_metadata_album_artist_name')
            song = entry.get('master_metadata_track_name')
            
            if artist == "Taylor Swift" and song:
                unified_song = taylor_version_mapping.get(song, song)
                yearly_songs[year][unified_song] += 1
    
    # Get top song for each year
    time_capsule = {}
    for year, songs in yearly_songs.items():
        if songs:
            top_song = songs.most_common(1)[0]
            time_capsule[year] = top_song[0]
    
    return time_capsule


def analyze_taylor_swift_data(file_names, album_mapping=None, taylor_version_mapping=None):
    """
    Analyze Taylor Swift listening data and calculate stats for both yearly and album views.
    """
    all_data = []
    total_minutes_spotify = defaultdict(int)
    taylor_minutes_by_year = defaultdict(int)
    album_minutes_by_year = defaultdict(lambda: defaultdict(int))
    album_song_counter = defaultdict(Counter)
    total_song_counter = Counter()
    monthly_stats = defaultdict(lambda: {
        'minutes': 0,
        'albums': Counter(),  # Changed from defaultdict to Counter
        'songs': Counter()
    })
    prev_month_stats = {}

    # Load data from all files
    for file_name in file_names:
        with open(file_name, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            normalized_data = [
                {k: (v.replace("\u2019", "'") if isinstance(v, str) else v) for k, v in entry.items()}
                for entry in raw_data
            ]
            all_data.extend(normalized_data)

    # Filter and process data
    for entry in all_data:
        ts = entry.get('ts', None)
        if ts:
            # Skip tracks from the reputation tour playlist
            album_name = entry.get('master_metadata_album_album_name', '')
            if album_name == "reputation Stadium Tour Surprise Song Playlist":
                continue  # Skip this entry entirely


            
            ms_played = entry.get('ms_played', 0)
            dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
            year_month = f"{dt.year}-{dt.month:02d}"

            # Skip tracks played for less than 30 seconds
            if ms_played < 30000:
                continue
                
            year = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").year
            total_minutes_spotify[year] += ms_played

            song_name = entry.get('master_metadata_track_name', None)
            album_name = entry.get('master_metadata_album_album_name', None)
            artist_name = entry.get('master_metadata_album_artist_name', None)

            if artist_name == "Taylor Swift" and song_name and album_name:
                # Map song and album names
                if taylor_version_mapping:
                    song_name = taylor_version_mapping.get(song_name, song_name)
                if album_mapping:
                    album_name = album_mapping.get(album_name, album_name)

                # Track minutes for both yearly and album views
                taylor_minutes_by_year[year] += ms_played
                album_minutes_by_year[year][album_name] += ms_played
                
                # Count song plays per album and overall
                album_song_counter[album_name][song_name] += 1
                total_song_counter[song_name] += 1

                # Update monthly stats
                monthly_stats[year_month]['minutes'] += ms_played
                monthly_stats[year_month]['albums'][album_name] += 1  # Counting plays instead of ms
                monthly_stats[year_month]['songs'][song_name] += 1

    # Convert milliseconds to minutes
    convert_ms_to_minutes = lambda ms: ms / 60000
    total_minutes_spotify = {year: convert_ms_to_minutes(ms) for year, ms in total_minutes_spotify.items()}
    taylor_minutes_by_year = {year: convert_ms_to_minutes(ms) for year, ms in taylor_minutes_by_year.items()}
    album_minutes_by_year = {
        year: {album: convert_ms_to_minutes(ms) for album, ms in albums.items()}
        for year, albums in album_minutes_by_year.items()
    }

    # Calculate total minutes per album
    total_album_minutes = defaultdict(float)
    for year, albums in album_minutes_by_year.items():
        for album, minutes in albums.items():
            total_album_minutes[album] += minutes


    # Convert ms to minutes and prepare comparison data
    sorted_months = sorted(monthly_stats.keys())
    for i, month in enumerate(sorted_months):
        # Convert to minutes
        monthly_stats[month]['minutes'] = round(monthly_stats[month]['minutes'] / 60000, 1)
        
        # Prepare comparison data
        if i > 0:
            prev_month = sorted_months[i-1]
            prev_month_stats[month] = {
                'albums': monthly_stats[prev_month]['albums'].copy(),
                'songs': monthly_stats[prev_month]['songs'].copy()
            }


    # All-time stats
    all_time_spotify_minutes = sum(total_minutes_spotify.values())
    all_time_taylor_minutes = sum(taylor_minutes_by_year.values())
    all_time_percentage_taylor = (all_time_taylor_minutes / all_time_spotify_minutes) * 100 if all_time_spotify_minutes else 0

    # Include song counters in all-time stats
    all_time_stats = {
        'total_spotify_minutes': all_time_spotify_minutes,
        'total_taylor_minutes': all_time_taylor_minutes,
        'percentage_taylor': all_time_percentage_taylor,
        'songs': total_song_counter,
        'album_songs': album_song_counter
    }

    return {
        'total_minutes_spotify': total_minutes_spotify,
        'taylor_minutes_by_year': taylor_minutes_by_year,
        'album_minutes_by_year': album_minutes_by_year,
        'total_album_minutes': total_album_minutes,
        'monthly_stats': monthly_stats,
        'prev_month_stats': prev_month_stats,
        'sorted_months': sorted_months,
        'all_time_stats': all_time_stats,
        'all_data': all_data
    }

def get_top_songs_for_year(results, year, taylor_version_mapping):
    """Get top songs for a specific year"""
    yearly_songs = Counter()
    for entry in results['all_data']:
        ts = entry.get('ts')
        if ts and datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").year == year:
            artist = entry.get('master_metadata_album_artist_name')
            song = entry.get('master_metadata_track_name')
            if artist == "Taylor Swift" and song:
                unified_song = taylor_version_mapping.get(song, song)
                yearly_songs[unified_song] += 1
    return yearly_songs.most_common(31)

def get_top_songs_for_album(results, album_name, taylor_version_mapping):
    """Get top songs for a specific album"""
    album_songs = results['all_time_stats']['album_songs'].get(album_name, Counter())
    merged_songs = merge_taylor_versions(album_songs, taylor_version_mapping)
    return merged_songs.most_common()

def generate_html_report(results, album_colors, taylor_version_mapping):
    """
    Generate an HTML report with toggleable yearly and album views.
    """
    release_anniversaries = {
        2024: "19.04 <i>THE TORTURED POETS DEPARTMENT</i>",
        2023: "07.07 <i>Speak Now (Taylor's Version)</i><br>27.10 <i>1989 (Taylor's Version)</i>",
        2022: "21.10 <i>Midnights</i>",
        2021: "09.04 <i>Fearless (Taylor's Version)</i><br>12.11 <i>Red (Taylor's Version)</i>",
        2020: "24.07 <i>folklore</i><br>11.12 <i>evermore</i>",
        2019: "23.08 <i>Lover</i>",
        2017: "10.11 <i>reputation</i>",
        2014: "27.10 <i>1989</i>",
        2012: "22.10 <i>Red</i>",
        2010: "25.10 <i>Speak Now</i>",
        2008: "11.11 <i>Fearless</i>",
        2006: "24.10 <i>Taylor Swift</i>"
    }
    
    
    
    
    # Calculate all-time album totals
    total_taylor_minutes = results['all_time_stats']['total_taylor_minutes']
    merged_songs = merge_taylor_versions(results['all_time_stats']['songs'], taylor_version_mapping)
    top_songs = merged_songs.most_common(89)
    
    # Get last played date
    last_song_date = max(
        datetime.strptime(entry['ts'], "%Y-%m-%dT%H:%M:%SZ") 
        for entry in results['all_data'] 
        if entry.get('ts') and entry.get('master_metadata_album_artist_name') == "Taylor Swift"
    )

    # Sort albums by total minutes (descending)
    sorted_albums = sorted(
        results['total_album_minutes'].items(), 
        key=lambda x: x[1], 
        reverse=True
    )

    monthly_stats = results['monthly_stats']
    prev_month_stats = results['prev_month_stats']
    sorted_months = results['sorted_months']
    
    # Extract years from sorted months
    years = sorted({month.split('-')[0] for month in sorted_months}, reverse=True)
    
    # Get last played date
    last_song_date = max(
        datetime.strptime(entry['ts'], "%Y-%m-%dT%H:%M:%SZ") 
        for entry in results['all_data'] 
        if entry.get('ts') and entry.get('master_metadata_album_artist_name') == "Taylor Swift"
    )

    def get_position_trend(current_month, item, type, monthly_stats, prev_month_stats):
        if current_month not in prev_month_stats:
            return ""
            
        # Get current rankings
        current_items = monthly_stats[current_month][type].most_common()
        current_ranking = {item: idx for idx, (item, count) in enumerate(current_items)}
        
        # Get previous rankings (just from immediate previous month)
        prev_items = prev_month_stats[current_month][type].most_common()
        prev_ranking = {item: idx for idx, (item, count) in enumerate(prev_items)}
        
        # Check if item has ever appeared in any previous month
        has_ever_appeared = False
        for month in sorted_months:
            if month >= current_month:  # Only check months before current month
                continue
            if item in monthly_stats[month][type]:
                has_ever_appeared = True
                break
        
        # Compare positions
        if not has_ever_appeared:
            return '<span class="trend-indicator new">NEW</span>'
        
        current_pos = current_ranking.get(item, 999)
        prev_pos = prev_ranking.get(item, 999)
        pos_diff = abs(current_pos - prev_pos)

        
        if current_pos < prev_pos:  # Moved up
            if pos_diff > 5:
                return f'<span class="trend-indicator up"><i class="fa-solid fa-caret-up"></i><i class="fa-solid fa-caret-up"></i></span>'
            else:
                return f'<span class="trend-indicator up"><i class="fa-solid fa-caret-up"></i></span>'
        elif current_pos > prev_pos:  # Moved down
            if pos_diff > 5:
                return f'<span class="trend-indicator down"><i class="fa-solid fa-caret-down"></i><i class="fa-solid fa-caret-down"></i></span>'
            else:
                return f'<span class="trend-indicator down"><i class="fa-solid fa-caret-down"></i></span>'
        return '<span class="trend-indicator same"><i class="fa-solid fa-equals"></i></span>'

    # Define the custom album order
    custom_album_order = [
        "The Life of a Showgirl",
        "THE TORTURED POETS DEPARTMENT",
        "Midnights",
        "evermore",
        "folklore",
        "Lover",
        "reputation",
        "1989",
        "Red",
        "Speak Now",
        "Fearless",
        "Taylor Swift"
    ]

    # Sort albums according to custom order
    sorted_albums = sorted(
        results['total_album_minutes'].items(),
        key=lambda x: custom_album_order.index(x[0]) if x[0] in custom_album_order else float('inf')
    )
    time_capsule_songs = get_time_capsule_songs(results, taylor_version_mapping)


    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>In Summation</title>
    <link rel="icon" href="fav.ico" type="image/x-icon">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        :root {{
            --primary: #000000;
            --secondary: #ffd1a3;
            --accent: #7FB069;
            --highlight: #ADEBB3;
            --border: 3px solid var(--primary);
            --shadow: 8px 8px 0px var(--primary);
            --font-main: 'DM Sans', monospace;
            --font-size: 18px;
        }}

        /* Add this to your existing CSS */
        button, .nav-tab  {{
            cursor: pointer; /* Shows hand cursor on hover */
        }}

        /* Prevent text selection on interactive elements */
        button, .nav-tab, .song-item, .album-row, .total-minutes-text, .total-minutes-value {{
            user-select: none;
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
        }}
        
        body {{
            font-family: var(--font-main);
            background: 
                linear-gradient(rgba(255, 209, 163, 0.65), rgba(255, 209, 163, 0.2)),
                url('back.jpg') no-repeat center center;            
            color: var(--primary);
            background-size: cover;
            background-attachment: fixed;
            font-size: var(--font-size);
            line-height: 1.6;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}

        header {{
            border: var(--border);
            padding: 20px;
            margin-bottom: 15px;
            background-color: var(--highlight);
            border-radius: 5px;
        }}
        
        h1, h2, h3 {{
            margin-top: 0;
            font-weight: 700;
        }}
        
        h1 {{
            font-size: 2.5rem;
            text-transform: uppercase;
            margin-bottom: 0;
        }}
        
        h2 {{
            font-size: 1.8rem;
            border-bottom: var(--border);
            padding-bottom: 10px;
            margin-top: 40px;
        }}

        h3 {{
            font-size: 1.5rem;
            margin-top: 30px;
        }}

        .card {{
            border: var(--border);
            border-radius: 5px;
            padding: 20px;
            margin-bottom: 15px;
            background-color: #FFFFFF;
        }}
        
        /* Top Songs Styling */
        .song-list {{
            list-style-type: none;
            padding: 0;
        }}
        
        .song-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            border-bottom: 2px solid #f0f0f0;
        }}
        
        .song-item-top {{
            width: 40px;
            height: 40px;
            font-size: 1.5rem;
        }}
        
        .song-info {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .song-number {{
            width: 25px;
            height: 25px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            border: var(--border);
            border-radius: 2px;
            margin-right: 10px;
            color: var(--secondary)
        }}
        
        .song-number-top {{
            font-size: 1.5rem;
            width: 40px;
            height: 40px;
        }}
        
        .song-title {{
            font-weight: 500;
            flex-grow: 1;
        }}
        
        .song-title-top {{
            font-size: 1.2rem;
            font-weight: 700;
        }}
        
        .play-count {{
            font-weight: bold;
            margin-right: 15px;
        }}
        
        .play-count-top {{
            font-size: 1.2rem;
        }}
        
        .album-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            border-bottom: 2px solid #f0f0f0;
        }}
        
        .album-row:last-child {{
            border-bottom: none;
        }}
        
        .album-info {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .album-color {{
            width: 20px;
            height: 20px;
            border: var(--border);
            border-radius: 2px;
        }}
        
        .album-percentage {{
            font-weight: bold;
        }}
            
/* Stacked bar container */
.stacked-bar {{
    height: 40px;
    background-color: #D8F3DC;
    border: var(--border);
    margin-bottom: 30px;
    position: relative;
    display: flex;
    box-sizing: border-box;
}}

/* Base segment style */
.stacked-segment {{
    height: 100%;
    position: relative;
    border-right: 2px solid var(--primary);
    z-index: 1;
    margin-right: -1px;
    transform-origin: center;
    box-sizing: border-box;
    transition: all 0.2s ease;
}}

/* Highlighted segment - show tooltip */
.stacked-segment.highlighted {{
    opacity: 1 !important;
    transform: scaleY(1.1);
    z-index: 2;
    border: 2px solid var(--primary) !important;
    margin: -1px -1px -1px -1px;
}}

/* Shaded segment - hide tooltip */
.stacked-segment.shaded {{
    opacity: 0.2 !important;
    filter: grayscale(90%);
    border-right: none !important;
    pointer-events: none; /* This prevents hover on shaded segments */
}}

/* Only show tooltip on highlighted segments */
.stacked-segment.highlighted:hover .stacked-segment-tooltip {{
    opacity: 1;
    visibility: visible;
}}

/* Hide tooltip on shaded segments */
.stacked-segment.shaded .stacked-segment-tooltip {{
    display: none;
}}

/* Tooltip styles */
.stacked-segment-tooltip {{
    position: absolute;
    bottom: calc(100% + 5px);
    left: 50%;
    transform: translateX(-50%);
    background-color: #D8F3DC;
    color: black;
    padding: 5px 10px;
    border-radius: 2px 2px 0 0;
    box-shadow: 2px 2px 0px var(--primary);
    border: var(--border);
    font-size: 16px;
    white-space: nowrap;
    opacity: 0;
    visibility: hidden;
    transition: all 0.2s ease;
    z-index: 100;
}}

.stacked-segment-tooltip::after {{
    content: "";
    position: absolute;
    top: 100%;
    left: 50%;
    margin-left: -5px;
    border-width: 5px;
    border-style: solid;
    border-color: #D8F3DC transparent transparent transparent;
}}

/* All-albums view - show all tooltips */
#all-albums-album-view .stacked-segment:hover .stacked-segment-tooltip {{
    opacity: 1;
    visibility: visible;
}}
        /* Navigation tabs */
        .nav-tabs {{
                display: flex;
            gap: 10px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            overflow-x: auto;
            white-space: nowrap;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
            flex-wrap: wrap;
            row-gap: 8px;
        }}

        .nav-tabs::-webkit-scrollbar {{
            display: none;
        }}
        
        .nav-tab {{
            padding: 8px 15px;
            background: none;
            border: 2px solid var(--primary);
            
            border-radius: 2px 2px 0 0;
            font-family: var(--font-main);
            font-size: clamp(0.8rem, 3vw, 1rem);
            margin-right: 0;
            flex-shrink: 0;
            min-width: max-content;
            box-shadow: 2px 2px 0px var(--primary);
            transition: all 0.2s ease;
            position: relative;
            top: 0;
        }}
        
        .nav-tab:hover {{
                background-color: #D8F3DC;
    box-shadow: none;
    top: 4px;
        }}
        
        .nav-tab.active {{
    background-color: var(--highlight);
    font-weight: bold;
    box-shadow: none;
    top: 4px;
        }}
        
        .stats-view {{
            display: none;
        }}
        
        .stats-view.active {{
            display: block;
        }}
        
        .minutes-header {{
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 15px;
            padding: 10px;
            background-color: #FFF5E6;
            border: var(--border);
            display: inline-block;
        }}
        
        footer {{
            text-align: center;
            margin-top: 50px;
            padding: 20px;
            border: var(--border);
            background-color: var(--secondary);
        }}
        
        .total-minutes-row {{
            background-color: var(--secondary);
            padding: 15px;
            margin: 15px 0;
            border: var(--border);
            box-shadow: var(--shadow);
        }}

        .total-minutes-text {{
            font-weight: bold;
            font-size: 1.1rem;
            flex-grow: 1;
        }}

        .total-minutes-value {{
            font-weight: bold;
            font-size: 1.1rem;
            color: var(--accent);
            margin-right: 15px;
        }}

        .card-highlight {{
            font-weight: bold;
            font-size: 1.1rem;
            color: var(--accent);
            border: var(--border);
            border-radius: 5px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 8px 0px 0px var(--primary);
            background-color: var(--accent);        
        }}

        .big-number {{
            font-size: 2rem;
            font-weight: 900;
            color: var(--secondary);
            line-height: 1;
            margin-bottom: 10px;
        }}
        
        .unit {{
            font-size: 1.1rem;
            font-weight: 00;
            margin-left: 5px;
            color: var(--primary);
        }}

        @media (max-width: 768px) {{
            .nav-tabs {{
                gap: 8px;
                padding-bottom: 8px;
                flex-wrap: wrap;
            }}
    
            .nav-tab {{
                padding: 6px 12px;
                margin-bottom: 8px;
            }}
        }}


        .calendar-list {{
    list-style-type: none;
    padding: 0;
}}

.calendar-list h2 {{
    border-bottom: var(--border);
    padding-bottom: 5px;
    margin-top: 30px;
}}

.calendar-item {{
    display: flex;
    align-items: center;
    padding: 12px 15px;
    border-bottom: 2px solid #f0f0f0;
    gap: 20px;
}}

.calendar-date {{
    font-weight: bold;
    min-width: 100px;
    text-align: center;
    
}}

.calendar-event {{
    flex-grow: 1;
}}


        .legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 20px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            margin-right: 15px;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border: var(--border);
            margin-right: 5px;
        }}

        
        .month-section {{
            margin-bottom: 40px;
            background-color: white;
   
        }}
        
        .month-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
        }}
        
        .total-minutes {{
            font-size: 1.2rem;
            font-weight: bold;
            color: var(--accent);
        }}
        
        .album-list, .song-list {{
            list-style-type: none;
            padding: 0;
        }}
        
        .album-item, .song-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            border-bottom: 2px solid #f0f0f0;
        }}
        
        .album-info, .song-info {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .album-color {{
            width: 20px;
            height: 20px;
            border: var(--border);
            border-radius: 2px;
        }}
        
        .trend-indicator {{
            font-weight: bold;
            margin-left: 10px;
            font-weight: 900;
        }}
        
        .up {{
            color: green;
        }}
        
        .down {{
            color: red;
        }}
        
        .same {{
            color: #666;
        }}
        
        .new {{
            color: var(--accent);
        }}
        
        /* Navigation tabs */
        .nav-tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            overflow-x: auto;
            white-space: nowrap;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
            flex-wrap: wrap;
            row-gap: 8px;
        }}

        .nav-tabs::-webkit-scrollbar {{
            display: none;
        }}
        
        .nav-tab {{
            padding: 8px 15px;
            background: none;
            border: 2px solid var(--primary);
            border-radius: 2px 2px 0 0;
            font-family: var(--font-main);
            font-size: clamp(0.8rem, 3vw, 1rem);
            margin-right: 0;
            flex-shrink: 0;
            min-width: max-content;
            box-shadow: 2px 2px 0px var(--primary);
            transition: all 0.2s ease;
            position: relative;
            top: 0;
        }}
        
        .nav-tab:hover {{
            background-color: #D8F3DC;
            box-shadow: none;
            top: 4px;
        }}
        
        .nav-tab.active {{
            background-color: var(--highlight);
            font-weight: bold;
            box-shadow: none;
            top: 4px;
        }}
        
        .month-nav {{
            display: none;
        }}
        
        .month-nav.active {{
            display: flex;
        }}
        
        .stats-view {{
            display: none;
        }}
        
        .stats-view.active {{
            display: block;
        }}
        
        footer {{
            text-align: center;
            margin-top: 50px;
            padding: 20px;
            border: var(--border);
            background-color: var(--secondary);
        }}

        @media (max-width: 768px) {{
            .nav-tabs {{
                gap: 8px;
                padding-bottom: 8px;
                flex-wrap: wrap;
            }}
    
            .nav-tab {{
                padding: 6px 12px;
                margin-bottom: 8px;
            }}

            .total-minutes-text, .total-minutes-value {{
                font-size: 0.9rem;
            }}

            body {{
                font-size: 0.9rem;
            }}
        }}

    .fa-heart, .fa-music{{
        margin: 0 5px; /* Spacing */
    }}
/* Album Info Box - Neobrutalism Style */
.album-info-box {{
    display: flex;
    border: var(--border);
    margin-bottom: 20px;
    box-shadow: var(--shadow);
    background-color: white;
    padding: 0;
    overflow: hidden;
}}

.album-cover {{
    width: 250px;
    height: 250px;
    border-right: var(--border);
    overflow: hidden;
    flex-shrink: 0;
}}

.album-cover img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}}

.album-details {{
    padding: 15px;
    flex-grow: 1;
}}

.album-details h3 {{
    margin-top: 0;
    font-size: 1.5rem;
    border-bottom: var(--border);
    padding-bottom: 5px;
}}

.album-meta p {{
    margin: 8px 0;
    line-height: 1.4;
}}

/* Responsive adjustments */
@media (max-width: 600px) {{
    .album-info-box {{
        flex-direction: column;
    }}
    
    .album-cover {{
        width: 100%;
        height: auto;
        aspect-ratio: 1/1;
        border-right: none;
        border-bottom: var(--border);
    }}
    
    .album-cover img {{
        width: 100%;
        height: auto;
    }}
}}


/* Add this to your CSS to ensure tooltips work in all views */
#years-view .stacked-segment:hover .stacked-segment-tooltip {{
    opacity: 1;
    visibility: visible;
}}

    </style>
</head>
<body>
    <header>
        <h1>In Summation</h1>
                <p><i>A brutalist breakdown of your Taylor Swift listening habits</i></p>

    </header>
    
    
    <!-- Main Navigation Tabs -->
    <div class="card">
        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showViewMode('home')">Ohh, hi!!</button>
            <button class="nav-tab" onclick="showViewMode('albums')">By Era</button>
            <button class="nav-tab" onclick="showViewMode('years')">By Year</button>
            <button class="nav-tab" onclick="showViewMode('ranking')">By Month</button>
        </div>

        <div id="home-view" class="stats-view active">
            <h2>👋 Ohh, hi!!</h2>
            <h3>Welcome to <i>In Summation</i></h3>
            <p>The most comprehensive musical report of your Swiftly listening habits.</p>
            
            {f'''
                <h3 style="margin-top: 0; color: var(--accent);">"{random_quote['quote']}"</h3>
                <p style="margin: 0; font-size: 0.9rem; color: #666;">
                    — {random_quote['song']} • {random_quote['album']}
                </p>
            ''' if random_quote else ''}
            
            <h2>From the Vault: <span id="current-date"></span></h2>
            {"".join([f"""
            <div class="album-row">
                <div class="album-info">
                    <div class="album-color" style="background-color: var(--accent);"></div>
                    <span>{year}</span>
                </div>
                <div class="album-percentage">{song}</div>
            </div>
            """ for year, song in sorted(time_capsule_songs.items(), reverse=True)])}
            
            <script>
                // Update the date when the page loads
                document.addEventListener('DOMContentLoaded', function() {{
                    const now = new Date();
                    const options = {{ month: 'long', day: 'numeric' }};
                    document.getElementById('current-date').textContent = now.toLocaleDateString('en-US', options);
                }});
            </script>
        </div>

            
        <!-- TAB - By Year -->
        <div id="years-view" class="stats-view">
            <!-- Year Navigation Tabs -->
            <div class="nav-tabs">
                <button class="nav-tab active" onclick="showYearView('all-time')">Forever & Always</button>
                {"".join([f"""
                <button class="nav-tab" onclick="showYearView('{year}')">{year}</button>
                """ for year in sorted(results['taylor_minutes_by_year'].keys(), reverse=True)])}
            </div>

<div class="album-row total-minutes-row" style="margin-top: 20px; background-color: var(--highlight); display: flex; align-items: center;">
    <div class="album-percentage total-minutes-value" style="text-align: left; color: black; flex-grow: 1; font-weight: 400;" id="anniversary-text">
        {format_anniversaries(release_anniversaries.get(datetime.now().year, "No major releases this year"))}
    </div>
</div>


            <h2>Yearly Breakdown</h2>
            <!-- All Time Year View -->
            <div id="all-time-year-view" class="stats-view active">
                <div class="stacked-bar">
                    {"".join([f"""
                    <div class="stacked-segment" style="width: {(minutes / total_taylor_minutes) * 100 if total_taylor_minutes > 0 else 0}%; background-color: {album_colors.get(album, '#FFFFFF')};">
                        <div class="stacked-segment-tooltip">
                            <b>{album}</b><br>
                            {round(minutes)} min ({(minutes / total_taylor_minutes) * 100 if total_taylor_minutes > 0 else 0:.1f}%)
                        </div>
                    </div>
                    """ for album, minutes in sorted(results['total_album_minutes'].items(), key=lambda x: x[1], reverse=True)])}
                </div>
                
                {"".join([f"""
                <div class="album-row">
                    <div class="album-info">
                        <div class="album-color" style="background-color: {album_colors.get(album, '#FFFFFF')};"></div>
                        <span>{album}</span>
                    </div>
                    <div class="album-percentage">{(minutes / total_taylor_minutes) * 100 if total_taylor_minutes > 0 else 0:.1f}%</div>
                </div>
                """ for album, minutes in sorted(results['total_album_minutes'].items(), key=lambda x: x[1], reverse=True)])}
                
                <div class="album-row total-minutes-row">
                    <div class="album-info">
                        <div class="album-color" style="background-color: var(--accent);"></div>
                        <span class="total-minutes-text"><i>In Summation</i></span>
                    </div>
                    <div class="album-percentage total-minutes-value">{round(total_taylor_minutes)} min</div>
                </div>
            </div>
            
            <!-- Individual Year Views -->
            {"".join([f"""
            <div id="{year}-year-view" class="stats-view">
                <div class="stacked-bar">
                    {"".join([f"""
                    <div class="stacked-segment" style="width: {(minutes / results['taylor_minutes_by_year'][year]) * 100 if results['taylor_minutes_by_year'][year] > 0 else 0}%; background-color: {album_colors.get(album, '#FFFFFF')};">
                        <div class="stacked-segment-tooltip">
                            <b>{album}</b><br>
                            {round(minutes)} min ({(minutes / results['taylor_minutes_by_year'][year]) * 100 if results['taylor_minutes_by_year'][year] > 0 else 0:.1f}%)
                        </div>
                    </div>
                    """ for album, minutes in sorted(results['album_minutes_by_year'].get(year, {}).items(), key=lambda x: x[1], reverse=True)])}
                </div>
                
                {"".join([f"""
                <div class="album-row">
                    <div class="album-info">
                        <div class="album-color" style="background-color: {album_colors.get(album, '#FFFFFF')};"></div>
                        <span>{album}</span>
                    </div>
                    <div class="album-percentage">{(minutes / results['taylor_minutes_by_year'][year]) * 100 if results['taylor_minutes_by_year'][year] > 0 else 0:.1f}%</div>
                </div>
                """ for album, minutes in sorted(results['album_minutes_by_year'].get(year, {}).items(), key=lambda x: x[1], reverse=True)])}
                
                <div class="album-row total-minutes-row">
                    <div class="album-info">
                        <div class="album-color" style="background-color: var(--accent);"></div>
                        <span class="total-minutes-text"><i>In Summation</i></span>
                    </div>
                    <div class="album-percentage total-minutes-value">{round(results['taylor_minutes_by_year'][year])} min</div>
                </div>
            </div>
            """ for year in sorted(results['taylor_minutes_by_year'].keys())])}

            <h2>Song Breakdown</h2>

            <!-- All Time Songs View -->
            <div id="all-time-songs-view" class="stats-view active">
                <ul class="song-list">
                    {"".join([f"""
                    <li class="{'total-minutes-row' if i < 3 else 'song-item'}">
                        <div class="album-info">
                            <div class="song-number {'song-number-top' if i < 3 else ''}" 
                                style="background-color: var(--accent);">{i+1}</div>
                            <span class="{'total-minutes-text' if i < 3 else 'song-title'}">{song}</span>
                            {f'<div class="album-percentage total-minutes-value">{count} <i class="fa-solid fa-play"></i></div>' if i < 3 else ''}
                        </div>
                    </li>
                    """ for i, (song, count) in enumerate(top_songs)])}
                </ul>
            </div>

            <!-- Yearly Songs Views -->
            {"".join([f"""
            <div id="{year}-songs-view" class="stats-view">
                <ul class="song-list">
                    {"".join([f"""
                    <li class="{'total-minutes-row' if i < 3 else 'song-item'}">
                        <div class="album-info">
                            <div class="song-number {'song-number-top' if i < 3 else ''}" 
                                style="background-color: var(--accent);">{i+1}</div>
                            <span class="{'total-minutes-text' if i < 3 else 'song-title'}">{song}</span>
                            {f'<div class="album-percentage total-minutes-value">{count} <i class="fa-solid fa-play"></i></div>' if i < 3 else ''}
                        </div>
                    </li>
                    """ for i, (song, count) in enumerate(get_top_songs_for_year(results, year, taylor_version_mapping))])}
                </ul>
            </div>
            """ for year in sorted(results['taylor_minutes_by_year'].keys())])}
            </div>


<!-- TAB2 - ERAS -->
<div id="albums-view" class="stats-view">
    <!-- Album Navigation Tabs -->
<div class="nav-tabs">
    <button class="nav-tab active" onclick="showAlbumView('all-albums')">Swiftie Era</button>
    {"".join([f"""
    <button class="nav-tab" onclick="showAlbumView('{album}')">{album}</button>
    """ for album in custom_album_order if album in results['total_album_minutes']])}
</div>
    
    <!-- All Albums View -->
    <div id="all-albums-album-view" class="stats-view active">
        <h2>Yearly Breakdown</h2>

        
        <div class="stacked-bar">
            {"".join([f"""
            <div class="stacked-segment" style="width: {(minutes / total_taylor_minutes) * 100 if total_taylor_minutes > 0 else 0}%; background-color: {album_colors.get(album, '#FFFFFF')};">
                <div class="stacked-segment-tooltip">
                    <b>{album}</b><br>
                    {round(minutes)} min ({(minutes / total_taylor_minutes) * 100 if total_taylor_minutes > 0 else 0:.1f}%)
                </div>
            </div>
            """ for album, minutes in sorted(results['total_album_minutes'].items(), key=lambda x: x[1], reverse=True)])}
        </div>
        
        {"".join([f"""
        <div class="album-row">
            <div class="album-info">
                <div class="album-color" style="background-color: {album_colors.get(album, '#FFFFFF')};"></div>
                <span>{album}</span>
            </div>
            <div class="album-percentage">{round(minutes)} min</div>
        </div>
        """ for album, minutes in sorted_albums])}
        
        <div class="album-row total-minutes-row">
            <div class="album-info">
                <div class="album-color" style="background-color: var(--accent);"></div>
                <span class="total-minutes-text"><i>In Summation</i></span>
            </div>
            <div class="album-percentage total-minutes-value">{round(total_taylor_minutes)} min</div>
        </div>
    </div>
    
    <!-- Individual Album Views -->
    {"".join([f"""
    <div id="{album}-album-view" class="stats-view">
       

        <div class="album-info-box" style="background-color: {album_colors.get(album, '#FFFFFF')}30;">  <!-- Added 30% opacity (hex '30') -->
            <div class="album-cover">
                <img src="{album_info.get(album, {}).get('image', 'default.jpg')}" alt="{album} Cover">
            </div>
            <div class="album-details">
                <h3>{album}<br><i>{album_info.get(album, {}).get('fun_fact', '')}</i></h3>
                <div class="album-meta">
                    <p><b>Released:</b> {album_info.get(album, {}).get('release_date', 'N/A')}</p>
                    <p><b>Taylor's Version:</b> {album_info.get(album, {}).get('taylor_version', 'N/A')}</p>                    
                </div>
            </div>
        </div>

        <h2>Yearly Breakdown</h2>

         <div class="stacked-bar">
            {"".join([f"""
            <div class="stacked-segment {'highlighted' if a == album else 'shaded'}" 
                 style="width: {(m / total_taylor_minutes) * 100 if total_taylor_minutes > 0 else 0}%; 
                        background-color: {album_colors.get(a, '#FFFFFF')};">
                <div class="stacked-segment-tooltip">
                    <b>{a}</b><br>
                    {round(m)} min ({(m / total_taylor_minutes) * 100 if total_taylor_minutes > 0 else 0:.1f}%)
                </div>
            </div>
            """ for a, m in sorted(results['total_album_minutes'].items(), key=lambda x: x[1], reverse=True)])}
        </div>
        
        {"".join([f"""
        <div class="album-row">
            <div class="album-info">
                <div class="album-color" style="background-color: {album_colors.get(album, '#FFFFFF')};"></div>
                <span>{year}</span>
            </div>
            <div class="album-percentage">{round(minutes)} min</div>
        </div>
        """ for year, minutes in sorted((y, m) for y, albums in results['album_minutes_by_year'].items() for album_name, m in albums.items() if album_name == album)])}
        
        <div class="album-row total-minutes-row">
            <div class="album-info">
                <div class="album-color" style="background-color: {album_colors.get(album, '#FFFFFF')};"></div>
                <span class="total-minutes-text"><i>In Summation</i></span>
            </div>
            <div class="album-percentage total-minutes-value">{round(results['total_album_minutes'][album])} min</div>
        </div>
    </div>
    """ for album, _ in sorted_albums])}


<h2>Song Breakdown</h2>

<!-- All Albums Songs View -->
<div id="all-albums-songs-view" class="stats-view active">
    <ul class="song-list">
        {"".join([f"""
        <li class="{'total-minutes-row' if i < 3 else 'song-item'}">
            <div class="album-info">
                <div class="song-number {'song-number-top' if i < 3 else ''}" 
                    style="background-color: var(--accent);">{i+1}</div>
                <span class="{'total-minutes-text' if i < 3 else 'song-title'}">{song}</span>
                {f'<div class="album-percentage total-minutes-value">{count} <i class="fa-solid fa-play"></i></div>' if i < 3 else ''}
            </div>
        </li>
        """ for i, (song, count) in enumerate(top_songs)])}
    </ul>
</div>

<!-- Album Songs Views -->
{"".join([f"""
<div id="{album}-songs-view" class="stats-view">
    <ul class="song-list">
        {"".join([f"""
        <li class="{'total-minutes-row' if i < 3 else 'song-item'}">
            <div class="album-info">
                <div class="song-number {'song-number-top' if i < 3 else ''}" 
                    style="background-color: {album_colors.get(album, '#FFFFFF')};">{i+1}</div>
                <span class="{'total-minutes-text' if i < 3 else 'song-title'}">{song}</span>
                {f'<div class="album-percentage total-minutes-value">{count} <i class="fa-solid fa-play"></i></div>' if i < 3 else ''}
            </div>
        </li>
        """ for i, (song, count) in enumerate(get_top_songs_for_album(results, album, taylor_version_mapping))])}
    </ul>
</div>
""" for album, _ in sorted_albums])}
</div>

    
    
    

    <div id="ranking-view" class="stats-view">
        <!-- Year Navigation -->
        <div class="nav-tabs" id="year-tabs">
            {"".join([f"""
            <button class="nav-tab {'active' if i == 0 else ''}" 
                    onclick="showYear('{year}')">
                {year}
            </button>
            """ for i, year in enumerate(years)])}
        </div>
    
        <!-- Month Navigation (hidden by default) -->
        {"".join([f"""
        <div class="nav-tabs month-nav" id="month-tabs-{year}" style="display: {'flex' if i == 0 else 'none'};">
            {"".join([f"""
            <button class="nav-tab {'active' if j == 0 and i == 0 else ''}" 
                    onclick="showMonth('{month}')">
                {datetime.strptime(month + '-01', '%Y-%m-%d').strftime('%b')}
            </button>
            """ for j, month in enumerate([m for m in reversed(sorted_months) if m.startswith(year)])])}
        </div>
        """ for i, year in enumerate(years)])}
    
        <!-- Monthly Content -->
        {"".join([f"""
        <div class="month-section stats-view" id="month-{month}" style="display: {'block' if i == 0 and j == 0 else 'none'};">
            
            
            <h2>{datetime.strptime(month + '-01', '%Y-%m-%d').strftime('%B %Y')}</h2>
            
            <div class="album-row total-minutes-row">
                <div class="album-info">
                    <div class="album-color" style="background-color: var(--accent);"></div>
                    <span class="total-minutes-text"><i>In Summation</i></span>
                </div>
<div class="album-percentage total-minutes-value">{round(monthly_stats[month]['minutes'])} min</div>            </div>


        
        <h3>Albums</h3>
        <ul class="album-list">
            {"".join([f"""
            <li class="album-item">
                <div class="album-info">
                    <div class="album-color" style="background-color: {album_colors.get(album, '#FFFFFF')};"></div>
                    <span>{album}</span>
                </div>
                <div>
                    {get_position_trend(month, album, 'albums', monthly_stats, prev_month_stats)}
                </div>
            </li>
            """ for album, count in monthly_stats[month]['albums'].most_common()])}
        </ul>
        
        <h3>Top Songs</h3>
        <ul class="song-list">
            {"".join([f"""
            <li class="{'total-minutes-row' if i < 3 else 'song-item'}">
                <div class="album-info">
                    <div class="song-number {'song-number-top' if i < 3 else ''}" 
                        style="background-color: var(--accent);">{i+1}</div>
                    <span class="{'total-minutes-text' if i < 3 else 'song-title'}">{song}</span>
                    <div class="{'album-percentage total-minutes-value' if i < 3 else 'play-count'}">{get_position_trend(month, song, 'songs', monthly_stats, prev_month_stats)}</div>
                </div>
            </li>
            """ for i, (song, count) in enumerate(monthly_stats[month]['songs'].most_common(31))])}
        </ul>
        </div>
        """ for i, year in enumerate(years) 
            for j, month in enumerate([m for m in reversed(sorted_months) if m.startswith(year)])])}
    </div>
    </div>













<script>
    // Function to switch between year and album views
    function showViewMode(mode) {{
        // Update active tab
        document.querySelectorAll('.nav-tab').forEach(tab => {{
            tab.classList.remove('active');
        }});
        event.target.classList.add('active');
        
        // Show/hide views
        document.getElementById('home-view').classList.remove('active');
        document.getElementById('years-view').classList.remove('active');
        document.getElementById('albums-view').classList.remove('active');
        document.getElementById('ranking-view').classList.remove('active');
        document.getElementById(mode + '-view').classList.add('active');
        
        // Activate the default tab for each view
        if (mode === 'albums') {{
            document.querySelectorAll('#albums-view .nav-tab').forEach(tab => tab.classList.remove('active'));
            document.querySelector('#albums-view .nav-tab').classList.add('active');
            showAlbumView('all-albums');
        }} else if (mode === 'years') {{
            document.querySelectorAll('#years-view .nav-tab').forEach(tab => tab.classList.remove('active'));
            document.querySelector('#years-view .nav-tab').classList.add('active');
            showYearView('all-time');
        }} else if (mode === 'ranking') {{
            // For monthly view, activate the most recent year and month
            const yearTabs = document.querySelectorAll('#year-tabs .nav-tab');
            if (yearTabs.length > 0) {{
                yearTabs.forEach(tab => tab.classList.remove('active'));
                yearTabs[0].classList.add('active');
                showYear(yearTabs[0].textContent.trim());
            }}
        }}
    }}

    
    // Function to show year-specific views
    function showYearView(viewId) {{
        // Update active tab
        document.querySelectorAll('#years-view .nav-tab').forEach(tab => {{
            tab.classList.remove('active');
        }});
        event.target.classList.add('active');
        
        // Show/hide album views
        document.querySelectorAll('#years-view [id$="-year-view"]').forEach(el => {{
            el.classList.remove('active');
        }});
        document.getElementById(viewId + '-year-view').classList.add('active');
        
        // Show/hide song views
        document.querySelectorAll('#years-view [id$="-songs-view"]').forEach(el => {{
            el.classList.remove('active');
        }});
        document.getElementById(viewId + '-songs-view').classList.add('active');
        
    // Update the anniversary display
    const year = viewId === 'all-time' ? new Date().getFullYear() : viewId;
    const anniversaryData = {{
        2024: "19.04 <i>THE TORTURED POETS DEPARTMENT</i>",
        2023: "07.07 <i>Speak Now (Taylor's Version)</i><br>27.10 <i>1989 (Taylor's Version)</i>",
        2022: "21.10 <i>Midnights</i>",
        2021: "09.04 <i>Fearless (Taylor's Version)</i><br>12.11 <i>Red (Taylor's Version)</i>",
        2020: "24.07 <i>folklore</i><br>11.12 <i>evermore</i>",
        2019: "23.08 <i>Lover</i>",
        2017: "09.06 <i>Back to Spotify</i><br>10.11 <i>reputation</i>",
        2014: "27.10 <i>1989</i>",
        2012: "22.10 <i>Red</i>",
        2010: "25.10 <i>Speak Now</i>",
        2008: "11.11 <i>Fearless</i>",
        2006: "24.10 <i>Taylor Swift</i>"
    }};
    document.getElementById('anniversary-text').innerHTML = anniversaryData[year] || "No major releases this year";

    }}
    
    function format_anniversaries(text) {{
        if (text === "No major releases this year") return text;
        
        // This regex matches dates in format "Month Day" or "Month Day, Year"
        return text.replace(/([A-Za-z]+ \d{1,2}(?:, \d{4})?)/g, '<strong>$1</strong>');
    }}

    // Function to show album-specific views with highlighting
    function showAlbumView(viewId) {{
        // Update active tab
        document.querySelectorAll('#albums-view .nav-tab').forEach(tab => {{
            tab.classList.remove('active');
        }});
        event.target.classList.add('active');
        
        // Show/hide album views
        document.querySelectorAll('#albums-view [id$="-album-view"]').forEach(el => {{
            el.classList.remove('active');
        }});
        document.getElementById(viewId + '-album-view').classList.add('active');
        
        // Show/hide song views
        document.querySelectorAll('#albums-view [id$="-songs-view"]').forEach(el => {{
            el.classList.remove('active');
        }});
        document.getElementById(viewId + '-songs-view').classList.add('active');
        
        // Only update highlighting if not in "all-albums" view
        if (viewId !== 'all-albums') {{
            const albumName = viewId;
            document.querySelectorAll('#albums-view .stacked-segment').forEach(segment => {{
                segment.classList.remove('highlighted', 'shaded');
                if (segment.textContent.includes(albumName)) {{
                    segment.classList.add('highlighted');
                    segment.style.borderRight = '2px solid var(--primary)';
                }} else {{
                    segment.classList.add('shaded');
                    segment.style.borderRight = 'none';
                }}
            }});
        }} else {{
            // Reset all segments to normal in "all-albums" view
            document.querySelectorAll('#albums-view .stacked-segment').forEach(segment => {{
                segment.classList.remove('highlighted', 'shaded');
                segment.style.borderRight = '2px solid var(--primary)';
                segment.style.opacity = '1';
            }});
        }}
    }}


    function showYear(selectedYear) {{
        // Update active year tab
        document.querySelectorAll('#year-tabs .nav-tab').forEach(tab => {{
            tab.classList.remove('active');
            if (tab.getAttribute('onclick') === `showYear('${{selectedYear}}')`) {{
                tab.classList.add('active');
            }}
        }});
        
        // Hide all month sections
        document.querySelectorAll('.month-section').forEach(section => {{
            section.style.display = 'none';
        }});
        
        // Show month tabs for selected year
        document.querySelectorAll('.month-nav').forEach(nav => {{
            nav.style.display = 'none';
        }});
        document.getElementById(`month-tabs-${{selectedYear}}`).style.display = 'flex';
        
        // Activate first month tab and show its content
        const monthTabs = document.querySelectorAll(`#month-tabs-${{selectedYear}} .nav-tab`);
        if (monthTabs.length > 0) {{
            monthTabs.forEach(tab => tab.classList.remove('active'));
            monthTabs[0].classList.add('active');
            
            // Get the month from the first tab's onclick attribute
            const onclickContent = monthTabs[0].getAttribute('onclick');
            const monthMatch = onclickContent.match(/showMonth\\('([^']+)'\\)/);
            if (monthMatch && monthMatch[1]) {{
                document.getElementById(`month-${{monthMatch[1]}}`).style.display = 'block';
            }}
        }}
    }}

    function showMonth(month) {{
        // Update active month tab
        const allMonthTabs = document.querySelectorAll('.month-nav .nav-tab');
        allMonthTabs.forEach(tab => {{
            tab.classList.remove('active');
            if (tab.getAttribute('onclick') === `showMonth('${{month}}')`) {{
                tab.classList.add('active');
            }}
        }});
        
        // Hide all month sections
        document.querySelectorAll('.month-section').forEach(section => {{
            section.style.display = 'none';
        }});
        
        // Show selected month content
        document.getElementById(`month-${{month}}`).style.display = 'block';
    }}
</script>
<footer>
  <p><i class="fa-solid fa-music"></i> {last_song_date.strftime('%Y-%m-%d')} | Made with <i class="fas fa-heart"></i></p>
</footer>
</body>
</html>
    """

    # Save the HTML to a file
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    return html






# Run the analysis and generate the report with all required arguments
results = analyze_taylor_swift_data(file_names, album_mapping, taylor_version_mapping)
generate_html_report(results, album_colors, taylor_version_mapping)
