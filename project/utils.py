from itertools import tee, islice, izip_longest

__author__ = 'guglielmo'


def get_next(some_iterable, window=1):
    """
    returns an iterable that pre-fetches next item
    usage:
        for line, next_line in get_next(original_iterable):
            ... do stuff

    :param   some_iterable: the original iterable
    :param   window: the number of lines to look ahead
    :return: iterable of tuples
    """
    items, nexts = tee(some_iterable, 2)
    nexts = islice(nexts, window, None)
    return izip_longest(items, nexts)

