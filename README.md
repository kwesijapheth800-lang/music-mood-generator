# 🎧 Mooiz — Music Mood Generator

> Find music for any mood, instantly.

Mooiz is a mood-based music discovery app built with **FastAPI** and the **YouTube Data API v3**. Search any vibe — *anime, late night, chill, workout* — and get a curated playlist in seconds. Sign in with Google to save songs, like tracks, and get personalised "For You" recommendations.

---

## ✨ Features

- 🔍 **Mood Search** — Type any mood or vibe and get instant YouTube playlist results
- 😊 **Quick Mood Buttons** — One-tap presets: Happy, Focus, Sad, Workout
- 💾 **Save to Library** — Save songs to your personal playlist (requires login)
- ❤️ **Like Songs** — Like tracks to train your For You feed
- 🎯 **For You** — Personalised recommendations based on your liked songs
- 🔐 **Google Login** — Secure OAuth 2.0 authentication
- 📱 **Mobile-first UI** — Responsive bottom navigation, works great on any screen
- 🔄 **Search Persistence** — Your last search stays when you switch tabs and come back

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| Frontend | HTML + Tailwind CSS |
| Auth | Google OAuth 2.0 (authlib) |
| Database | SQLite |
| Music Data | YouTube Data API v3 |
| Sessions | Starlette SessionMiddleware |

---

## 📁 Project Structure

```
music-mood-generator/
├── templates/
│   ├── index.html       # Home / search page
│   ├── library.html     # Saved & liked songs
│   ├── for_you.html     # Personalised recommendations
│   └── me.html          # Profile & settings
├── main.py              # FastAPI app + all routes
├── mooiz.db             # SQLite database (auto-created, git-ignored)
├── requirements.txt     # Python dependencies
├── .env                 # Secret keys (git-ignored)
└── .gitignore
```

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/kwesijapheth800-lang/music-mood-generator.git
cd music-mood-generator
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your `.env` file

Create a `.env` file in the root directory:

```env
YOUTUBE_API_KEY=your_youtube_api_key_here
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
SESSION_SECRET=any_random_long_string_here
```

> **Where to get these:**
> - YouTube API Key → [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → YouTube Data API v3
> - Google OAuth credentials → Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client IDs

### 5. Run the app

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Then open your browser and visit:

```
http://127.0.0.1:8000
```

---

## 🔐 Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use an existing one)
3. Enable the **YouTube Data API v3**
4. Go to **Credentials** → **Create OAuth 2.0 Client ID**
5. Set application type to **Web application**
6. Add this to **Authorised redirect URIs**:
   ```
   http://127.0.0.1:8000/auth
   ```
7. Copy the **Client ID** and **Client Secret** into your `.env`

---

## 📦 requirements.txt

Make sure your `requirements.txt` includes:

```
fastapi
uvicorn
httpx
python-dotenv
authlib
itsdangerous
jinja2
python-multipart
starlette
```

---

## 🗄️ Database

SQLite is used for lightweight local persistence. Two tables are created automatically on first run — no setup needed.

| Table | Purpose |
|-------|---------|
| `saved_songs` | Songs saved by the user to their library |
| `liked_songs` | Songs liked by the user (drives For You recommendations) |

The `mooiz.db` file is git-ignored and created fresh on each new install.

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

1. Fork the repo
2. Create your branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a pull request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

Built with ❤️ by Japheth
