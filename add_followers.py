from json import dump
from json import dumps
from json import load
from logging import INFO
from logging import basicConfig
from logging import getLogger
from os.path import isfile

from arrow import now
from tweepy import API
from tweepy import Cursor
from tweepy import OAuthHandler
from tweepy import TweepyException

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
    output_file = '{}/{}'.format(settings['output_folder'], settings['output_file']).replace('//', '/')

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
    logger.info('order length: %d', len(order))
    order = [item for item in order if item[1] > 0]
    logger.info('order length: %d', len(order))
    order = [item for item in order if 4 < item[1] < 10]
    order = [item for item in order if 'follower_list' not in data[item[0]].keys()]
    logger.info('order length: %d', len(order))
    order = [item[0] for item in order]

    for index, id_ in enumerate(order):
        # todo refactor this to use a comprehension (?)
        followers = []
        try:
            for page in Cursor(api.get_follower_ids, user_id=id_).pages():
                followers.extend(page)
                logger.info('%d follower count: %s %s', index, id_, len(followers))
        except TweepyException as tweepy_exception:
            logger.warning(tweepy_exception)
            continue
        data[id_]['follower_list'] = [str(follower) for follower in followers]
        data['retrieved_date']: now().isoformat()

        logger.info('%s %s', id_, data[id_]['follower_list'])
        if index % 10 == 0:
            # checkpoint our updated data
            string_version = dumps(obj=data, sort_keys=True, indent=4)
            logger.info('writing update to %s', output_file)
            with open(file=output_file, mode='w') as output_fp:
                dump(obj=data, fp=output_fp, sort_keys=True, indent=4)

    # do the final write
    string_version = dumps(obj=data, sort_keys=True, indent=4)
    logger.info('writing final update to %s', output_file)
    with open(file=output_file, mode='w') as output_fp:
        dump(obj=data, fp=output_fp, sort_keys=True, indent=4)

    logger.info('total time: {:5.2f}s'.format((now() - time_start).total_seconds()))
