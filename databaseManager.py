import sqlite3, datetime


class dbManager:
    def __init__(self):
        self.conn = sqlite3.connect('site.db')
        self.c =  self.conn.cursor()
    def createDatabase(self):
        try:
            self.c.execute(("CREATE TABLE IF NOT EXISTS Reddit (ID int, Title varchar(255), URL varchar(255),Path varchar(255), Subreddit varchar(255),FileFormat varchar(255), DateExtracted date, PRIMARY KEY(ID))"))
            self.c.execute("CREATE TABLE IF NOT EXISTS Instagram (ID int, Caption varchar(255), Account varchar(255), DatePosted date, PRIMARY KEY(ID) )")
            self.c.execute("CREATE TABLE IF NOT EXISTS Posted (ID int, redditID int, instagramID int, DatePosted date, FOREIGN KEY (redditID) REFERENCES Reddit(ID), FOREIGN KEY (instagramID  ) REFERENCES Instagram(ID))")
            self.c.execute("CREATE TABLE IF NOT EXISTS Directory (ID int, Path varchar(255), DateCreated date, PRIMARY KEY(ID))")
            self.c.execute("CREATE TABLE IF NOT EXISTS Following (ID int, Account varchar(255), PK int, DateFollowed date, PRIMARY KEY(ID))")
            self.c.execute("CREATE TABLE IF NOT EXISTS Like (ID int, Account varchar(255), MediaID varchar(255), DateLiked date, PRIMARY KEY(ID))")
        except Exception as e:
            print("ERROR DURING createDatabase: ",e)

    def insert(self, table_name, values):
        try:
            # if type(values) != list:
            #     v = []
            #     temp = v.append(values)
            #     values = temp

            lastID = self.c.execute("SELECT ID FROM {0} ORDER BY ID DESC LIMIT 1".format(table_name)).fetchone()
            if lastID == None:
                lastID = 0
            else:
                lastID = lastID[0]
            curID = int((lastID) + 1)

            values.insert(0, str(curID))
            values.append(datetime.datetime.now().strftime("%Y-%m-%d"))
            values = ', '.join(('"' + str(val) + '"' for val in values))

            self.c.execute("INSERT INTO {0} VALUES({1});".format(table_name, values))
            self.conn.commit()

            return curID  #The id of what was inserted
        except Exception as e:
            print("ERROR DURING SQL INSERT: ", e)

    def update(self, table_name, dic, condition = None):
        try:
            dicStr = ", ".join(["=".join([str(key), str(val)]) for key, val in dic.items()])
            if not condition:
                self.c.execute("UPDATE {0} SET {1}".format(table_name, dicStr))
            else:
                self.c.execute("UPDATE {0} SET {1} WHERE {2}".format(table_name, dicStr, condition))
            self.conn.commit()
        except Exception as e:
            print("ERROR DURING SQL UDPATE: ", e)

    def delete(self, table_name, condition = None):
        try:
            if condition == None:
                self.c.execute("DELETE FROM {0}".format(table_name))
            else:
                self.c.execute("DELETE FROM {0} WHERE {1} ".format(table_name, condition))
            self.conn.commit()
        except Exception as e:
            print("ERROR DUING SQL DELETE: ", e)


    def updateID (self,table):
        num = self.c.execute("SELECT COUNT(*) FROM REDDIT WHERE ID IS NULL").fetchone()
        for i in range(0,int(num[0])):
            lastID = self.c.execute("SELECT ID FROM {0} ORDER BY ID DESC LIMIT 1".format(table)).fetchone()[0]
            self.c.execute("UPDATE {0} SET ID = {1} WHERE URL in (SELECT x.URL FROM {0} x WHERE x.ID is null ORDER BY x.ID DESC LIMIT 1)".format(table,int(lastID) +1))
            self.conn.commit()

    # def select(self,table_name, columns, condition = None ):
    #     try:
    #         cols = ','.join(map(str, columns))
    #         tables = ','.join(map(str, table_name))
    #         if condition == None:
    #             print("SELECT {0} FROM {1}".format(cols, tables))
    #         else:
    #             print("SELECT {0} FROM {1} WHERE {2}".format(cols, tables, condition))
    #     except Exception as e:
    #         print("ERROR DURING SQL SELECT: ", e)


#db.createDatabase()

