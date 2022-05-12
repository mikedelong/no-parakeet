from json import load
from logging import INFO
from logging import basicConfig
from logging import getLogger

from arrow import now

if __name__ == '__main__':
    time_start = now()
    logger = getLogger(__name__)
    basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=INFO, )
    logger.info('started.', )
    with open(file='./make_graph_settings.json', mode='r', ) as settings_fp:
        settings = load(fp=settings_fp, )
    logger.info('settings: {}'.format(settings))
    input_file = '{}/{}'.format(settings['input_folder'], settings['input_file']).replace('//', '/')

    logger.info('total time: {:5.2f}s'.format((now() - time_start).total_seconds()))
