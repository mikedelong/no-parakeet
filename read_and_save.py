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
    with open(file='./read_and_save_settings.json', mode='r', ) as settings_fp:
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

    me = api.get_user(screen_name=settings['screen_names'][settings['screen_name_index']])
    logger.info('ID: %d %s screen name: %s', me.id, me.id_str, me.name)

    # add the root user to the data
    data[me.id_str] = {
        'id': me.id_str,
        'name': me.name,
        'follower count': me.followers_count,
        'screen name': me.screen_name,
        'retrieved_date': now().isoformat()
    }
    follower_list = []
    for user in [me.id_str]:
        # todo refactor this to use a comprehension (?)
        followers = []
        try:
            for page in Cursor(api.get_follower_ids, user_id=user).pages():
                followers.extend(page)
                logger.info('follower count: %s', len(followers))
        except TweepyException as tweepy_exception:
            logger.warning(tweepy_exception)
            continue
        follower_list.extend(followers)
        for index, follower in enumerate(followers):
            if str(follower) not in data.keys():
                logger.info('get_user for %d (%d) %d', follower, index, len(data))
                this = api.get_user(user_id=follower)
                data[str(follower)] = {
                    'id': this.id_str,
                    'name': this.name,
                    'follower count': this.followers_count,
                    'screen name': this.screen_name,
                    'retrieved_date': now().isoformat()
                }
            else:
                logger.info('skipping %d because it is already present', follower)
            if index % 100 == 0:
                data[user]['follower_list'] = [str(item) for item in follower_list]
                string_version = dumps(obj=data, sort_keys=True, indent=4)
                logger.info('writing size %d to %s', len(data), output_file)
                with open(file=output_file, mode='w') as output_fp:
                    dump(obj=data, fp=output_fp, sort_keys=True, indent=4)

        data[user]['follower_list'] = [str(item) for item in follower_list]

    string_version = dumps(obj=data, sort_keys=True, indent=4)
    with open(file=output_file, mode='w') as output_fp:
        dump(obj=data, fp=output_fp, sort_keys=True, indent=4)

    # todo under some conditions copy the output file back to the input file

    logger.info('total time: {:5.2f}s'.format((now() - time_start).total_seconds()))
