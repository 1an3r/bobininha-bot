import yt_dlp
import discord
import asyncio
import re


class YTDLSource(discord.PCMVolumeTransformer):
    ytdl_format_options = {
        'format': 'bestaudio/best',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'skip_download': False,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': False,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -nostdin -nodisp',
    }

    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(self, url, *, loop=None, stream=True, noplaylist=True):
        self.ytdl_format_options['noplaylist'] = noplaylist
        ytdl = yt_dlp.YoutubeDL(self.ytdl_format_options)
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return self(discord.FFmpegPCMAudio(filename, **self.ffmpeg_options), data=data)

    @classmethod
    def is_url(self, input_str: str) -> bool:
        return re.match(r'^https?://', input_str) is not None

    @classmethod
    async def extract_info_async(self, url):
        loop = asyncio.get_event_loop()
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'noplaylist': True,
        }

        def run():
            with yt_dlp.YoutubeDL(ydl_opts) as ytdl:
                return ytdl.extract_info(url, download=False)

        info = await loop.run_in_executor(None, run)
        return info

    @classmethod
    async def search_youtube(self, query: str, limit: int = 10):
        loop = asyncio.get_event_loop()
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'extract_flat': 'in_playlist',
            'format': 'bestaudio/best',
            'default_search': f'ytsearch{limit}',
        }

        def run():
            with yt_dlp.YoutubeDL(ydl_opts) as ytdl:
                return ytdl.extract_info(query, download=False)

        data = await loop.run_in_executor(None, run)
        return data.get('entries', []) if 'entries' in data else [data]
