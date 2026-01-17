# 📦 TG Storage Cluster

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=for-the-badge&logo=fastapi)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
![Developer](https://img.shields.io/badge/Developer-DraxonV1-orange?style=for-the-badge)

A lightweight, high-performance file storage API that transforms Telegram into an infinite, scalable backend. Designed for developers who need a reliable CDN-like service for media, documents, and private file hosting without the overhead of traditional storage providers.

---

## ✨ Key Features

- **🚀 Bot Cluster Technology**: Seamlessly rotate between multiple Telegram bots to bypass API rate limits and ensure high availability.
- **📈 Infinite Scalability**: Leverage Telegram's massive infrastructure to host files of virtually any size (up to 2GB per file).
- **🎥 Advanced Streaming**: Built-in support for `Range` headers, allowing for smooth video seeking, scrubbing, and real-time image previews in any browser.
- **🎨 Modern Web Dashboard**: A sleek, responsive built-in dashboard for effortless file management, uploads, and monitoring.
- **🔒 Robust Security**: Database-backed API key authentication with multi-key support for different applications or users.
- **🌐 Proxy Ready**: Native HTTP/SOCKS5 proxy support integrated at the core for restricted network environments.
- **📦 Fully Modular**: Clean source code designed to be imported as a Python module or run as a standalone service.

---

## 🚀 Detailed Setup Guide

### 1. Prerequisites
- **Python 3.10+**
- **Telegram API Credentials**: You need an `API_ID` and `API_HASH`.
- **Storage Channel**: A Telegram Channel (Private recommended) where the bots will "dump" the files.

### 2. Getting Your Credentials

#### Telegram API
1.  Log in to [my.telegram.org](https://my.telegram.org).
2.  Click on **API development tools**.
3.  Create a new application. Note down your `App api_id` and `App api_hash`.

#### Telegram Channel ID
1.  Open [Telegram Web](https://web.telegram.org/).
2.  Click on your target Channel.
3.  The URL will end with something like `-1003478619104`. That entire number (including the `-100`) is your `CHANNEL_ID`.

#### Bot Tokens
1.  Message [@BotFather](https://t.me/BotFather) on Telegram.
2.  Create one or more bots using `/newbot`.
3.  **IMPORTANT**: Add every bot you create to your Storage Channel as an **Administrator** with "Post Messages" permissions.

### 3. Installation
```bash
# Clone the repository
git clone https://github.com/DraxonV1/tgstorage.git
cd tgstorage

# Install dependencies
pip install -r tgstorage_src/requirements.txt
```

### 4. Configuration
1.  **Environment**: Rename `tgstorage_src/.env.example` to `tgstorage_src/.env`.
2.  **Edit `.env`**: Fill in your `API_ID`, `API_HASH`, and `CHANNEL_ID`.
3.  **Bots**: Create a file named `tgstorage_src/tokens.txt` and paste your bot tokens (one per line).

---

## 🛠️ Management & API

### Generate API Keys
To create a new key for your application:
```bash
cd tgstorage_src
python generate_key.py --owner "MyFirstApp"
```

### Running the Server
```bash
python main.py
```
- **Web Dashboard**: `http://localhost:8082/`
- **API Base**: `http://localhost:8082`

### API Endpoints
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/upload` | `POST` | Upload a file via multipart form-data. |
| `/files` | `GET` | List all indexed files (Paginated). |
| `/f/{id}/{name}` | `GET` | Direct raw stream (Perfect for `<img>` or `<video>`). |
| `/share/{token}` | `GET` | Direct proxy landing page for sharing. |
| `/stats` | `GET` | Retrieve cluster statistics. |

---

## 📦 Python Integration
Since `tgstorage_src` is a valid package, you can import it:
```python
from tgstorage_src.bot import cluster

async def test():
    bot = await cluster.get_healthy_bot()
    # Perform direct operations...
```

---
## Note:
This Project is in beta-state, expect bugs (minimal-state) and nginx conf syntax errors. it is recommended to use api endpoints only & not use nginx because we are not using dashboard 🥀

## 🤝 Contributing
Developed with ❤️ by **DraxonV1**. Contributions, issues, and feature requests are welcome!

## 📜 License
This project is licensed under the [MIT License](LICENSE).
