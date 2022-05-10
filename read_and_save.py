from json import load
from logging import INFO
from logging import basicConfig
from logging import getLogger

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
    with open(file='./read_and_save_settings.json', mode='r', ) as settings_fp:
        settings = load(fp=settings_fp, )
    logger.info('settings: {}'.format(settings))
    api_key = settings['api_key']
    logger.info('API key: {}'.format(api_key, ), )
    api_secret_key = settings['api_secret_key']
    logger.info('secret key: {}'.format(api_secret_key, ), )
    access_token = settings['access_token']
    access_token_secret = settings['access_token_secret']
    follower_count_cutoff = settings['follower_count_cutoff']

    authorization = OAuthHandler(consumer_key=api_key, consumer_secret=api_secret_key, access_token=access_token,
                                 access_token_secret=access_token_secret)
    api = API(auth=authorization, wait_on_rate_limit=True)

    me = api.get_user(screen_name=settings['screen_names'][settings['screen_name_index']])
    logger.info('ID: %d %s screen name: %s', me.id, me.id_str, me.name)
    data = dict()
    # add the root user to the data
    data[me.id] = {
        'id_str': me.id_str,
        'name': me.name,
        'follower count': me.followers_count,
        'screen name': me.screen_name,
        'retrieved_date': now()
    }
    user_list = [me.id_str]
    follower_list = []
    for user in user_list:
        # todo refactor this to use a comprehension (?)
        followers = []
        try:
            for page in Cursor(api.get_follower_ids, user_id=user).pages():
                followers.extend(page)
                logger.info('follower count: %s', len(followers))
        except TweepyException as tweepy_exception:
            logger.warning(tweepy_exception)
            continue
        follower_list.append(followers)
        for follower in followers:
            this = api.get_user(user_id=follower)
            data[follower] = {
                'id_str': this.id_str,
                'name': this.name,
                'follower count': this.followers_count,
                'screen name': this.screen_name,
                'retrieved_date': now()
            }

    logger.info('total time: {:5.2f}s'.format((now() - time_start).total_seconds()))
