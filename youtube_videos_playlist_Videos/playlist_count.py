from googleapiclient.discovery import build

API_KEY = "YOUR_API_KEY"
CHANNEL_ID = "CHANNEL_ID_HERE"

youtube = build("youtube", "v3", developerKey=API_KEY)

# 1. Get total uploads playlist (default YouTube creates one)
uploads_playlist = youtube.channels().list(
    part="contentDetails",
    id=CHANNEL_ID
).execute()

uploads_playlist_id = uploads_playlist["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

# 2. Get all videos in uploads (total channel videos)
def get_videos_from_playlist(playlist_id):
    videos = []
    request = youtube.playlistItems().list(
        part="contentDetails",
        playlistId=playlist_id,
        maxResults=50
    )
    while request:
        response = request.execute()
        for item in response["items"]:
            videos.append(item["contentDetails"]["videoId"])
        request = youtube.playlistItems().list_next(request, response)
    return videos

all_videos = get_videos_from_playlist(uploads_playlist_id)
print("Total uploaded videos:", len(all_videos))

# 3. Get all playlists in the channel
playlists = []
request = youtube.playlists().list(
    part="id,snippet",
    channelId=CHANNEL_ID,
    maxResults=50
).execute()

for item in request["items"]:
    playlists.append(item["id"])

# 4. Get all videos in playlists
playlist_videos = set()
for pl_id in playlists:
    vids = get_videos_from_playlist(pl_id)
    playlist_videos.update(vids)

print("Videos in playlists:", len(playlist_videos))
print("Videos NOT in any playlist:", len(all_videos) - len(playlist_videos))
