import configparser, json

#dankeraccount - edgymemes, surrealmemes
class ConfigFile:
    def __init__(self, username):
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.configfile = username + ".ini"
        self.config.read_file(open(self.configfile))

    def createConfig(self, iUsername, iPassword, rUsername, rPassword):
        self.config["Time"] = {
            "ScrapeTime" : "43200",
            "UploadTimeMax" : "3200",
            "UploadTimeMin" : "1800",
            "ExpireTime" : "86400",
            "ImageLifetime" : "4",
            "RetryUploadDelay" : "300",
            "slowhourstart" : "22",
            "slowhourend" :"6",
            "slowhourdelay" : "3200",
            "unfollowdays" : "5",
            "followtimemax" : "5000",
	        "followtimemin" : "3200",
            "liketimemax" : "5000",
            "liketimemin" : "1800",
            "videodurationmax" : "390"
        }
        self.config["Instagram"] = {
            "Username" : iUsername,
            "Password" : iPassword,
            "Titles" : "['rav', 'no']",
            "followamountmax" : "15",
            "followamountmin" : "10",
            "likeamountmax" : "20",
            "likeamountmin" : "10"
        }
        self.config["Reddit"] = {
            "Username" : rUsername,
            "Password" : rPassword,
            "client_id" : '',
            "client_secret" : '',
            "user_agent" : '',
            "Subreddits" : '["funny", "dankmemes", "memes"]'
        }
        self.config["Hashtags"] = {
            "funny" : '[lol, lmao, funny, meme, memes, bruh, wut, humor, hilarious, ravioli, ravioliravioligivemetheformuoli, follow, rofl, memesdaily]',
            "dankmemes" : '["lol", "lmao", "funny", "meme", "memes", "dank", "dankmemes", "fire", "spicy", "lit", "humor", "laugh"]'
        }
        self.save()
    def add(self, section, key, value):
        self.config[section][key] = str(value)
        self.save()

    def get(self, section, value = None):
        if value is None:
            result =  dict(self.config.items(section))
            for key,value in result.items():
                if "[" in value:
                    result[key] = json.loads(value)
            return result
        else:
            result = self.config.get(section, value)
            if "[" not in result:
                return result
            else:
                return json.loads(result)
    def save(self):
        with open(self.configfile, "w") as f:
            self.config.write(f)
