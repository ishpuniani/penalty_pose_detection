from pytube import YouTube

SAVE_PATH = 'resources/videos/'

if __name__ == '__main__':
    links = [
        'https://www.youtube.com/watch?v=cYUl2dp9bOQ', # Eng vs Italy
        'https://www.youtube.com/watch?v=IgwsdBR_N1w&t=4s', # Portugal vs Spain
        'https://www.youtube.com/watch?v=3EiE7eLWI_M', # Old Eng vs Germany
        'https://www.youtube.com/watch?v=CBRE46C0tnM' # Fifa penalties over the years
        ]

    i = 1
    for link in links:
        yt = YouTube(link)
        print('Downloading : ' + yt.title)
        stream = yt.streams.get_highest_resolution()
        stream.download(SAVE_PATH, filename='video' + str(i))
        i+=1

    print('Videos downloaded!')