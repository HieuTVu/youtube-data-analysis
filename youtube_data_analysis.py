from googleapiclient.discovery import build
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Enter your API Key with Youtube Data API v3
your_youtube_api_key = '...'

# Enter the channel IDs you want to parse
channel_ids = [
    'UCqECaJ8Gagnn7YCbPEzWH6g' # Taylor Swift
    , 'UC9CoOnJkIBMdeijd9qYoT_g' # Adriana Grande
    , 'UCsRM0YB_dabtEPGPTKo-gcw' # Adele
    , 'UCByOQJjav0CUDwxCk-jVNRQ' # Drake
    , 'UCy3zgWom-5AGypGX_FVTKpg' # Olivia Rodrigo
    , 'UC-J-KZfRV8c13fOCkhXdLiQ' # Dua Lipa
    , 'UC0C-w0YjGpqDXGB8IHb662A' # Ed Sheeran
    , 'UCxMAbVFmxKUVGAll0WVGpFw' # Cardi B
    , 'UCurpiDXSkcUbgdMwHNZkrCg' # Mariah Carey
    , 'UCAvCL8hyXjSUHKEGuUPr1BA' # Shawn Mendes
]

youtube_api_key = your_youtube_api_key
youtube = build('youtube', 'v3', developerKey=youtube_api_key)


def turn_int(x):
    """
    Turn a non-numeric data types into numeric one.
    """
    if not isinstance(x, int):
        try:
            x = int(x)
        except:
            print("Cannot turn {} into int-type".format(x))
    return x
    

def get_channel_stats(youtube, channel_id):
    """
    Get channel statistics
    """
    response = youtube.channels().list(
            part='snippet,contentDetails,statistics'
            , id=channel_id
        ).execute()
    channel_title = response['items'][0]['snippet']['title']
    view_count = turn_int(response['items'][0]['statistics']['viewCount'])
    subscriber_count = turn_int(response['items'][0]['statistics']['subscriberCount'])
    video_count = turn_int(response['items'][0]['statistics']['videoCount'])
    playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    data = {
        'channel_title': channel_title
        , 'view_count': view_count
        , 'subscriber_count': subscriber_count
        , 'video_count': video_count
        , 'playlist_id': playlist_id
    }
    return data


def visualize_channel_stats(data):
    """
    Visualize views, subscribers and the number of videos of the artists.
    Arg: data is a DataFrame.
    """
    for column in data.columns[1:4]:
        plt.figure()
        sns.set(rc={'figure.figsize': (15,5)})
        sns.barplot(x='channel_title', y=column, data=data).set_title(column.upper())


def get_video_stats(youtube, video_ids):
    """
    Get the likes, unlikes, comments and shares of a list of videos.
    Arg: 
        youtube: API object
        video_ids: a list of video ids
    Return:
        A list of videos' stats based on their ids. This function is called by get_playlist_stats().
    Note:
        Maximum for one call is 50 videos.
    """
    video_stats = []
    response = youtube.videos().list(
            part='snippet,contentDetails,statistics'
            , id=','.join(video_ids)
        ).execute()
    for video in response['items']:
        video_stats.append(
            {'Title': video['snippet']['title']
             , 'Published_date': datetime.strptime(video['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%S%f%z')
             , 'View': turn_int(video['statistics'].get('viewCount'))
             , 'Like': turn_int(video['statistics'].get('likeCount'))
             , 'Dislike': turn_int(video['statistics'].get('dislikeCount'))
             , 'Comment': turn_int(video['statistics'].get('commentCount'))}
        )
    return video_stats


def get_playlist_stats(youtube, playlist_id, video_num):
    """
    Arg:
        youtube: API object
        playlist_id: id of the playlist containing the videos
        video_num: the number of videos of the playlist
    Return:
        A list of the playlist's videos' stats
    """
    playlist_stats = []
    nextPageToken = None
    
    for i in range(0, video_num, 50):
        # Request each page in the playlist (each page contains 50 videos)
        response = youtube.playlistItems().list(
                part='snippet, contentDetails'
                , playlistId=playlist_id
                , maxResults=50 # this is the maximum videos retrieve in one run
                , pageToken=nextPageToken
            ).execute()
        nextPageToken = response.get('nextPageToken')
        
        # Get video ids of the page
        video_ids = []
        for video in response['items']:
            video_ids.append(video['contentDetails']['videoId'])
        
        # Get the stats for the videos in page
        playlist_stats.extend(get_video_stats(youtube, video_ids))
    
    return playlist_stats


def visualize_playlist_stats(artist_name, playlist):
    """
    Visulize the interactions of the artists' channels.
    Arg:
        artist_name is the name of the artist owning the playlist.
        playlist is the DataFrame containing the interaction of the each video.
    """
    ### Number of videos in 2021
    # Add new column to record only month and year
    playlist['Year_Month'] = playlist['Published_date'].dt.strftime('%Y-%m')
    num_song = playlist.groupby('Year_Month', as_index=False).size()
    num_song_2021 = num_song[num_song['Year_Month'] > '2021-00']
    plt.figure()
    sns.barplot(x='Year_Month', y='size', data=num_song_2021).set_title(("{}'s number of songs in 2021".format(artist_name)).upper())
    
    ### Top 10 videos have best number of views
    top_view = playlist.sort_values('View', ascending=False)
    plt.figure()
    sns.barplot(x='View', y='Title', data=top_view.head(10)).set_title(("{}'s top view".format(artist_name)).upper())


def main():
    artist_stats = []
    
    for channel_id in channel_ids:
        artist_stats.append(get_channel_stats(youtube, channel_id))
        
    data = pd.DataFrame(artist_stats)
    
    visualize_channel_stats(data)
    
    # Get the artist with the highest video_count
    max_num_video = data['video_count'].max()
    artist = data.loc[data['video_count'] == max_num_video]
    artist_name = artist['channel_title'].iloc[0]
    playlist_id = artist['playlist_id'].iloc[0]
    
    playlist = pd.DataFrame(get_playlist_stats(youtube, playlist_id, max_num_video))
    
    # Clean data
    playlist.isnull().any()
    playlist[playlist['Comment'].isnull()]
    playlist = playlist.dropna(axis=0)
    
    visualize_playlist_stats(artist_name, playlist)