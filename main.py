from collections import Counter
from datetime import datetime
from datetime import timedelta
from json import load
from logging import INFO
from logging import basicConfig
from logging import getLogger
from time import time

from tweepy import API
from tweepy import Cursor
from tweepy import OAuthHandler

# https://blog.f-secure.com/how-to-get-tweets-from-a-twitter-account-using-python-and-tweepy/
if __name__ == '__main__':
    time_start = time()
    logger = getLogger(__name__)
    basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=INFO, )
    logger.info('started.', )
    with open(file='./settings.json', mode='r', ) as settings_fp:
        settings = load(fp=settings_fp, )
    logger.info('settings: {}'.format(settings))
    api_key = settings['api_key']
    logger.info('API key: {}'.format(api_key, ), )
    api_secret_key = settings['api_secret_key']
    logger.info('secret key: {}'.format(api_secret_key, ), )
    hash_tag = settings['hash_tag']
    user = settings['user']

    authorization = OAuthHandler(consumer_key=api_key, consumer_secret=api_secret_key, )
    interface = API(auth_handler=authorization, wait_on_rate_limit=True, )

    # get some tweets using a hash tag
    do_hash_tag = False
    if do_hash_tag:
        values = Cursor(interface.search, q=hash_tag, ).items(10)
        for value in values:
            logger.info(value)

    do_user = True
    if do_user:
        value = API(auth_handler=authorization, ).get_user(user)
        logger.info("name: " + value.name)
        logger.info("screen_name: " + value.screen_name)
        logger.info("description: " + value.description)
        logger.info("statuses_count: " + str(value.statuses_count))
        logger.info("friends_count: " + str(value.friends_count))
        logger.info("followers_count: " + str(value.followers_count))

        # now get some tweets from this user and list hash tags
        hashtags = []
        mentions = []
        tweet_count = 0
        end_date = datetime.now() - timedelta(days=30)
        for status in Cursor(interface.user_timeline, id=user).items():
            if status.created_at > end_date:
                tweet_count += 1
                if hasattr(status, 'entities'):
                    entities = dict(status.entities)
                    if 'hashtags' in entities:
                        for entity in entities['hashtags']:
                            if entity is not None:
                                if 'text' in entity:
                                    hashtag = entity['text']
                                    if hashtag is not None:
                                        hashtags.append(hashtag)
                    if 'user_mentions' in entities:
                        for entity in entities['user_mentions']:
                            if entity is not None:
                                if 'screen_name' in entity:
                                    name = entity['screen_name']
                                    if name is not None:
                                        mentions.append(name)
        logger.info('hashtags: {}'.format(hashtags, ), )
        logger.info('most common hashtags: {}'.format(Counter(hashtags).most_common(5, ), ), )
        logger.info('mentions: {}'.format(mentions, ), )
        logger.info('most common mentions: {}'.format(Counter(mentions).most_common(5, ), ), )

    logger.info('total time: {:5.2f}s'.format(time() - time_start))
