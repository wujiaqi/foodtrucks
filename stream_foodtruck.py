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

config = ConfigParser.RawConfigParser()
config.read('foodtrucks.cfg')

#Twitter OAuth credentials
TW_CONSUMER_KEY =config.get('twitter', 'TW_CONSUMER_KEY')
TW_CONSUMER_SECRET =config.get('twitter', 'TW_CONSUMER_SECRET')
TW_ACCESS_TOKEN =config.get('twitter', 'TW_ACCESS_TOKEN')
TW_ACCESS_TOKENSECRET =config.get('twitter', 'TW_ACCESS_TOKENSECRET')

#access token for pusbbullet 
PUSHBULLET_TOKEN =config.get('pushbullet', 'PUSHBULLET_TOKEN')

TWITTER_URL=config.get('twitter', 'TWITTER_URL')
PUSHBULLET_URL=config.get('pushbullet', 'PUSHBULLET_URL')

PB_BR3_TAG =config.get('pushbullet', 'PB_BR3_TAG')
#PB_BR3_TAG = "br3foodtrucks_dev"

FOODTRUCK_MAFIA_ID=config.get('twitter', 'FOODTRUCK_MAFIA_ID')
JERSEY_GIRL_ID=config.get('twitter', 'JERSEY_GIRL_ID')

BR3_REGEX=config.get('misc', 'BR3_REGEX')

LOG_FILENAME =config.get('misc', 'LOG_FILENAME')

#logging.basicConfig(datefmt='%m-%d %H:%M')

_logger = logging.getLogger('FoodtruckStreamLogger')
_logger.setLevel(logging.DEBUG)

logging_handler = logging.handlers.RotatingFileHandler(LOG_FILENAME)

_logger.addHandler(logging_handler)

auth = tweepy.OAuthHandler(TW_CONSUMER_KEY, TW_CONSUMER_SECRET)
auth.set_access_token(TW_ACCESS_TOKEN, TW_ACCESS_TOKENSECRET)
api = tweepy.API(auth)

class StreamHandler(tweepy.StreamListener):

	def on_data(self, data):
		statusobj = json.loads(unicode(data))
		_logger.debug("tweet received: " + statusobj['text'])
		if re.search(BR3_REGEX, statusobj['text']) != None:
			br3_portion = re.search(r"@?BR#?3\s+(.*)", statusobj['text']).group(1)
			br3_mentions = re.findall(r"\@([a-zA-Z0-9_]+)", br3_portion)
			push_message = ""
			for mention in br3_mentions:
		        tw_user = api.get_user(mention)
		        push_message += tw_user.name + "\n"
		        if tw_user.url:
		            push_message += tw_user.url + "\n"
		        else:
		            push_message += "https://twitter.com/" + mention + "\n"

			_logger.debug("text matched, pushing to Pushbullet Channel")
			pushbullet_message(push_message, PB_BR3_TAG)

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
	if(response.status == httplib.UNAUTHORIZED):
		sys.exit("Unauthorized")
	elif(response.status != httplib.OK):
		sys.exit("Something else went wrong when pushing")
	conn.close()


while(True):

	try:
		_logger.info("streaming...")
		stream = tweepy.Stream(auth, StreamHandler())
		stream.filter(follow=[FOODTRUCK_MAFIA_ID, JERSEY_GIRL_ID])
		#stream.filter(track=[sys.argv[1]])
	except KeyboardInterrupt:
		sys.exit()
	except Exception, e:
		logging.exception("error occured")
		time.sleep(2)
		_logger.info("starting again...")
	
