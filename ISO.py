import json
import os
import re

# File names
file_names = [
    "Streaming_History_Audio_2015-2018_0.json",
    "Streaming_History_Audio_2018-2021_1.json",
    "Streaming_History_Audio_2021-2022_2.json",
    "Streaming_History_Audio_2022-2023_3.json",
    "Streaming_History_Audio_2023-2025_4.json",
    "Streaming_History_Audio_2025_5.json"
]

# Taylor Swift collaboration track URIs
taylor_collaborations = [
    "spotify:track:73W5aXorr5vxrySFcoZqIN",
    "spotify:track:0hhzNPE68LWLfgZwdpxVdR",
    "spotify:track:2bzUVEvpZ7At5cYz1kOLI9",
    "spotify:track:55n9yjI6qqXh5F2mYvUc2y",
    "spotify:track:7wo2UNeQBowm28hfAJsEMz",
    "spotify:track:60hGQrn24APqEFSLObLeDc",
    "spotify:track:6N1K5OVVCopBjGViHs2IvP",
    "spotify:track:6INztpNwOTlfSKTuPo0HOP",
    "spotify:track:1MaqkdFNIKPdpQGDzme5ss"
]

def clean_text(text):
    """Replace curly quotes with straight quotes"""
    if not text or not isinstance(text, str):
        return text
    text = text.replace('‘', "'").replace('’', "'")
    text = text.replace('“', '"').replace('”', '"')
    text = text.replace('…', '...').replace('–', '-').replace('—', '-')
    return text

def is_taylor_swift_song(entry):
    """Check if an entry is a Taylor Swift song or collaboration"""
    artist_name = entry.get('master_metadata_album_artist_name', '')
    if artist_name and 'taylor swift' in artist_name.lower():
        return True
    track_uri = entry.get('spotify_track_uri', '')
    if track_uri in taylor_collaborations:
        return True
    return False

