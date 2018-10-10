import random, asyncio, datetime
from databaseManager import dbManager
from instagrambot import InstagramBot
from redditbot import RedditBot
from osManager import osManager
from config import ConfigFile
import os #Delete this when you remove the check for FileFormat

class Bot:
    def __init__(self, account):          #Account and password are instagram account and password
        self.config_file = ConfigFile(account)
        self.sub_list = self.config_file.get("Reddit", "Subreddits")
        self.account = account
        self.ibot =  InstagramBot(account)
        self.rbot = RedditBot(account)
        self.obot = osManager(int(self.config_file.get("Time", "imagelifetime")))
        self.db = dbManager()
        self.numPosts = int(self.ibot.getNumberOfPosts())
        #Make this self and remove all of the member variables and instead call the dicionary when needed
        times = self.config_file.get("Time")
        for k,v in times.items():
            times[k] = int(v)

        self.scrape_time = times["scrapetime"]
        self.upload_time_MAX = times["uploadtimemax"]
        self.upload_time_MIN = times["uploadtimemin"]
        self.expire_time = times["expiretime"]
        self.retry_upload_delay = times["retryuploaddelay"]
        #Keep this however when deleting for convenience
        self.slow_hours_start = datetime.time(times["slowhourstart"], 0, 0)
        self.slow_hours_end = datetime.time(times["slowhourend"], 0, 0)
        self.slow_hours_delay = times["slowhourdelay"]
        self.follow_time_MAX = times["followtimemax"]
        self.follow_time_MIN = times["followtimemin"]
        self.like_time_MAX = times["liketimemax"]
        self.like_time_MIN = times["liketimemin"]

    def start(self):
        self.db.createDatabase()
        loop = asyncio.get_event_loop()
        loop.create_task(self.scrape())
        loop.create_task(self.upload())
        loop.create_task(self.expire())
        loop.create_task(self.follow())
        loop.create_task(self.like())
        loop.run_forever()
        loop.close()

    def getPost(self):
        try:
            temp_sub_list = list(self.sub_list)
            while temp_sub_list:
                try:
                    sub = temp_sub_list[random.randint(0, len(temp_sub_list) - 1)]
                    pic = self.db.c.execute("SELECT DISTINCT Reddit.ID, Reddit.Title, Reddit.Path, Reddit.Subreddit, Reddit.FileFormat FROM Reddit WHERE Reddit.Subreddit == (?)  AND Reddit.Path is NOT NULL AND REDDIT.ID NOT IN (SELECT redditID FROM POSTED) GROUP BY Reddit.Path HAVING COUNT(Reddit.Path) = 1",(sub,)).fetchall()
                    temp_sub_list.remove(sub)   #removing here
                    if pic:
                        picList = pic[random.randint(0, len(pic) - 1)]
                        pic_info = {
                            "ID" : picList[0],
                            "Title" : picList[1],
                            "Path" : picList[2],
                            "Subreddit" : picList[3],
                            "FileFormat" : picList[4]
                        }
                        #If the FileFormat value is null (will not need this in the future!)
                        if not pic_info['FileFormat']:
                            filename, file_extension = os.path.splitext(pic_info['Path'])
                            pic_info['FileFormat'] = file_extension.split('.')[1]
                        return pic_info
                except Exception as e:
                    print("ERROR DURING getPost while trying to get path to image: ", e)
            return None
        except Exception as e:
            print("ERROR DURING getPost: ", e)

    def getNumPosts(self):
        try:
            return self.ibot.getNumberOfPosts()
        except Exception as e:
            print("ERROR DURING getnumPosts: ", e)

    async def scrape(self):
        while True:
            try:
                for sub in self.sub_list:
                    self.rbot.scrapeImages(sub)
            except Exception as e:
                print("ERROR DURING scape in bot: ", e)
            finally:
                await asyncio.sleep(self.scrape_time)

    async def upload(self):
        while True:
            waitTime = random.randint(self.upload_time_MIN, self.upload_time_MAX)
            if self.isSlowHours():
                waitTime += self.slow_hours_delay
            try:
                succeed = self.ibot.upload(self.getPost())
                if not succeed:
                    waitTime = self.retry_upload_delay      #If it did not succeed only wait 5 more min to post again
            except Exception as e:
                print("ERROR DURING upload in bot: ", e)
                waitTime = self.retry_upload_delay
            finally:
                await asyncio.sleep(waitTime)

    async def expire(self):
        while True:
            try:
                self.obot.checkExpired()
            except Exception as e:
                print("ERROR DURING expire in bot: ", e)
            finally:
                await asyncio.sleep(self.expire_time)

    async def follow(self):
        while True:
            try:
                waitTime = random.randint(self.follow_time_MIN, self.follow_time_MAX)
                if self.isSlowHours():
                    waitTime += self.slow_hours_delay
                await self.ibot.followRandom()
                await self.ibot.unfollow()
            except Exception as e:
                print("ERROR DURING expire in bot: ", e)
            finally:
                await asyncio.sleep(waitTime)

    async def like(self):
        while True:
            try:
                waitTime = random.randint(self.follow_time_MIN, self.follow_time_MAX)
                if self.isSlowHours():
                    waitTime += self.slow_hours_delay
                await self.ibot.likeTimelineRandom()
            except Exception as e:
                print("ERROR DURING expire in bot: ", e)
            finally:
                await asyncio.sleep(waitTime)


    def isSlowHours(self):
        currentTime = datetime.datetime.now().time()
        if self.slow_hours_start <= self.slow_hours_end:
            return self.slow_hours_start <= currentTime <= self.slow_hours_end
        else:
            return self.slow_hours_start <= currentTime or currentTime <= self.slow_hours_end

#bot = Bot("ravioliraviolirobot")
# print(bot.upload_time_MIN)
# print(bot.upload_time_MAX)
# print(bot.expire_time)
# print(bot.retry_upload_delay)
# print(bot.scrape_time)
# print(bot.isSlowHours())
#print(bot.getPost())
