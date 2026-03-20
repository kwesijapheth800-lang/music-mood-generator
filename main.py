# =============================================================
# 🚀 main.py — Mooiz Backend (FastAPI)
# Handles routing, YouTube API calls, Google OAuth,
# SQLite persistence (saved + liked songs), and
# all page rendering via Jinja2 templates.
# =============================================================

# ── Standard library ──
import os
import sqlite3

# ── Third-party ──
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
import httpx
from dotenv import load_dotenv
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware

# =============================================================
# 🔧 INITIAL SETUP
# =============================================================

load_dotenv()  # Load .env variables (API keys, OAuth secrets)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 🔐 Session middleware — keeps the user logged in across requests.
#    Replace "super-secret-key" with a strong random string in production!
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "super-secret-key"))

# YouTube Data API v3 key (set in .env as YOUTUBE_API_KEY)
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# =============================================================
# 🗄️ DATABASE SETUP
# Creates the SQLite tables on first run if they don't exist.
# =============================================================

def init_db():
    conn = sqlite3.connect("mooiz.db")
    cursor = conn.cursor()

    # ⭐ Table for songs the user explicitly saves to their playlist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_songs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            title      TEXT,
            channel    TEXT,
            videoId    TEXT,
            thumbnail  TEXT
        )
    ''')

    # ❤️ Table for songs the user likes (used by the For You algorithm)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS liked_songs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            title      TEXT,
            channel    TEXT,
            videoId    TEXT,
            thumbnail  TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# =============================================================
# 🔐 GOOGLE OAUTH SETUP
# Uses authlib to handle the Google OpenID Connect flow.
# Required env vars: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
# =============================================================

oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"}
)

# =============================================================
# 🏠 HOME PAGE
# =============================================================

@app.get("/")
async def home(request: Request):
    """Serve the main search/discovery page."""
    return templates.TemplateResponse("index.html", {"request": request})

# =============================================================
# 🔐 LOGIN — Redirect to Google OAuth consent screen
# =============================================================

@app.get("/login")
async def login(request: Request):
    """Redirect the user to Google's OAuth login page."""
    redirect_uri = request.url_for("auth")
    return await oauth.google.authorize_redirect(request, redirect_uri)

# =============================================================
# 🔐 AUTH CALLBACK — Google redirects here after login
# =============================================================

@app.get("/auth")
async def auth(request: Request):
    """Handle the OAuth callback, store user info in session."""
    token = await oauth.google.authorize_access_token(request)
    user  = token.get("userinfo")
    request.session["user"] = dict(user)
    return RedirectResponse(url="/")

# =============================================================
# 🚪 LOGOUT
# =============================================================

@app.get("/logout")
async def logout(request: Request):
    """Clear the session and redirect to home."""
    request.session.clear()
    return RedirectResponse(url="/")

# =============================================================
# 👤 ME PAGE
# Shows the user's profile, stats, and settings.
# Also used as a JSON endpoint by the frontend to check
# if the user is currently logged in (/me → JSON).
# =============================================================

@app.get("/me")
async def me(request: Request):
    """
    If called from a browser (Accept: text/html), render the Me page.
    If called via fetch() from JS, return JSON login status.
    """
    user = request.session.get("user")

    # ── Detect if this is an API call from the frontend JS ──
    accept = request.headers.get("accept", "")
    is_api_call = "application/json" in accept or "text/html" not in accept

    if is_api_call:
        # JS fetch("/me") — just return login status
        return JSONResponse({"logged_in": bool(user)})

    # ── Full page render ──
    saved_count = 0
    liked_count = 0

    if user:
        conn = sqlite3.connect("mooiz.db")
        cursor = conn.cursor()

        # Count saved songs for this user
        cursor.execute(
            "SELECT COUNT(*) FROM saved_songs WHERE user_email=?", (user["email"],)
        )
        saved_count = cursor.fetchone()[0]

        # Count liked songs for this user
        cursor.execute(
            "SELECT COUNT(*) FROM liked_songs WHERE user_email=?", (user["email"],)
        )
        liked_count = cursor.fetchone()[0]

        conn.close()

    return templates.TemplateResponse("me.html", {
        "request":     request,
        "user":        user,
        "saved_count": saved_count,
        "liked_count": liked_count,
    })

# =============================================================
# 📚 LIBRARY PAGE
# Requires login. Shows all saved + liked songs.
# =============================================================

@app.get("/library")
async def library(request: Request):
    """Render the library page with the user's saved and liked songs."""
    user = request.session.get("user")

    if not user:
        # Not logged in → send to Google login
        return RedirectResponse(url="/login")

    conn = sqlite3.connect("mooiz.db")
    cursor = conn.cursor()

    # ⭐ Fetch saved songs for this user
    cursor.execute(
        "SELECT title, channel, videoId, thumbnail FROM saved_songs WHERE user_email=?",
        (user["email"],)
    )
    saved_rows = cursor.fetchall()

    # ❤️ Fetch liked songs for this user
    cursor.execute(
        "SELECT title, channel, videoId, thumbnail FROM liked_songs WHERE user_email=?",
        (user["email"],)
    )
    liked_rows = cursor.fetchall()

    conn.close()

    # Convert DB rows to dicts for the template
    saved = [{"title": r[0], "channel": r[1], "videoId": r[2], "thumbnail": r[3]} for r in saved_rows]
    liked = [{"title": r[0], "channel": r[1], "videoId": r[2], "thumbnail": r[3]} for r in liked_rows]

    return templates.TemplateResponse("library.html", {
        "request": request,
        "saved":   saved,
        "liked":   liked,
    })

# =============================================================
# 💾 SAVE SONG TO LIBRARY
# =============================================================

@app.post("/save-playlist")
async def save_playlist(request: Request):
    """Save a song to the user's saved_songs table."""
    user = request.session.get("user")

    if not user:
        return JSONResponse({"status": "error", "message": "Not logged in"}, status_code=401)

    data = await request.json()
    song = data.get("playlist")

    if not song:
        return JSONResponse({"status": "error", "message": "No song data provided"}, status_code=400)

    conn = sqlite3.connect("mooiz.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO saved_songs (user_email, title, channel, videoId, thumbnail) VALUES (?, ?, ?, ?, ?)",
        (user["email"], song.get("title"), song.get("channel"), song.get("videoId"), song.get("thumbnail"))
    )

    conn.commit()
    conn.close()

    return JSONResponse({"status": "success", "message": "Song saved!"})

# =============================================================
# ❤️ LIKE A SONG
# =============================================================

@app.post("/like-song")
async def like_song(request: Request):
    """Add a song to the user's liked_songs table."""
    user = request.session.get("user")

    if not user:
        return JSONResponse({"status": "error", "message": "Not logged in"}, status_code=401)

    data = await request.json()
    song = data.get("song")

    if not song:
        return JSONResponse({"status": "error", "message": "No song data provided"}, status_code=400)

    conn = sqlite3.connect("mooiz.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO liked_songs (user_email, title, channel, videoId, thumbnail) VALUES (?, ?, ?, ?, ?)",
        (user["email"], song.get("title"), song.get("channel"), song.get("videoId"), song.get("thumbnail"))
    )

    conn.commit()
    conn.close()

    return JSONResponse({"status": "success", "message": "Song liked!"})

# =============================================================
# 🎵 PLAYLIST GENERATOR
# Queries YouTube Data API v3 for videos matching the mood.
# Returns up to 16 results as JSON.
# =============================================================

@app.get("/playlist")
async def get_playlists(mood: str):
    """
    Fetch YouTube videos for a given mood/query string.
    Accepts any free-text mood, e.g. 'anime vibes', 'sad', 'workout'.
    """
    query = mood.strip() + " music playlist"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part":       "snippet",
                "q":          query,
                "type":       "video",
                "maxResults": 16,
                "key":        YOUTUBE_API_KEY
            }
        )

    data = response.json()

    songs = [
        {
            "title":     item["snippet"]["title"],
            "channel":   item["snippet"]["channelTitle"],
            "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
            "videoId":   item["id"]["videoId"]
        }
        for item in data.get("items", [])
    ]

    return {"playlist": songs}

# =============================================================
# 🎯 FOR YOU PAGE
# Recommends songs based on the title of the user's first
# liked song. Falls back to "popular music playlist" if the
# user hasn't liked anything yet.
# =============================================================

@app.get("/for-you")
async def for_you(request: Request):
    """Personalised recommendations page. Requires login."""
    user = request.session.get("user")

    if not user:
        return RedirectResponse(url="/login")

    conn = sqlite3.connect("mooiz.db")
    cursor = conn.cursor()

    # Grab the most recently liked song title to base recommendations on
    cursor.execute(
        "SELECT title FROM liked_songs WHERE user_email=? ORDER BY id DESC LIMIT 1",
        (user["email"],)
    )
    liked = cursor.fetchone()
    conn.close()

    # Build the YouTube search query
    if liked:
        query = liked[0] + " similar songs playlist"
    else:
        query = "popular music playlist"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part":       "snippet",
                "q":          query,
                "type":       "video",
                "maxResults": 16,
                "key":        YOUTUBE_API_KEY
            }
        )

    data = response.json()

    songs = [
        {
            "title":     item["snippet"]["title"],
            "channel":   item["snippet"]["channelTitle"],
            "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
            "videoId":   item["id"]["videoId"]
        }
        for item in data.get("items", [])
    ]

    return templates.TemplateResponse("for_you.html", {
        "request": request,
        "songs":   songs
    })

