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


def get_user_data(arg):
    this = API(auth_handler=authorization, ).get_user(arg)
    return this.name, this.screen_name, this.description, this.statuses_count, this.friends_count, this.followers_count


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
        name, screen_name, description, statuses_count, friends_count, followers_count = get_user_data(user)
        logger.info('name: {} screen name: {}'.format(name, screen_name, ))
        logger.info('description: {}'.format(description, ))
        logger.info('statuses: {} friends: {} followers: {}'.format(statuses_count, friends_count, followers_count, ))

        # now get some tweets from this user and list hash tags
        tags = []
        mentions = []
        tweet_count = 0
        end_date = datetime.now() - timedelta(days=30)
        tag_key = 'hash''tags'
        for status in Cursor(interface.user_timeline, id=user).items():
            if status.created_at > end_date:
                tweet_count += 1
                if hasattr(status, 'entities'):
                    entities = dict(status.entities)
                    if tag_key in entities:
                        for entity in entities[tag_key]:
                            if entity is not None:
                                if 'text' in entity:
                                    hashtag = entity['text']
                                    if hashtag is not None:
                                        tags.append(hashtag)
                    if 'user_mentions' in entities:
                        for entity in entities['user_mentions']:
                            if entity is not None:
                                if 'screen_name' in entity:
                                    name = entity['screen_name']
                                    if name is not None:
                                        mentions.append(name)
        logger.info('{}: {}'.format(tag_key, tags, ), )
        repeats = {key: count for key, count in Counter(tags).items() if count > 1}
        logger.info('most common {}: {}'.format(tag_key, repeats, ), )
        logger.info('mentions: {}'.format(sorted(list(set(mentions), ), ), ), )
        mention_count = Counter(mentions)
        threshold = 0.005 * sum([value for value in dict(mention_count).values()])
        percentage_mentions = {key: count for key, count in dict(mention_count).items() if count >= threshold}
        logger.info('most common mentions: {}'.format(percentage_mentions, ), )

    logger.info('total time: {:5.2f}s'.format(time() - time_start))
