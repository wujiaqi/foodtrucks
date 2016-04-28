import httplib, urllib
import tweepy 
import sys
import time
import logging
import json
import logging
import logging.handlers
import re
import ConfigParser
import datetime
import pymongo
import os

from pymongo import MongoClient

config = ConfigParser.RawConfigParser()
config.read('foodtrucks.cfg')

#Twitter OAuth credentials
TW_CONSUMER_KEY =os.environ['TW_CONSUMER_KEY']
TW_CONSUMER_SECRET =os.environ['TW_CONSUMER_SECRET']
TW_ACCESS_TOKEN =os.environ['TW_ACCESS_TOKEN']
TW_ACCESS_TOKENSECRET =os.environ['TW_ACCESS_TOKENSECRET']

#access token for pusbbullet 
PUSHBULLET_TOKEN =os.environ['PUSHBULLET_TOKEN']

TWITTER_URL=config.get('twitter', 'TWITTER_URL')
PUSHBULLET_URL=config.get('pushbullet', 'PUSHBULLET_URL')

PB_BR3_TAG =config.get('pushbullet', 'PB_BR3_TAG')
#PB_BR3_TAG = "br3foodtrucks_dev"

FOODTRUCK_MAFIA_ID=config.get('twitter', 'FOODTRUCK_MAFIA_ID')
JERSEY_GIRL_ID=config.get('twitter', 'JERSEY_GIRL_ID')

BR3_REGEX=config.get('misc', 'BR3_REGEX')

LOG_FILENAME =config.get('misc', 'LOG_FILENAME')

DB_HOST = "localhost"
DB_HOST = config.get('mongodb', 'HOST')
DB_PORT = 27107
DB_PORT = config.getint('mongodb', 'PORT')

#logging.basicConfig(datefmt='%m-%d %H:%M')

_logger = logging.getLogger()
_logger.setLevel(logging.INFO)
logFormatter = logging.Formatter("%(asctime)s [%(threadName)s] [%(levelname)s]  %(message)s")

logging_handler = logging.handlers.RotatingFileHandler(LOG_FILENAME)
logging_handler.setFormatter(logFormatter)
_logger.addHandler(logging_handler)

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
_logger.addHandler(consoleHandler)

class StreamHandler(tweepy.StreamListener):

    def __init__(self, tw_api, history_collection):
        self.api = tw_api
        self.history_coll = history_collection


    def on_data(self, data):
        statusobj = json.loads(unicode(data))
        _logger.debug("tweet received: " + statusobj['text'])
        if re.search(BR3_REGEX, statusobj['text']) != None:
            br3_portion = re.search(r"@?BR#?3\s+(.*)", statusobj['text']).group(1)
            br3_mentions = re.findall(r"\@([a-zA-Z0-9_]+)", br3_portion)
            todays_date = datetime.datetime.now().replace(hour=0, minute=0, second=0)
            cursor = self.history_coll.find({"timestamp": {"$gt": todays_date}}).sort("timestamp", pymongo.DESCENDING).limit(1)
            if cursor.count() > 0:
                doc = cursor.next()
                #exit out if no update on foodtrucks today
                if set(doc['trucks']) == set(br3_mentions):
                    return
            push_message = ""
            if len(br3_mentions) == 0:
            	return
            for mention in br3_mentions:
                tw_user = self.api.get_user(mention)
                push_message += tw_user.name + "\n"
                if tw_user.url:
                    push_message += tw_user.url + "\n"
                else:
                    push_message += "https://twitter.com/" + mention + "\n"
            _logger.info("text matched, pushing to Pushbullet Channel:\n" + push_message)
            push_status = pushbullet_message(push_message, PB_BR3_TAG)
            if push_status == True:
                post = {
                    "timestamp": datetime.datetime.now(),
                    "trucks": br3_mentions
                }
                self.history_coll.insert(post)

    def on_error(self, status_code):
        _logger.error("Error status: " + str(status_code))
        if status_code == 420:
            _logger.error("Rate limit hit, sleeping for 1 hour before reconnect")
            time.sleep(3600)
            return True
        else:
            _logger.error("sleeping for 2 minutes before reconnect")
            time.sleep(120)
            return True
        

def pushbullet_message(message, channel_tag):
    conn = httplib.HTTPSConnection(PUSHBULLET_URL)
    headers = {"Content-Type": "application/x-www-form-urlencoded",
     "Authorization": "Bearer " + PUSHBULLET_TOKEN}
    params = {"channel_tag": channel_tag, "type": "note", "title": "Food Trucks at BR3 Today", "body": message}
    params = urllib.urlencode(params)
    conn.request("POST", "/v2/pushes", params, headers)
    response = conn.getresponse()
    success = False
    if(response.status == httplib.UNAUTHORIZED):
        _logger.error("Unauthorized Pushbullet request")
    elif(response.status != httplib.OK):
        _logger.error("Error occured while pushing to Pushbullet")
    else:
        _logger.info("Pushed successfully")
        success = True
    conn.close()
    return success


def initDBIndexing(history_coll):
    _logger.info("creating index")
    history_coll.create_index([('timestamp', pymongo.ASCENDING)])
    _logger.info("index created")


dbclient = None
for i in range(20):
    try:
        client = MongoClient(DB_HOST, DB_PORT, serverSelectionTimeoutMS=10000)
        client.server_info()
        dbclient = client
        break
    except pymongo.errors.ServerSelectionTimeoutError:
        _logger.warning("MongoDB not yet ready...retrying in 10 seconds")
if dbclient == None:
    _logger.error("MongoDB failed to start. Exiting")
    sys.exit()

history_coll = dbclient['foodtruckdb']['history']
auth = tweepy.OAuthHandler(TW_CONSUMER_KEY, TW_CONSUMER_SECRET)
auth.set_access_token(TW_ACCESS_TOKEN, TW_ACCESS_TOKENSECRET)
api = tweepy.API(auth)
initDBIndexing(history_coll)

while(True):
    try:
        _logger.info("streaming...")
        stream = tweepy.Stream(auth, StreamHandler(api, history_coll))
        stream.filter(follow=[FOODTRUCK_MAFIA_ID, JERSEY_GIRL_ID])
        #stream.filter(track=[sys.argv[1]])
    except KeyboardInterrupt:
        sys.exit()
    except Exception, e:
        logging.exception("error occured")
        time.sleep(2)
        _logger.info("starting again...")
    
