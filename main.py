import sys
import time
import threading

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    from InquirerPy import inquirer
    import colorama
    colorama.init()
except ImportError:
    print("\033[31mhi so u need to do 'pip install spotipy InquirerPy colorama' to run all ts!!\033[0m")
    sys.exit(1)

################ config stuff ################
CLIENT_ID = "put client id here"
CLIENT_SECRET = "client secret here"
REDIRECT_URI = "https://127.0.0.1:8888/callback"
SCOPE = "playlist-read-private playlist-modify-private playlist-modify-public"
##############################################

# auth
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    open_browser=True,
    cache_path=".cache"
))

#spinner
def spinner(msg, stop_event):
    chars = "|/-\\"
    i = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{msg} {chars[i % len(chars)]}")
        sys.stdout.flush()
        i += 1
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * (len(msg) + 2) + "\r")

#all the playlist functions
def choose_playlist():
    playlists = sp.current_user_playlists(limit=50)
    playlist_choices = [
        {"name": f"{p['name']} ({p['tracks']['total']} tracks)", "value": p}
        for p in playlists['items']
    ]
    playlist = inquirer.select(
        message="select a playlist to scan for duplicates:",
        choices=playlist_choices,
    ).execute()
    return playlist

def get_playlist_tracks(playlist_id):
    results = sp.playlist_items(playlist_id)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks

def find_duplicates(tracks):
    seen = {}
    dupes = []
    for item in tracks:
        track = item['track']
        if not track:
            continue
        name = track['name'].strip().lower()
        artists = ", ".join(a['name'] for a in track['artists']).strip().lower()
        key = (name, artists)
        if key in seen:
            dupes.append(item)
        else:
            seen[key] = item
    return dupes

def show_duplicates(duplicates):
    print("\033[33m\nduplicate songs found:\033[0m")
    for idx, item in enumerate(duplicates, 1):
        track = item['track']
        name = track['name']
        artists = ", ".join(a['name'] for a in track['artists'])
        print(f"{idx}. {name} - {artists}")
    print(f"\033[32mtotal duplicates: {len(duplicates)}\033[0m\n")

def remove_duplicates(playlist_id, duplicates):
    uris = [item['track']['uri'] for item in duplicates]
    for i in range(0, len(uris), 100):  
        sp.playlist_remove_all_occurrences_of_items(playlist_id, uris[i:i+100])
    print(f"\033[32mremoved {len(duplicates)} duplicate tracks,.,\033[0m\n")

################ main ################
if __name__ == "__main__":
    playlist = choose_playlist()
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=spinner, args=(f"scanning playlist: {playlist['name']}...", stop_event))
    spinner_thread.start()

    tracks = get_playlist_tracks(playlist['id'])
    duplicates = find_duplicates(tracks)

    stop_event.set()
    spinner_thread.join()

    if not duplicates:
        print("\033[32mno duplicates found!!!!\033[0m")
    else:
        show_duplicates(duplicates)
        confirm = inquirer.confirm(
            message="remove these duplicates???",
            default=False
        ).execute()
        if confirm:
            remove_duplicates(playlist['id'], duplicates)
        else:
            print("\033[33mno changes made.,.\033[0m")
######################################
