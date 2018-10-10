from instagrambot import InstagramBot
from redditbot import RedditBot
from osManager import osManager
from databaseManager import dbManager
from bot import Bot
import asyncio, sys

def main():
    name = sys.argv[1]
    bot = Bot(name)
    bot.start()

if __name__ == "__main__":
    main()
