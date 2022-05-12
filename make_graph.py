from json import load
from logging import INFO
from logging import basicConfig
from logging import getLogger

from arrow import now
from community import community_louvain
from networkx import from_pandas_edgelist
from networkx import k_core
from pandas import DataFrame
from pandas import concat
from pandas import merge

if __name__ == '__main__':
    time_start = now()
    logger = getLogger(__name__)
    basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=INFO, )
    logger.info('started.', )
    with open(file='./make_graph_settings.json', mode='r', ) as settings_fp:
        settings = load(fp=settings_fp, )
    logger.info('settings: {}'.format(settings))
    input_file = '{}/{}'.format(settings['input_folder'], settings['input_file']).replace('//', '/')

    with open(file=input_file, mode='r') as input_fp:
        graph_data = load(fp=input_fp)

    logger.info('size: %d', len(graph_data))
    logger.info('count: %d', sum(1 for value in graph_data.values() if 'follower_list' in value.keys()))
    subgraph_data = {key: value['follower_list'] for key, value in graph_data.items() if
                     'follower_list' in value.keys()}
    logger.info('subgraph size: %d', len(subgraph_data))
    graph_df = concat([DataFrame(data={'source': key, 'target': value}) for key, value in subgraph_data.items()])
    logger.info('shape: %s', graph_df.shape)

    graph = from_pandas_edgelist(df=graph_df, source='source', target='target', edge_key=None,
                                 create_using=None, edge_attr=None)

    logger.info('edge count: %d', graph.number_of_edges())
    logger.info('node count: %d', graph.number_of_nodes())
    graph_sorted_df = DataFrame(data=sorted(graph.degree, key=lambda x: x[1], reverse=True),
                                columns=['nconst', 'degree'])
    logger.info('sorted shape: %s', graph_sorted_df.shape)

    G_tmp = k_core(G=graph, k=2)

    # todo roll these up
    # Turn partition into dataframe
    partition = DataFrame([community_louvain.best_partition(G_tmp)]).T
    partition = partition.reset_index()
    partition.columns = ['names', 'group']

    G_sorted = DataFrame(sorted(G_tmp.degree, key=lambda x: x[1], reverse=True), columns=['names', 'degree'])
    logger.info(G_sorted.head().to_dict())
    dc = G_sorted  # do we need this?
    combined_df = merge(G_sorted, partition, how='left', left_on='names', right_on='names')
    logger.info(combined_df.shape)

    logger.info('total time: {:5.2f}s'.format((now() - time_start).total_seconds()))
