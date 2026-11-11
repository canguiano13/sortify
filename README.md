# Sortify
Easier playlist sorting with Spotify Web API + Rofi

## Requirements/Notes
- The track must be playing, not paused, when the shortcut is invoked.
- The app operates on the currently playing track. There is no way currently to highlight a specific song.
- API permissions that will be requested: current track, playlist listing, playlist modification, and library modification.

- As of 2026, new Spotify Web API apps in Development Mode require the app owner to have Spotify Premium. See Spotify's [quota mode documentation](https://developer.spotify.com/documentation/web-api/concepts/quota-modes).

## 0. Prerequisites
First, install the project dependencies
```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip rofi libnotify-bin unzip
```

## 1. Create a Spotify Developer app
1. Open https://developer.spotify.com/dashboard
2. Create an app.
3. In the app settings, add this exact Redirect URI:
   `http://127.0.0.1:8888/callback`
4. Copy the app's **Client ID**.

## 2. Configure the project
Add your client ID, redirect uri, and playlist name to .env

```
SPOTIFY_CLIENT_ID=your-client-id
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
PLAYLIST_NAME=TODO
```

`PLAYLIST_NAME` should be the exact name of the playlist being edited when you invoke the app (default: `TODO`).

## 3. Install python dependencies
There's a script for this. Or just install the requirements in `requirements.txt`.

```bash
./install.sh
```

## 4. Initialize Spotify auth

```bash
./launch.sh
```

You should get a browser popup asking for Spotify authorization. Approve it.
The app will cache a token under `~/.cache/spotify-todo/` -- don't share that.

## 5. (Optional) Create a global keybind or shortcut for sortify
Highly recommended to make it easy to launch sortify.
Some information about how to do this:

[ubuntu](https://askubuntu.com/questions/597395/how-to-set-custom-keyboard-shortcuts-from-terminal)
[windows](https://stackoverflow.com/questions/947492/what-is-the-easiest-way-to-add-global-keyboard-shortcuts-in-windows)
[mac](https://apple.stackexchange.com/questions/124896/how-is-it-possible-to-have-global-hotkeys-in-osx)


