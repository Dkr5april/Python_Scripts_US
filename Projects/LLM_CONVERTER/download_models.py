import asyncio
from livekit.plugins import silero

async def download():
    print("Downloading Silero VAD models...")
    silero.VAD.load() # This command automatically triggers the download
    print("Download complete!")

if __name__ == "__main__":
    asyncio.run(download())