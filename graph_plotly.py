from json import load
from logging import INFO
from logging import basicConfig
from logging import getLogger
from time import time

from networkx import spring_layout
from networkx import read_gpickle
from plotly.graph_objects import Figure
from plotly.graph_objects import Layout
from plotly.graph_objects import Scatter
from plotly.io import write_html

COLORSCALE = ['Greys', 'YlGnBu', 'Greens', 'YlOrRd', 'Bluered', 'RdBu', 'Reds', 'Blues', 'Picnic', 'Rainbow',
              'Portland', 'Jet', 'Hot', 'Blackbody', 'Earth', 'Electric', 'Viridis']

# https://towardsdatascience.com/how-to-download-and-visualize-your-twitter-network-f009dbbf107b

if __name__ == '__main__':
    time_start = time()
    logger = getLogger(__name__)
    basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=INFO, )
    logger.info('started.', )

    # load up the graph we're going to use to build the layout
    G_small = read_gpickle(path='./data/positions.pkl')
    pos = spring_layout(G_small)
    # load up the full graph
    G = read_gpickle(path='./data/adjacency.pkl')

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
            colorscale=COLORSCALE[1],
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
                     showlegend=False,
                     titlefont_size=16,
                     hovermode='closest',
                     margin=dict(b=20, l=5, r=5, t=40),
                     annotations=[dict(
                         text='text',
                         showarrow=False,
                         xref='paper', yref='paper',
                         x=0.005, y=-0.002)],
                     xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                     yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))

    write_html(fig=fig, file='./output/{}.html'.format('test'))

    logger.info('total time: {:5.2f}s'.format(time() - time_start))
