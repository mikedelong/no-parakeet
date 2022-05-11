from json import load
from logging import INFO
from logging import basicConfig
from logging import getLogger
from os.path import isfile

from arrow import now
from tweepy import API
from tweepy import OAuthHandler

if __name__ == '__main__':
    time_start = now()
    logger = getLogger(__name__)
    basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=INFO, )
    logger.info('started.', )
    with open(file='./add_followers_settings.json', mode='r', ) as settings_fp:
        settings = load(fp=settings_fp, )
    logger.info('settings: {}'.format(settings))
    api_key = settings['api_key']
    logger.info('API key: {}'.format(api_key, ), )
    api_secret_key = settings['api_secret_key']
    logger.info('secret key: {}'.format(api_secret_key, ), )
    access_token = settings['access_token']
    access_token_secret = settings['access_token_secret']
    input_file = '{}/{}'.format(settings['input_folder'], settings['input_file']).replace('//', '/')

    if isfile(input_file):
        with open(file=input_file, mode='r') as input_fp:
            data = load(fp=input_fp)
        logger.info('loaded %d items from %s', len(data), input_file)
    else:
        data = dict()

    authorization = OAuthHandler(consumer_key=api_key, consumer_secret=api_secret_key, access_token=access_token,
                                 access_token_secret=access_token_secret)
    api = API(auth=authorization, wait_on_rate_limit=True)

    order = sorted([(item['id'], item['follower count']) for item in data.values()], key=lambda x: x[1])
    order = [item for item in order if item[1] > 0]


    logger.info('total time: {:5.2f}s'.format((now() - time_start).total_seconds()))
