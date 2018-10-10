from InstagramAPI import InstagramAPI
from databaseManager import dbManager
import random as r
from config import ConfigFile
import re, asyncio, time
from moviepy.video.io.VideoFileClip import VideoFileClip

class InstagramBot:
    def __init__(self, account):
        self.config_file = ConfigFile(account)
        self.account = account.strip()
        self.password = self.config_file.get("Instagram", "password").strip()
        self.db = dbManager()
        self.hashtags = self.config_file.get("Hashtags")
        self.titles = self.config_file.get("Instagram", "Titles")
        self.follow_amount_min = int(self.config_file.get("Instagram", "followamountmin"))
        self.follow_amount_max = int(self.config_file.get("Instagram", "followamountmax"))
        self.unfollow_days = int(self.config_file.get("Time", "unfollowdays"))
        self.like_ammount_max = int(self.config_file.get("Instagram", "likeamountmax"))
        self.like_ammount_min = int(self.config_file.get("Instagram", "likeamountmin"))
        print("Created Instagram Bot!")

    def upload(self, pic_info):
        try:
            api = InstagramAPI(self.account, self.password)
            if (api.login()):
                startCount = len(api.getTotalSelfUserFeed(self.account))
                photo_path = pic_info['Path']
                caption = self.genCaption(pic_info["Title"], pic_info["Subreddit"])
                if caption is None:
                    caption = self.titles[r.randint(0, len(self.titles) - 1 )] + "#lol #lmao #funny #rofl #meme #error #404 #human #notabot"

                if pic_info['FileFormat'] not in ['jpg', 'png']:
                    clip = VideoFileClip(photo_path)
                    clip.save_frame("images/thumbnail.jpg")
                    api.uploadVideo(photo_path,"images/thumbnail.jpg", caption=caption)
                    statusCode = api.LastResponse.status_code
                    if statusCode == 500:
                        print("Retrying to upload video in 10s")
                        time.sleep(10)
                        api.uploadVideo(photo_path,"images/thumbnail.jpg", caption=caption)
                else:
                    api.uploadPhoto(photo=photo_path, caption=caption)

                if len(api.getTotalSelfUserFeed(self.account)) - startCount >= 1:
                    iID = self.db.insert("Instagram", [caption, self.account])
                    self.db.insert("Posted", [pic_info["ID"], iID])
                    print("Uploaded Post!")
                    return True
                else:
                    print("Didn't upload post :(")
                    self.db.update("Reddit", {"Path": "null"}, "Reddit.ID == {0}".format(pic_info["ID"]))
                    return False
            else:
                print("Can't login!")
                return False
        except Exception as e:
            print("ERROR WHILE UPLOADING: ", e)
            self.db.update("Reddit", {"Path": "null"}, "Reddit.ID == {0}".format(pic_info["ID"]))
            return False

    def genCaption(self, title, subreddit):
        try:
            tagList = list(self.hashtags[subreddit])
            capList = []
            for i in range(0, min(r.randint(7,12), len(self.hashtags[subreddit]))):
                tag = tagList[r.randint(0, len(tagList) - 1)]
                capList.append(tag)
                tagList.remove(tag)

            pronouns = ["i", "me", "my", "our", "ours", "myself", "ourself", "we", "us", "i'm", "reddit", "sub", "karma", "upvote"]
            wordList = title.lower().split()
            ran = r.randint(0,9)

            if any(word in pronouns for word in wordList):
                return self.titles[r.randint(0, len(self.titles) - 1 )] + " #"+ " #".join(capList)
            if ran in range(0,9):
                return title + " #"+ " #".join(capList)
            else:
                return self.titles[r.randint(0, len(self.titles) - 1 )] + " #"+ " #".join(capList)
        except Exception as e:
            print("ERROR DURING genCaption: ", e)

    def getNumberOfPosts(self):
        try:
            api = InstagramAPI(self.account, self.password)
            if (api.login()):
                return len(api.getTotalSelfUserFeed())
            else:
                return 0
                print("ERROR COULDN'T DETERMINE NUMBER OF POSTS")
        except Exception as e:
            return 0
            print("ERROR DURING getNumberOfPosts: ", e)

    def getUsernameID(self, username, api):
        try:
            api.searchUsername(username)  # the InstagramUserID you want to know the followers
            usernameJson = api.LastJson
            return re.search("(?<=pk\'\: )[0-9]*", str(usernameJson)).group() # finds the pk numeral cod
        except Exception as e:
            print("ERROR DURING getUsernameID: ", e)

    def getFollowers(self, api, username = None):
        try:
            if username is None:
                username = self.account
            pkString = self.getUsernameID(username, api)
            api.getUserFollowers(int(pkString))
            followers = api.LastJson
            #followersNamesList = re.findall("(?<=username\'\: \').*?(?=\',)", str(followers)) # finds the UserID of the followers and creates a list
            #followersPksList = re.findall("(?<=pk\'\: )[0-9]*", str(followers)) # finds the UserID of the followers and creates a list
            return followers['users']
        except Exception as e:
            print("ERROR DURING getFollowers: ", e)

    def getHashtagFeed(self, hashtag):
        try:
            api = InstagramAPI(self.account, self.password)
            if (api.login()):
                api.getHashtagFeed(hashtag)
                tagJson = api.LastJson
                mediaIdList = re.findall("(?<=\'id\'\: \')[0-9]*_[0-9]*(?=\')", str(tagJson))
                return mediaIdList
        except Exception as e:
            print("ERROR DURING getHashtagFeed: ", e)

    def getMediaLikers(self, mediaId, api):
        try:
            api.getMediaLikers(mediaId)
            likerJson = api.LastJson
            return re.findall("(?<=pk\'\: )[0-9]*", str(likerJson))
        except Exception as e:
            print("ERROR DURING getMediaLikers: ", e)

    # Will choose a random hashtag for list of hashtags
    ## Get the feed of that hashtag and pick a picture
    ## Like the picture, then follow random people who have also
    ## liked the picture
    async def followRandom(self):
        try:
            api = InstagramAPI(self.account, self.password)
            if(api.login()):
                amountToFollow = r.randint(self.follow_amount_min, self.follow_amount_max)
                hashValues = list(self.hashtags.values())
                hashList = r.choice(hashValues)
                hashtag = r.choice(hashList)
                mediaList = self.getHashtagFeed(hashtag)
                amountFollowed = 0
                while mediaList and amountFollowed < amountToFollow:
                    mediaId = mediaList.pop(r.randint(0, len(mediaList) - 1))
                    api.like(mediaId)
                    self.db.insert("Like", [self.account, mediaId])
                    likersList = self.getMediaLikers(mediaId, api)
                    if not likersList:
                        continue
                    r.shuffle(likersList)
                    for i in range(0, min(amountToFollow - amountFollowed, len(likersList))):
                        print("trying to follow")
                        try:
                            user_pk = likersList[i]
                            followers = self.db.c.execute("SELECT PK from FOLLOWING").fetchall()
                            if user_pk not in followers:
                                api.follow(user_pk)
                                self.db.insert("Following", [self.account, user_pk])
                        except Exception as e:
                            print("ERRROR DURING followRandom while trying to follow")
                        finally:
                            await asyncio.sleep(r.randint(5,120))
                            amountFollowed += 1
        except Exception as e:
            print("ERROR DURING followRandom: ", e)

    async def unfollow(self):
        try:
            api = InstagramAPI(self.account, self.password)
            if api.login():
                amountToUnfollow = r.randint(self.follow_amount_min, self.follow_amount_max)
                expiredSelection = self.db.c.execute("SELECT PK From Following WHERE DateFollowed IS NOT NULL AND julianday('now') - julianday(DateFollowed) >= " + str(self.unfollow_days))
                expiredList = expiredSelection.fetchall()
                amountUnfollowed = 0
                for pk in expiredList:
                    print("trying to unfollow")
                    api.unfollow(pk[0])
                    self.db.update("Following", {"DateFollowed" : "null"}, "PK = {0}".format(pk[0]))
                    await asyncio.sleep(r.randint(5,120))
                    amountUnfollowed += 1
                    if amountUnfollowed >= amountToUnfollow:
                        return
        except Exception as e:
            print("ERROR DURING unfollow: ", e)

    async def likeTimelineRandom(self):
        try:
            api = InstagramAPI(self.account, self.password)
            if api.login():
                if not api.getTimeline():
                    raise Exception("Couldn't get timeline!")
                amountToLike = r.randint(self.like_ammount_min, self.like_ammount_max)
                amountLiked = 0
                mediaList = re.findall("(?<=\'id\'\: \')[0-9]*_[0-9]*(?=\')", str(api.LastJson))
                liked = self.db.c.execute("SELECT MediaID from Like").fetchall()
                while mediaList and amountLiked < amountToLike:
                    mediaId = mediaList.pop(r.randint(0, len(mediaList) - 1))
                    if mediaId not in liked:
                        print("trying to like") #Still need to do check
                        api.like(mediaId)
                        amountLiked += 1
                        self.db.insert("Like", [self.account, mediaId])
                        await asyncio.sleep(r.randint(3,40)) #You should have a like wait time min/max
        except Exception as e:
            print("ERROR DURING likeRandom: ", e)

    def directMessage(self):
        try:
            api = InstagramAPI(self.account, self.password)
            if api.login():
                followersInfo = self.getFollowers(api)
                followingPks = self.db.c.execute("SELECT PK FROM Following").fetchall()
                followingPks = [pk[0] for pk in followingPks]
                print(type(followingPks[0]))
                #Get all pks that are in followingPks but not in followersPks
                ## i.e., Get all people you are following but are not following you
                nonFollowersPks = [pk for pk in followingPks if pk not in followersInfo]
           #     api.direct_message("hey whats up", 'ravioliraviolirobot')
        except Exception as e:
            print("ERROR DURING directMessage",e)

#ibot = InstagramBot("ecstaticgames")
# for i in range(0,10):
#     print(ibot.genCaption("This is a random caption", "memes"))
#ibot.directMessage()
