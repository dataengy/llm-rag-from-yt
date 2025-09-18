"""YouTube audio downloader using yt-dlp."""

from pathlib import Path
from typing import Optional

import yt_dlp
from loguru import logger


class YouTubeDownloader:
    """Downloads YouTube audio content."""

    def __init__(self, output_dir: Path):
        """Initialize downloader with output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(self.output_dir / "%(title)s.%(ext)s"),
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
            "quiet": True,
            "no_warnings": True,
        }

    def download(self, url: str) -> Optional[dict[str, str]]:
        """Download audio from YouTube URL.

        Args:
            url: YouTube URL to download

        Returns:
            Dict with file info or None if failed
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get("title", "unknown")
                duration = info.get("duration", 0)

                ydl.download([url])

                downloaded_file = self.output_dir / f"{title}.mp3"
                if downloaded_file.exists():
                    logger.info(f"Downloaded: {title} ({duration}s)")
                    return {
                        "title": title,
                        "file_path": str(downloaded_file),
                        "duration": duration,
                        "url": url,
                    }

        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return None

    def download_multiple(self, urls: list[str]) -> dict[str, dict[str, str]]:
        """Download multiple YouTube URLs.

        Args:
            urls: List of YouTube URLs

        Returns:
            Dict mapping URL to download info
        """
        results = {}
        for url in urls:
            result = self.download(url)
            if result:
                results[url] = result
        return results
