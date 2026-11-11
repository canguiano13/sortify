#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyPKCE
from spotipy.cache_handler import CacheFileHandler

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

API = "https://api.spotify.com/v1"
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
TODO_NAME= os.getenv("PLAYLIST_NAME", "ToDo")

#commands possible from rofi
SCOPES = " ".join([
    "user-read-currently-playing",
    "user-modify-playback-state",
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-private",
    "playlist-modify-public",
    "user-library-modify",
])

#####
## UI
#####

#pop-up notification via notify-send
def notify(message: str, title: str = "Sortify") -> None:
    try:
        subprocess.run(
            ["notify-send", title, message],
            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except FileNotFoundError:
        try:
            subprocess.run(["rofi", "-e", message], check=False)
        except FileNotFoundError:
            print(message)

#display menu with actions
def menu(prompt: str, choices: list[str]) -> str | None:
    if not choices:
        return None
    try:
        result = subprocess.run(
            ["rofi", "-dmenu", "-i", "-p", prompt],
            input="\n".join(choices) + "\n",
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        raise SpotifyError("missing rofi. run sudo apt install rofi")
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None

#display yes/no confirmation on menu
def confirm(prompt: str) -> bool:
    return menu(prompt, ["Yes", "Cancel"]) == "Yes"

#choose which playlist to add a song to
def choose_destination(playlists: list[dict], todo_id: str) -> dict | None:
    destinations = [p for p in playlists if p.get("id") != todo_id]
    labels = {
        f'{p.get("name", "unknown song")} — {p.get("owner", {}).get("display_name", "unknown artist")}': p
        for p in destinations
    }
    #avoid ambiguous labels when two playlists share the same name 
    if len(labels) != len(destinations):
        labels = {
            f'{p.get("name", "Untitled")} — {p.get("owner", {}).get("display_name", "unknown")} [{p["id"][:6]}]': p
            for p in destinations
        }
    selected = menu("Add to which playlist?", list(labels))
    return labels.get(selected) if selected else None

             
#find and select playlist being edited
def select_edit_playlist(playlists: list[dict]) -> dict:
    #find playlist with same name
    matches = [p for p in playlists if p.get("name", "").casefold() == TODO_NAME.casefold()]
    if not matches:
        raise SpotifyError(f"couldn't find a playlist named '{TODO_NAME}' (update env?).")

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        raise SpotifyError("multiple playlists named '{TODO_NAME}'.")
    raise SpotifyError("multiple playlists named '{TODO_NAME}'.")


#####
## SPOTIFY 
####
class SpotifyError(Exception):
    pass

#call spotify api
def api(method: str, path: str, token: str, *, params=None, body=None):
    response = requests.request(
        method,
        f"{API}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        json=body,
        timeout=20,
    )
    if not response.ok:
        raise SpotifyError(f"Spotify API error ({response.status_code}): {response.text}")
    if response.status_code == 204 or not response.text.strip():
        return None
    
    try:
        return response.json()
    except ValueError:
        raise SpotifyError("unexpected response from spotify ", f"({response.status_code})")

#get the song currently playing
def current_track(token: str) -> dict:
    data = api("GET", "/me/player/currently-playing", token)

    if not data or not data.get("item"):
        raise SpotifyError("no track playing. start a song and try again.")
    if not data.get("is_playing"):
        raise SpotifyError("playback is paused. resume the song and try again.")

    track = data["item"]
    if track.get("type") != "track" or not track.get("uri"):
        raise SpotifyError("item currently playing isn't a supported music track")
    return track


#get list of playlists (in batches of 50)
def get_playlists(token: str) -> list[dict]:
    playlists = []
    offset = 0
    while True:
        data = api("GET", "/me/playlists", token, params={"limit": 50, "offset": offset})
        batch = data.get("items", [])
        playlists.extend(batch)
        if not data.get("next") or not batch:
            break
        offset += len(batch)
    return playlists


#add a song to another playlist
def add_to_playlist(token: str, playlist_id: str, uri: str) -> None:
    api("POST", f"/playlists/{playlist_id}/items", token, body={"uris": [uri]})

#remove from current playlist
def remove_from_playlist(token: str, playlist_id: str, uri: str) -> None:
    api("DELETE", f"/playlists/{playlist_id}/items", token, body={"items": [{"uri": uri}]},)

#skip current song
def skip_track(token: str ) -> None:
    api("POST", "/me/player/next", token)

#TODO save to liked songs
#def save_to_liked(token: str, uri: str) -> None:
#    api("PUT", "/me/library", token, body={"uris": [uri]})

#####
## SPOTIFY AUTH
#####
def get_token() -> str:
    client_id = os.getenv("SPOTIFY_CLIENT_ID", "").strip()

    if not client_id:
        raise SpotifyError("Missing spotify client ID. Add one to .env")

    #search for tokens in cache
    cache_dir = Path.home() / ".cache" / "sortify"
    cache_dir.mkdir(parents=True, exist_ok=True)

    auth = SpotifyPKCE(
        client_id=client_id,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
        cache_handler=CacheFileHandler(cache_path=str(cache_dir / "token-cache")),
    )

    access_token = auth.get_access_token()
    if not access_token:
        raise SpotifyError("Spotify authorization did not return an access token.")

    return access_token


#run rofi
def run() -> None:
    token = get_token()

    track = current_track(token)
    artists = ", ".join(a["name"] for a in track.get("artists", []))
    title = track.get("name", "Unknown track")
    description = f"{title} — {artists}"

    playlists = get_playlists(token)
    todo = select_edit_playlist(playlists)

    actions = [
        "⇢  Move to another playlist",
        "−  Remove from ToDo",
        "＋ Add to another playlist",
        "Cancel",
    ]
    
    #choose which action to do
    action = menu(f"{title[:32]} — choose action", actions)
    if not action or action == "Cancel":
        return

    uri = track["uri"]


    #move to another playlist
    if action.startswith("⇢  Move"):
        #add to desired playlist
        destination = choose_destination(playlists, todo["id"])
        if not destination:
            return
        add_to_playlist(token, destination["id"], uri)

        #remove from current playlist
        try:
            remove_from_playlist(token, todo["id"], uri)
        except SpotifyError as exc:
            notify(
                f'added to {destination["name"]}, but couldn\'t remove from {TODO_NAME}. '
                f'the track might in both playlists. {exc}'
            )
            return
        notify(f'moved: {description}')

    #remove from current playlist
    elif action.startswith("−  Remove"):
        if confirm(f"Remove song from {TODO_NAME}?"):
            remove_from_playlist(token, todo["id"], uri)
            notify(f"removed: {description}")

    #add to selected playlist, but keep in current playlist
    elif action.startswith("＋  Add"):
        destination = choose_destination(playlists, todo["id"])
        if not destination:
            return
        add_to_playlist(token, destination["id"], uri)
        notify(f'added: {description}')


def main():
    try:
        if "--skip" in sys.argv:
            token = get_token()
            skip_track(token)
        else:
            run()
    except SpotifyError as exc:
        notify(str(exc), "Sortify — problem")
        sys.exit(1)
    except requests.RequestException as exc:
        notify(f"Network error: {exc}", "Sortify — problem")
        sys.exit(1)

if __name__ == "__main__":
    main()
    
