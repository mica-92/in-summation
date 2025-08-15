from collections import Counter, defaultdict
from datetime import datetime
from mapps import album_colors, taylor_version_mapping, album_mapping, file_names
import json

def merge_taylor_versions(song_counter, version_mapping):
    """
    Merge counts of Taylor's Version and non-Taylor's Version songs.
    """
    merged_counter = Counter()
    for song, count in song_counter.items():
        unified_song = version_mapping.get(song, song)
        merged_counter[unified_song] += count
    return merged_counter

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
            --font-size: 16px;
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
        
        /* Stacked bar chart styles */
        .stacked-bar {{
            height: 40px;
            background-color: var(--secondary);
            border: var(--border);
            margin-bottom: 30px;
            position: relative;
            display: flex;
        }}
        
        .stacked-segment {{
            height: 100%;
            position: relative;
            border-right: 2px solid var(--primary);
            z-index: 1;
        }}
        
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
            font-size: 12px;
            white-space: nowrap;
            margin-bottom: 5px;
            opacity: 0;
            visibility: hidden;
            transition: all 0.2s ease;
            z-index: 10;
            pointer-events: none;
        }}

        .stacked-segment:hover .stacked-segment-tooltip {{
            opacity: 1;
            visibility: visible;
        }}

        .stacked-segment:hover {{
            opacity: 1;
            transform: scaleY(1.05);
            z-index: 2; /* Bring hovered segment above others */
        }}

        .stacked-segment-tooltip::after {{
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            border-color: rgba(0, 0, 0, 0.8) transparent transparent transparent;
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

        <!-- Home View -->
        <div id="home-view" class="stats-view active">
            <h3>Welcome to <i>In Summation</i></h3>
            <p>The most comprehensive musical report of your Swiftly listening habits.</p>
        </div>

        <!-- Yearly View -->
        <div id="years-view" class="stats-view">
            <!-- Year Navigation Tabs -->
            <div class="nav-tabs">
                <button class="nav-tab active" onclick="showYearView('all-time')">Forever & Always</button>
                {"".join([f"""
                <button class="nav-tab" onclick="showYearView('{year}')">{year}</button>
                """ for year in sorted(results['taylor_minutes_by_year'].keys(), reverse=True)])}
            </div>

            <h2>Listening Time</h2>
            
            <!-- All Time Year View -->
            <div id="all-time-year-view" class="stats-view active">
                <div class="stacked-bar">
                    {"".join([f"""
                    <div class="stacked-segment" style="width: {(minutes / total_taylor_minutes) * 100 if total_taylor_minutes > 0 else 0}%; background-color: {album_colors.get(album, '#FFFFFF')};">
                        <div class="stacked-segment-tooltip">
                            {album}<br>
                            {(minutes / total_taylor_minutes) * 100 if total_taylor_minutes > 0 else 0:.1f}%<br>
                            {round(minutes)} min
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
                        <span class="total-minutes-text">In summation</span>
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
                {album}<br>
                {(minutes / results['taylor_minutes_by_year'][year]) * 100 if results['taylor_minutes_by_year'][year] > 0 else 0:.1f}%<br>
                {round(minutes)} min
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
                        <span class="total-minutes-text">In summation</span>
                    </div>
                    <div class="album-percentage total-minutes-value">{round(results['taylor_minutes_by_year'][year])} min</div>
                </div>
            </div>
            """ for year in sorted(results['taylor_minutes_by_year'].keys())])}

<h2>Songs</h2>

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
            """ for album, _ in sorted_albums])}
        </div>

        <h2>Era Statistics</h2>
        
        <!-- All Albums View -->
        <div id="all-albums-album-view" class="stats-view active">

            
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
                    <span class="total-minutes-text">In summation</span>
                </div>
                <div class="album-percentage total-minutes-value">{round(total_taylor_minutes)} min</div>
            </div>
        </div>
        
        <!-- Individual Album Views -->
        {"".join([f"""
        <div id="{album}-album-view" class="stats-view">

            
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
                    <span class="total-minutes-text">In summation</span>
                </div>
                <div class="album-percentage total-minutes-value">{round(results['total_album_minutes'][album])} min</div>
            </div>
        </div>
        """ for album, _ in sorted_albums])}

<h2>Songs</h2>

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
                    <span class="total-minutes-text">In summation</span>
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
    }}
    
    // Function to show album-specific views
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
