from json import load
from logging import INFO
from logging import basicConfig
from logging import getLogger
from time import time

from tweepy import API
from tweepy import OAuthHandler

# https://docs.tweepy.org/en/stable/getting_started.html
if __name__ == '__main__':
    time_start = time()
    logger = getLogger(__name__)
    basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=INFO, )
    logger.info('started.', )
    with open(file='./main_settings.json', mode='r', ) as settings_fp:
        settings = load(fp=settings_fp, )
    logger.info('settings: {}'.format(settings))
    api_key = settings['api_key']
    logger.info('API key: {}'.format(api_key, ), )
    api_secret_key = settings['api_secret_key']
    logger.info('secret key: {}'.format(api_secret_key, ), )
    access_token = settings['access_token']
    access_token_secret = settings['access_token_secret']

    authorization = OAuthHandler(consumer_key=api_key, consumer_secret=api_secret_key, access_token=access_token,
                                 access_token_secret=access_token_secret)
    api = API(auth=authorization)
    timeline = api.home_timeline()
    for item in timeline:
        logger.info(item.text)

    user = api.get_user(screen_name=settings['user'])
    id_ = user.id
    users = api.get_user(id=id_)

    logger.info('total time: {:5.2f}s'.format(time() - time_start))
