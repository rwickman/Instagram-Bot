import os, shutil, datetime
from databaseManager import dbManager

class osManager:
    def __init__(self, daysTillExpire = 5):
        self.db = dbManager()
        self.expireDays = daysTillExpire

    def createDir(self, subreddit):
        try:
            now = datetime.datetime.now()
            filepath = "images/{0}/{1}/".format(subreddit, now.strftime("%m-%d-%Y"))
            filepathAbs = os.path.abspath(filepath)
            if not os.path.exists(filepathAbs):
                os.makedirs(filepathAbs)
                self.db.insert("Directory", [filepath])
        except Exception as e:
            print("ERROR DURING createDir: ", e)
        return filepath

    def deleteDirectory(self, path):
        try:
            shutil.rmtree(path)
        except Exception as e:
            print("ERROR DURING deleteDirectory: ", e)

    def deleteFile(self, fileLoc):
        try:
            os.remove(fileLoc)
        except Exception as e:
            print("ERROR DURING deleteFile: ", e)

    def checkExpired(self):
        try:
            expiredSelection = self.db.c.execute("SELECT Path From Directory WHERE julianday('now') - julianday(DateCreated) >= " + str(self.expireDays))
            expiredList = expiredSelection.fetchall()
            for dir in expiredList:
                try:
                    self.deleteDirectory(dir[0])
                except Exception as e:
                    print("ERROR DURING checkExpired while trying to delete directory: ", e)
            self.db.delete("Directory", "julianday('now') - julianday(DateCreated) >= " + str(self.expireDays))
            self.db.update("Reddit", {"Path" : "null"}, "julianday('now') - julianday(DateExtracted) >= {0} AND Path IS NOT NULL".format(self.expireDays))
        except Exception as e:
            print("ERROR DURING checkExpired: ", e)
