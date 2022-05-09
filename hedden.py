from json import load
from logging import INFO
from logging import basicConfig
from logging import getLogger
from time import time

from community import community_louvain
from matplotlib.pyplot import cm
from matplotlib.pyplot import savefig
from matplotlib.pyplot import style
from matplotlib.pyplot import subplots
from networkx import draw_networkx_edges
from networkx import draw_networkx_labels
from networkx import draw_networkx_nodes
from networkx import from_pandas_edgelist
from networkx import k_core
from networkx import spring_layout
from pandas import DataFrame
from pandas import concat
from pandas import merge
from pandas import read_csv
from plotly.graph_objects import Figure
from plotly.graph_objects import Layout
from plotly.graph_objects import Scatter
from tweepy import API
from tweepy import Cursor
from tweepy import OAuthHandler
from tweepy import TweepyException

# https://towardsdatascience.com/how-to-download-and-visualize-your-twitter-network-f009dbbf107b

if __name__ == '__main__':
    time_start = time()
    logger = getLogger(__name__)
    basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=INFO, )
    logger.info('started.', )
    with open(file='./hedden_settings.json', mode='r', ) as settings_fp:
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

    screen_names = dict()

    for id_ in df['target'].to_list():
        logger.info('processing id: %s', id_)
        followers = []
        follower_list = []

        # fetch the user
        user = api.get_user(user_id=id_)
        screen_names[id_] = user.screen_name
        # fetching the followers_count
        followers_count = user.followers_count
        try:
            for page in Cursor(api.get_follower_ids, user_id=id_).pages():
                followers.extend(page)
                logger.info('follower count: %s', len(followers))
                if followers_count >= follower_count_cutoff:  # truncate the followers
                    break
        except TweepyException as tweepy_exception:
            logger.warning(tweepy_exception)
            continue
        follower_list.append(followers)
        df = concat([df, DataFrame(data={'source': id_, 'target': follower_list[0]})])
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
        logger.info(G_sorted.head().to_dict())
        G_tmp = k_core(G, 4)  # Exclude nodes with degree less than 10

        # todo roll these up
        # Turn partition into dataframe
        partition = DataFrame([community_louvain.best_partition(G_tmp)]).T
        partition = partition.reset_index()
        partition.columns = ['names', 'group']

        G_sorted = DataFrame(sorted(G_tmp.degree, key=lambda x: x[1], reverse=True), columns=['names', 'degree'])
        logger.info(G_sorted.head().to_dict())
        dc = G_sorted
        combined = merge(dc, partition, how='left', left_on='names', right_on='names')

        # todo label the nodes with user names instead of IDs
        graph_package = 'plotly'

        if graph_package == 'matplotlib':
            pos = spring_layout(G_tmp)
            f, ax = subplots(figsize=(10, 10))
            style.use('ggplot')
            nodes = draw_networkx_nodes(G_tmp, pos, cmap=cm.Set1, node_color=combined['group'], alpha=0.8)
            nodes.set_edgecolor('k')
            draw_networkx_labels(G_tmp, pos, font_size=8)
            draw_networkx_edges(G_tmp, pos, width=1.0, alpha=0.2)
            savefig('./output/{}-clustered.png'.format(me.screen_name))
        elif graph_package == 'plotly':
            node_x = [edge[0] for edge in pos.values()]
            node_y = [edge[1] for edge in pos.values()]

            edge_trace = Scatter(
                x=node_x, y=node_y,
                line=dict(width=0.5, color='#888'),
                hoverinfo='none',
                mode='lines')

            node_trace = Scatter(
                x=node_x, y=node_y,
                mode='markers',
                hoverinfo='text',
                marker=dict(
                    showscale=True,
                    # colorscale options
                    # 'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
                    # 'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
                    # 'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
                    colorscale='YlGnBu',
                    reversescale=True,
                    color=[],
                    size=10,
                    colorbar=dict(
                        thickness=15,
                        title='Node Connections',
                        xanchor='left',
                        titleside='right'
                    ),
                    line_width=2))

            node_adjacencies = []
            node_text = []
            for node, adjacencies in enumerate(G.adjacency()):
                node_adjacencies.append(len(adjacencies[1]))
                node_text.append('# of connections: ' + str(len(adjacencies[1])))

            node_trace.marker.color = node_adjacencies
            node_trace.text = node_text

            fig = Figure(data=[edge_trace, node_trace],
                            layout=Layout(
                                title='<br>network graph',
                                titlefont_size=16,
                                showlegend=False,
                                hovermode='closest',
                                margin=dict(b=20, l=5, r=5, t=40),
                                annotations=[dict(
                                    text="text",
                                    showarrow=False,
                                    xref="paper", yref="paper",
                                    x=0.005, y=-0.002)],
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                            )
            fig.show()
        else:
            raise NotImplemented(graph_package)

    logger.info('total time: {:5.2f}s'.format(time() - time_start))
