import praw, os, re, requests, datetime
from bs4 import BeautifulSoup
from databaseManager import dbManager
from osManager import osManager
from config import ConfigFile
import moviepy.editor as mp

#subreddit: dankmemes, funny, memes,
#have another account that only posts with not caption and only a randomly selected tags
class RedditBot:
    def __init__(self, iusername):
        self.config_file = ConfigFile(iusername)
        self.reddit = praw.Reddit(client_id = self.config_file.get("Reddit", "client_id"),
                             client_secret = self.config_file.get("Reddit", "client_secret"),
                             password = self.config_file.get("Reddit", "password"),
                             user_agent = self.config_file.get("Reddit", "user_agent"),
                             username = self.config_file.get("Reddit", "username"))
        self.redditURL = 'www.reddit.com/r/'
        self.db = dbManager()
        self.osMan = osManager()
        self.videoDurationMax = int(self.config_file.get("Time", "videodurationmax"))

    def getImage(self, url, title):
        try:
            imgExtensions = [".jpg", ".png"]
            vidExtensions = [".mp4", ".gif", ".gifv"]
            doc = requests.get(url, stream=True)
            filename, file_extension = os.path.splitext(url)

            #Reddit gifs can be downloaded directly
            ##So no need for further parsing
            if re.search("redd[.]?it/.*.gif[v]?", url):
                return doc, file_extension
           
            x = re.compile("(\s?https?:)?(/{2})?")
            soup = BeautifulSoup(doc.text, 'html.parser')
            if re.search("v.redd[.]?it/.*", url):
                print(re.search('fallback_url', soup.prettify()))
                return doc, file_extension, True

            #If the image is a Imgur gif
            if file_extension.__contains__("gif"):
                #Imgur and reddit structure gifs differently in HTML, so
                ## The source is for Imgur
                for video in (soup.find_all('source')):
                    if video.has_attr('src'):
                        src = video['src']
                        filename, file_extension = os.path.splitext(src)
                        if file_extension not in vidExtensions:
                            return None, None
                        prefix = x.match(src)
                        if not prefix:
                            return requests.get("http://" + src, stream=True), file_extension
                        elif prefix.group(0) == "//":
                            return requests.get("http:" + src, stream=True), file_extension
                        else:
                            return requests.get(src, stream=True), file_extension
                return None, None       #This happens if it wasn't able to find the gif

            # If this url is already an image
            if file_extension in imgExtensions:
                return doc, file_extension

            # If not, then will need to extract the image from the URL
            for img in soup.find_all('img'):
                if img.has_attr('alt') and img['alt'] == title:             #There may nor be an alt
                    src = img['src']
                    filename, file_extension = os.path.splitext(src)
                    prefix = x.match(src)
                    if not prefix:
                        return requests.get("http://" + src, stream=True), file_extension
                    elif prefix.group(0) == "//":
                        return requests.get("http:" + src, stream=True), file_extension
                    else:
                        return requests.get(src, stream=True), file_extension

            return None,None
        except Exception as e:
            print("ERROR WHILE PARSING:  ", e)
            return None, None
    def download(self, submission, subreddit):
        pass #make this method call downloadVideo and downloadImage

    def downloadVideo(self, isGif, filepath, submission, subreddit):
        try:
            duration = submission.media['reddit_video']["duration"]
            if duration > self.videoDurationMax:
                return

            doc = requests.get(submission.media['reddit_video']['fallback_url'], stream=True)
            if not doc:
                raise Exception("COULDN'T RETRIEVE THE VIDEO")
 
            if not isGif:
                audioLocation = os.path.join(filepath, submission.title + "_audio")
                videoLocation = os.path.join(filepath, submission.title + "_video")
                audioPacket = requests.get(submission.url + "/audio", stream=True)
                if not audioPacket:
                    raise Exception("COULDN'T RETRIEVE THE AUDIO")

                self.writeFile(audioLocation, audioPacket)
                self.writeFile(videoLocation, doc)
                #audio = mp.AudioFileClip(audioLocation)
                video = mp.VideoFileClip(videoLocation)
                #video_with_audio = video.set_audio(audio)
                video_new_loc = videoLocation+".mp4"
                video.write_videofile(video_new_loc, audio=audioLocation)
                self.db.insert("Reddit", [submission.title, submission.url, video_new_loc, subreddit, "mp4"])
                self.osMan.deleteFile(audioLocation)
                self.osMan.deleteFile(videoLocation)
            else:
                imgLocation = os.path.join(filepath, submission.title)
                isWritten = self.writeFile(imgLocation, doc)
                if isWritten:
                    self.db.insert("Reddit", [submission.title, submission.url, imgLocation, subreddit, "gif"])


        except Exception as e:
            print("ERROR WHILE downloadVideo: ", e)
            return

    def downloadImage(self, submission, subreddit):                                          #Edit so it may only take in image
        try:
            url= submission.url #"https://v.redd.it/qahcxxgdvha11" 
            title = submission.title #https://v.redd.it/xglnc6dzlia11/HLSPlaylist.m3u8
            videoData = submission.media
            duplicateAmount = len(self.db.c.execute("SELECT URL FROM Reddit WHERE URL == '{0}'".format(str(url))).fetchall())

            if duplicateAmount >= 1:
                return False

            filepath = self.osMan.createDir(subreddit)                                  # Create the directory in which to store the (change this later so it wont be called in this function
            if isinstance( videoData, dict) and 'reddit_video' in videoData:
               self.downloadVideo(videoData['reddit_video']['is_gif'], filepath, submission, subreddit)
               return
            else:
                img, file_extension = self.getImage(url, title)
            
            if img == None or file_extension == None:
                return False
 
            imgLocation = os.path.join(filepath, title + file_extension)

            isWritten = self.writeFile(imgLocation, img)
            if isWritten:
                print(title + " URL: " + url)
                self.db.insert("Reddit", [title, url, imgLocation, subreddit, file_extension.split('.')[1]])
                
        except Exception as e:
            print("ERROR WHILE DOWNLOADING: ", e)
            return False

    def writeFile(self, toFile, content):
         try:
             with open(toFile, 'wb') as f:
                 for chunk in content.iter_content(chunk_size=1024):             #iter_content allows you to write the image by chunks
                    if chunk:
                        f.write(chunk)
             return True
         except Exception as e:
             print("ERROR WHILE writeFile: ", e)
             return False
    
    def scrapeImages(self, subreddit_id):
        try:
            print("DOWNLOADING IMAGES...")
            for submission in self.reddit.subreddit(subreddit_id).hot(limit=25):
                result = self.downloadImage(submission, subreddit_id)
        except Exception as e:
            print("ERROR WHILE REQUESTING: ", e)

#rbot = RedditBot("ravioliraviolirobot")
#rbot.db.createDatabase()
#rbot.scrapeImages("fortnitebr")
#rbot.downloadImage(None , "fortnitebr")
# src = 'https://i.redd.it/e3f4osg3uc511.gif'
# gif = requests.get(src, stream=True)
# with open("ayy.gifv", 'wb') as f:
#     for chunk in gif.iter_content(chunk_size=1024):             #iter_content allows you to write the image by chunks
#         if chunk`:
#             f.write(chunk)