def load_mapping(mapping_file_path):
    """Load the mapping file and create a lookup dictionary"""
    if not os.path.exists(mapping_file_path):
        print(f"Error: Mapping file '{mapping_file_path}' not found!")
        return None
    
    with open(mapping_file_path, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    
    # Create a lookup dictionary: spotify_uri -> mapping_data
    uri_mapping = {}
    for track_id, mapping_data in mapping.items():
        spotify_uris = mapping_data.get('all_spotify_uris', [])
        for uri in spotify_uris:
            uri_mapping[uri] = {
                'new_name': mapping_data['new_name'],
                'new_album': mapping_data['new_album'],
                'new_artist': mapping_data['new_artist']
            }
    
    print(f"Loaded mapping with {len(mapping)} song groups and {len(uri_mapping)} total track mappings")
    return uri_mapping

def create_mapped_entry(original_entry, mapping_data):
    """Create a new entry with only the specified fields and mapped values"""
    return {
        "ts": original_entry.get("ts"),
        "ms_played": original_entry.get("ms_played"),
        "master_metadata_track_name": mapping_data['new_name'],
        "master_metadata_album_artist_name": mapping_data['new_artist'],
        "master_metadata_album_album_name": mapping_data['new_album'],
        "spotify_track_uri": original_entry.get("spotify_track_uri")
    }

def process_file_for_mapped_songs(file_path, uri_mapping):
    """Process a single file and extract ONLY mapped Taylor Swift songs"""
    mapped_entries = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        print(f"  Scanning {len(data)} entries...")
        
        taylor_count = 0
        mapped_count = 0
        
        for entry in data:
            # Check if it's a Taylor Swift song
            if is_taylor_swift_song(entry):
                taylor_count += 1
                track_uri = entry.get('spotify_track_uri')
                
                # Check if this song is in our mapping
                if track_uri and track_uri in uri_mapping:
                    mapped_count += 1
                    
                    # Clean the original text fields
                    if 'master_metadata_track_name' in entry:
                        entry['master_metadata_track_name'] = clean_text(entry['master_metadata_track_name'])
                    if 'master_metadata_album_artist_name' in entry:
                        entry['master_metadata_album_artist_name'] = clean_text(entry['master_metadata_album_artist_name'])
                    if 'master_metadata_album_album_name' in entry:
                        entry['master_metadata_album_album_name'] = clean_text(entry['master_metadata_album_album_name'])
                    
                    # Create new entry with only the required fields and mapped values
                    mapped_entry = create_mapped_entry(entry, uri_mapping[track_uri])
                    mapped_entries.append(mapped_entry)
        
        print(f"  Found {taylor_count} Taylor Swift songs, {mapped_count} were mapped and included")
        return mapped_entries
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return []

def create_mapped_streaming_history():
    """Main function to create new streaming history with ONLY mapped Taylor Swift songs"""
    
    # Look for mapping file
    mapping_files = ['taylor_swift_final_mapping.json', 'taylor_swift_mapping_template.json']
    mapping_file = None
    
    for file in mapping_files:
        if os.path.exists(file):
            mapping_file = file
            break
    
    if not mapping_file:
        print("No mapping file found! Please make sure you have either:")
        print("  - taylor_swift_final_mapping.json")
        print("  - taylor_swift_mapping_template.json")
        return
    
    print(f"Using mapping file: {mapping_file}")
    
    # Load the mapping
    uri_mapping = load_mapping(mapping_file)
    if not uri_mapping:
        return
    
    # Process all files and collect ONLY mapped Taylor Swift songs
    all_mapped_entries = []
    total_entries_scanned = 0
    total_taylor_songs = 0
    total_mapped_songs = 0
    
    for file_name in file_names:
        if not os.path.exists(file_name):
            print(f"Warning: File {file_name} not found. Skipping...")
            continue
        
        print(f"\nProcessing {file_name}...")
        mapped_entries = process_file_for_mapped_songs(file_name, uri_mapping)
        
        if mapped_entries:
            all_mapped_entries.extend(mapped_entries)
            total_mapped_songs += len(mapped_entries)
    
    if not all_mapped_entries:
        print("No mapped Taylor Swift songs found!")
        return
    
    # Create output filename
    base_name = os.path.splitext(mapping_file)[0]
    output_file = f"{base_name}_MAPPED_ONLY.json"
    
    # Save ONLY the mapped Taylor Swift songs
    print(f"\nSaving mapped Taylor Swift songs to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_mapped_entries, f, indent=2, ensure_ascii=False)
    
    # Generate summary report
    generate_mapping_summary(all_mapped_entries, uri_mapping, output_file)
    
    print(f"\n✅ Successfully created mapped songs history!")
    print(f"📁 Output file: {output_file}")
    print(f"🎵 Total mapped Taylor Swift songs: {len(all_mapped_entries):,}")
    print(f"📊 Unique tracks: {len(set(entry['spotify_track_uri'] for entry in all_mapped_entries))}")

def generate_mapping_summary(mapped_entries, uri_mapping, output_file):
    """Generate a summary report of the mapped songs"""
    
    # Count statistics
    song_counts = {}
    album_counts = {}
    artist_counts = {}
    
    for entry in mapped_entries:
        song_name = entry.get('master_metadata_track_name', 'Unknown')
        album_name = entry.get('master_metadata_album_album_name', 'Unknown')
        artist_name = entry.get('master_metadata_album_artist_name', 'Unknown')
        
        song_counts[song_name] = song_counts.get(song_name, 0) + 1
        album_counts[album_name] = album_counts.get(album_name, 0) + 1
        artist_counts[artist_name] = artist_counts.get(artist_name, 0) + 1
    
    # Save summary report
    report_file = output_file.replace('.json', '_SUMMARY.txt')
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("MAPPED TAYLOR SWIFT SONGS SUMMARY\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"Total mapped songs: {len(mapped_entries):,}\n")
        f.write(f"Unique songs: {len(song_counts)}\n")
        f.write(f"Unique albums: {len(album_counts)}\n")
        f.write(f"Mapping coverage: {len(uri_mapping)} tracks in mapping\n\n")
        
        f.write("SONGS BY PLAY COUNT (Top 20):\n")
        f.write("-" * 30 + "\n")
        for song, count in sorted(song_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
            f.write(f"{count:6d} plays - {song}\n")
        
        f.write("\nALBUMS BY PLAY COUNT:\n")
        f.write("-" * 25 + "\n")
        for album, count in sorted(album_counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{count:6d} plays - {album}\n")
        
        f.write(f"\nARTIST DISTRIBUTION:\n")
        f.write("-" * 25 + "\n")
        for artist, count in artist_counts.items():
            f.write(f"{count:6d} plays - {artist}\n")
    
    print(f"📋 Summary report saved to: {report_file}")
    
    # Print quick summary to console
    print(f"\n📊 MAPPED SONGS SUMMARY:")
    print(f"   Total mapped songs: {len(mapped_entries):,}")
    print(f"   Unique songs: {len(song_counts)}")
    print(f"   Unique albums: {len(album_counts)}")
    
    if song_counts:
        print(f"\n🎵 Top 5 most played songs:")
        for song, count in sorted(song_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {count:6d} plays - {song}")

def show_sample_mapped_entries(output_file):
    """Show a sample of the mapped entries"""
    if not os.path.exists(output_file):
        return
    
    with open(output_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n🔍 Sample of first 5 mapped entries:")
    print("-" * 50)
    
    for i, entry in enumerate(data[:5], 1):
        print(f"{i}. {entry.get('master_metadata_track_name', 'Unknown')}")
        print(f"   Album: {entry.get('master_metadata_album_album_name', 'Unknown')}")
        print(f"   Artist: {entry.get('master_metadata_album_artist_name', 'Unknown')}")
        print(f"   Played: {entry.get('ts', 'Unknown')}")
        print(f"   Duration: {entry.get('ms_played', 0)} ms")
        print(f"   URI: {entry.get('spotify_track_uri', 'Unknown')}")
        print()

if __name__ == "__main__":
    create_mapped_streaming_history()
    
    # Show sample of the created file
    mapping_files = ['taylor_swift_final_mapping.json', 'taylor_swift_mapping_template.json']
    for file in mapping_files:
        if os.path.exists(file):
            base_name = os.path.splitext(file)[0]
            output_file = f"{base_name}_MAPPED_ONLY.json"
            if os.path.exists(output_file):
                show_sample_mapped_entries(output_file)
            break