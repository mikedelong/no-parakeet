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

    authorization = OAuthHandler(consumer_key=api_key, consumer_secret=api_secret_key, )
    interface = API(auth_handler=authorization, wait_on_rate_limit=True, )
    values = Cursor(interface.search, q=hash_tag, ).items(10)
    for value in values:
        logger.info(value)

    logger.info('total time: {:5.2f}s'.format(time() - time_start))
