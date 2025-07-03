import yt_dlp
import discord
import asyncio

class YTDLSource(discord.PCMVolumeTransformer):
    ytdl_format_options = {
        'format': 'bestaudio/best',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
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
        'options': '-vn -nostdin -extension_picky 0',
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
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return self(discord.FFmpegPCMAudio(filename, **self.ffmpeg_options), data=data)

    @classmethod
    async def get_url_info(self, url, noplaylist=True):
        loop = asyncio.get_event_loop()
        self.ytdl_format_options["noplaylist"] = noplaylist
        ytdl = yt_dlp.YoutubeDL(self.ytdl_format_options)

        try:
            info = await loop.run_in_executor(
                None, lambda: ytdl.extract_info(url, download=False)
            )

        except yt_dlp.utils.DownloadError:
            print(yt_dlp.utils.DownloadError)

        return info