import json
import os
from collections import defaultdict

def analyze_mapping_file(mapping_file_path):
    """Analyze the mapping file and print a comprehensive summary"""
    
    if not os.path.exists(mapping_file_path):
        print(f"Error: Mapping file '{mapping_file_path}' not found!")
        return
    
    # Load the mapping file
    with open(mapping_file_path, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    
    # Data structures for analysis
    albums = defaultdict(set)  # album -> set of songs
    songs = defaultdict(set)   # song -> set of albums
    song_details = {}          # song -> details
    album_song_count = defaultdict(int)  # album -> song count
    
    # Analyze the mapping
    for track_id, mapping_data in mapping.items():
        song_name = mapping_data.get('new_name', 'Unknown Song')
        album_name = mapping_data.get('new_album', 'Unknown Album')
        artist_name = mapping_data.get('new_artist', 'Unknown Artist')
        
        # Add to albums dictionary
        albums[album_name].add(song_name)
        
        # Add to songs dictionary
        songs[song_name].add(album_name)
        
        # Store song details
        if song_name not in song_details:
            song_details[song_name] = {
                'artist': artist_name,
                'track_ids': [],
                'original_versions': []
            }
        
        # Add track IDs
        all_track_ids = mapping_data.get('all_track_ids', [])
        song_details[song_name]['track_ids'].extend(all_track_ids)
        
        # Add original versions
        original_versions = mapping_data.get('original_versions', [])
        song_details[song_name]['original_versions'].extend(original_versions)
        
        # Count songs per album
        album_song_count[album_name] += 1
    
    # Print comprehensive summary
    print("=" * 80)
    print("MAPPING FILE ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"Total unique mappings: {len(mapping)}")
    print(f"Total unique albums: {len(albums)}")
    print(f"Total unique songs: {len(songs)}")
    print()
    
    # 1. Print albums and their songs (sorted alphabetically)
    print("1. ALBUMS AND THEIR SONGS:")
    print("-" * 40)
    
    for album in sorted(albums.keys()):
        album_songs = sorted(albums[album])
        print(f"\n🎵 {album} ({len(album_songs)} songs)")
        print("-" * len(album) + "-" * 15)
        
        for i, song in enumerate(album_songs, 1):
            track_count = len(song_details[song]['track_ids'])
            print(f"  {i:2d}. {song} ({track_count} track versions)")
    
    # 2. Print songs that appear in multiple albums (potential issues)
    print("\n\n2. SONGS IN MULTIPLE ALBUMS (Check for consistency):")
    print("-" * 55)
    
    multi_album_songs = {song: album_set for song, album_set in songs.items() if len(album_set) > 1}
    
    if multi_album_songs:
        for song in sorted(multi_album_songs.keys()):
            album_list = sorted(multi_album_songs[song])
            print(f"\n📝 {song} appears in {len(album_list)} albums:")
            for album in album_list:
                print(f"    • {album}")
    else:
        print("No songs appear in multiple albums. ✅")
    
    # 3. Print unique songs list
    print("\n\n3. UNIQUE SONGS (Alphabetical Order):")
    print("-" * 35)
    
    unique_songs_sorted = sorted(songs.keys())
    for i, song in enumerate(unique_songs_sorted, 1):
        album_count = len(songs[song])
        track_count = len(song_details[song]['track_ids'])
        print(f"{i:3d}. {song} ({album_count} album(s), {track_count} track versions)")
    
    # 4. Print unique albums list
    print("\n\n4. UNIQUE ALBUMS (Alphabetical Order):")
    print("-" * 35)
    
    unique_albums_sorted = sorted(albums.keys())
    for i, album in enumerate(unique_albums_sorted, 1):
        song_count = len(albums[album])
        total_tracks = sum(len(song_details[song]['track_ids']) for song in albums[album])
        print(f"{i:2d}. {album} ({song_count} songs, {total_tracks} total tracks)")
    
    # 5. Print statistics
    print("\n\n5. STATISTICS:")
    print("-" * 20)
    
    total_tracks = sum(len(details['track_ids']) for details in song_details.values())
    avg_tracks_per_song = total_tracks / len(songs) if songs else 0
    avg_songs_per_album = len(songs) / len(albums) if albums else 0
    
    print(f"Total track versions: {total_tracks}")
    print(f"Average tracks per song: {avg_tracks_per_song:.1f}")
    print(f"Average songs per album: {avg_songs_per_album:.1f}")
    
    # 6. Print songs with most versions
    print("\n\n6. SONGS WITH MOST VERSIONS:")
    print("-" * 30)
    
    songs_by_version_count = sorted(song_details.items(), 
                                   key=lambda x: len(x[1]['track_ids']), 
                                   reverse=True)
    
    for i, (song, details) in enumerate(songs_by_version_count[:10], 1):  # Top 10
        version_count = len(details['track_ids'])
        albums_list = sorted(songs[song])
        print(f"{i:2d}. {song} ({version_count} versions) - Albums: {', '.join(albums_list)}")
    
    # 7. Print potential issues
    print("\n\n7. POTENTIAL ISSUES TO CHECK:")
    print("-" * 35)
    
    issues_found = False
    
    # Check for songs with "Taylor's Version" in new_name (should have been removed)
    taylor_version_songs = [song for song in songs.keys() if "taylor's version" in song.lower()]
    if taylor_version_songs:
        print("❌ Songs still containing 'Taylor's Version' in new_name:")
        for song in taylor_version_songs:
            print(f"   - {song}")
        issues_found = True
    
    # Check for albums with "Taylor's Version" in new_album (should have been removed)
    taylor_version_albums = [album for album in albums.keys() if "taylor's version" in album.lower()]
    if taylor_version_albums:
        print("❌ Albums still containing 'Taylor's Version' in new_album:")
        for album in taylor_version_albums:
            print(f"   - {album}")
        issues_found = True
    
    # Check for songs with no track IDs
    no_track_songs = [song for song, details in song_details.items() if not details['track_ids']]
    if no_track_songs:
        print("❌ Songs with no track IDs:")
        for song in no_track_songs:
            print(f"   - {song}")
        issues_found = True
    
    if not issues_found:
        print("✅ No obvious issues detected!")
    
    # Save detailed report to file
    save_detailed_report(albums, songs, song_details, mapping_file_path)

def save_detailed_report(albums, songs, song_details, mapping_file_path):
    """Save a detailed report to a text file"""
    report_file = mapping_file_path.replace('.json', '_analysis_report.txt')
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("DETAILED MAPPING ANALYSIS REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        # Albums and songs
        f.write("ALBUMS AND THEIR SONGS:\n")
        f.write("=" * 25 + "\n\n")
        
        for album in sorted(albums.keys()):
            f.write(f"ALBUM: {album}\n")
            f.write("-" * (len(album) + 7) + "\n")
            
            for song in sorted(albums[album]):
                details = song_details[song]
                f.write(f"  • {song} ({len(details['track_ids'])} versions)\n")
                
                # Show original versions for reference
                if details['original_versions']:
                    f.write("    Original versions:\n")
                    for orig in details['original_versions'][:3]:  # Show first 3
                        f.write(f"      - '{orig.get('original_name', 'N/A')}' ")
                        f.write(f"[Album: {orig.get('original_album', 'N/A')}]\n")
                    if len(details['original_versions']) > 3:
                        f.write(f"      ... and {len(details['original_versions']) - 3} more\n")
                f.write("\n")
            f.write("\n")
    
    print(f"\n📊 Detailed report saved to: {report_file}")

def main():
    # Check for both possible mapping files
    mapping_files = ['taylor_swift_final_mapping.json', 'taylor_swift_mapping_template.json']
    
    found_file = None
    for file in mapping_files:
        if os.path.exists(file):
            found_file = file
            break
    
    if found_file:
        print(f"Analyzing mapping file: {found_file}")
        analyze_mapping_file(found_file)
    else:
        print("No mapping file found! Please make sure you have either:")
        print("  - taylor_swift_final_mapping.json (your final mapping)")
        print("  - taylor_swift_mapping_template.json (the template)")
        print("\nRun the previous script first to generate the mapping file.")

if __name__ == "__main__":
    main()