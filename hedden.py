from json import load
from logging import INFO
from logging import basicConfig
from logging import getLogger
from time import time

from networkx import from_pandas_edgelist
from networkx import spring_layout
from pandas import DataFrame
from tweepy import API
from tweepy import Cursor
from tweepy import OAuthHandler
from tweepy import TweepyException

from matplotlib.pyplot import style
from matplotlib.pyplot import subplots

from networkx import draw_networkx_edges
from networkx import draw_networkx_labels
from networkx import draw_networkx_nodes
from matplotlib.pyplot import savefig
from pandas import concat
from pandas import read_csv
from networkx import k_core
from community import community_louvain
from pandas import merge
from matplotlib.pyplot import cm

# https://towardsdatascience.com/how-to-download-and-visualize-your-twitter-network-f009dbbf107b

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
    access_token = settings['access_token']
    access_token_secret = settings['access_token_secret']

    authorization = OAuthHandler(consumer_key=api_key, consumer_secret=api_secret_key, access_token=access_token,
                                 access_token_secret=access_token_secret)
    api = API(auth=authorization, wait_on_rate_limit=True)

    screen_names = ['BathCounty', 'gohikevirginia', 'MyBristolVisit', 'SteveHedden']
    me = api.get_user(screen_name=screen_names[0])
    logger.info('ID: %d %s screen name: %s', me.id, me.id_str, me.name)
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

    df = DataFrame(columns=['source', 'target'])  # Empty DataFrame
    df['target'] = follower_list[0]  # Set the list of followers as the target column
    df['source'] = me.id

    f, ax = subplots(figsize=(10, 10))
    style.use('ggplot')
    G = from_pandas_edgelist(df, 'source', 'target')  # Turn df into graph
    pos = spring_layout(G)  # specify layout for visual
    nodes = draw_networkx_nodes(G, pos, alpha=0.8)
    nodes.set_edgecolor('k')
    draw_networkx_labels(G, pos, font_size=8)
    draw_networkx_edges(G, pos, width=1.0, alpha=0.2)

    savefig('./output/{}.png'.format(me.screen_name))

    for id_ in df['target'].to_list():
        logger.info('processing id: %s', id_)
        followers = []
        follower_list = []

        # fetch the user
        user = api.get_user(user_id=id_)

        # fetching the followers_count
        followers_count = user.followers_count

        try:
            for page in Cursor(api.get_follower_ids, user_id=id_).pages():
                followers.extend(page)
                logger.info('follower count: %s', len(followers))
                if followers_count >= 500:  # Only take first 5000 followers
                    break
        except TweepyException as tweepy_exception:
            logger.warning(tweepy_exception)
            continue
        follower_list.append(followers)
        # todo roll these up into a single call
        temp = DataFrame(columns=['source', 'target'])
        temp['target'] = follower_list[0]
        temp['source'] = id_
        df = concat([df, temp])
        output_file = './output/{}.csv'.format(me.screen_name)
        df.to_csv(path_or_buf=output_file)
        do_load = False
        if do_load:
            df = read_csv(filepath_or_buffer=output_file)
        G = from_pandas_edgelist(df=df, source='source', target='target', edge_key=None, create_using=None,
                                 edge_attr=None)
        logger.info('node count: %d', G.number_of_nodes())
        G_sorted = DataFrame(sorted(G.degree, key=lambda x: x[1], reverse=True))
        G_sorted.columns = ['nconst', 'degree']
        logger.info(G_sorted.head())
        G_tmp = k_core(G, 3)  # Exclude nodes with degree less than 10

        # todo roll these up
        # Turn partition into dataframe
        partition = DataFrame([community_louvain.best_partition(G_tmp)]).T
        partition = partition.reset_index()
        partition.columns = ['names', 'group']

        G_sorted = DataFrame(sorted(G_tmp.degree, key=lambda x: x[1], reverse=True), columns=['names', 'degree'])
        # G_sorted.columns =
        logger.info(G_sorted.head())
        dc = G_sorted
        combined = merge(dc, partition1, how='left', left_on='names', right_on='names')

        pos = spring_layout(G_tmp)
        f, ax = subplots(figsize=(10, 10))
        style.use('ggplot')
        nodes = draw_networkx_nodes(G_tmp, pos, cmap=cm.Set1, node_color=combined['group'], alpha=0.8)
        nodes.set_edgecolor('k')
        draw_networkx_labels(G_tmp, pos, font_size=8)
        draw_networkx_edges(G_tmp, pos, width=1.0, alpha=0.2)
        savefig('./output/{}-clustered.png'.format(me.screen_name))

    logger.info('total time: {:5.2f}s'.format(time() - time_start))
