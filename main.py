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

TAG_KEY = 'hash''tags'


def get_user_data(arg):
    this = API(auth_handler=authorization, ).get_user(arg)
    return this.name, this.screen_name, this.description, this.statuses_count, this.friends_count, this.followers_count


def get_connections(arg, end_date):
    result_tags = []
    result_mentions = []
    for status in Cursor(interface.user_timeline, id=arg).items():
        if status.created_at > end_date:
            if hasattr(status, 'entities'):
                entities = dict(status.entities)
                if TAG_KEY in entities:
                    for entity in entities[TAG_KEY]:
                        if entity is not None:
                            if 'text' in entity:
                                hashtag = entity['text']
                                if hashtag is not None:
                                    result_tags.append(hashtag)
                if 'user_mentions' in entities:
                    for entity in entities['user_mentions']:
                        if entity is not None:
                            if 'screen_name' in entity:
                                local_name = entity['screen_name']
                                if local_name is not None:
                                    result_mentions.append(local_name)
    return result_tags, result_mentions


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
    days = settings['days'] if 'days' in settings.keys() else 15
    if 'days' in settings.keys():
        logger.info('look back is {} days'.format(days))
    else:
        logger.warning('parameter days is missing; using default value {}'.format(days))
    if 'functions' in settings.keys():
        functions = settings['functions']
        logger.info('functions: {}'.format(functions))
    else:
        functions = list()
        logger.warning('functions not specified in settings; no default function')
    hash_tag = settings['hash_tag']
    left = settings['left']
    right = settings['right']
    user = settings['user']

    authorization = OAuthHandler(consumer_key=api_key, consumer_secret=api_secret_key, )
    interface = API(auth_handler=authorization, wait_on_rate_limit=True, )

    # get some tweets using a hash tag
    if TAG_KEY in functions:
        values = Cursor(interface.search, q=hash_tag, ).items(10)
        for value in values:
            logger.info(value)

    if 'user' in functions:
        name, screen_name, description, statuses_count, friends_count, followers_count = get_user_data(user)
        logger.info('name: {} screen name: {}'.format(name, screen_name, ))
        logger.info('description: {}'.format(description, ))
        logger.info('statuses: {} friends: {} followers: {}'.format(statuses_count, friends_count, followers_count, ))

        # now get some tweets from this user and list hash tags
        tags, mentions = get_connections(user, datetime.now() - timedelta(days=days, ), )
        logger.info('{}: {}'.format(TAG_KEY, tags, ), )
        repeats = {key: count for key, count in Counter(tags).items() if count > 1}
        logger.info('most common {}: {}'.format(TAG_KEY, repeats, ), )
        logger.info('mentions: {}'.format(sorted(list(set(mentions), ), ), ), )
        mention_count = Counter(mentions)
        threshold = 0.005 * sum([value for value in dict(mention_count).values()])
        percentage_mentions = {key: count for key, count in dict(mention_count).items() if count >= threshold}
        logger.info('most common mentions: {}'.format(percentage_mentions, ), )

    if 'user_compare' in functions:
        logger.info('getting {} days of data for {}'.format(days, left))
        left_tags, left_mentions = get_connections(left, datetime.now() - timedelta(days=days), )
        logger.info('getting {} days of data for {}'.format(days, right))
        right_tags, right_mentions = get_connections(right, datetime.now() - timedelta(days=days), )
        common_mentions = [item for item in left_mentions if item in right_mentions]
        logger.info('common mentions: {}'.format(Counter(common_mentions)))

    logger.info('total time: {:5.2f}s'.format(time() - time_start))
