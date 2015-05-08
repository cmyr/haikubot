# coding: utf-8
from __future__ import print_function
from __future__ import unicode_literals

import poetryutils2
import zmqstream
import twitterstream
import time
import sys


def generate_haiku(debug=False, verbose=False):
    haikuer = poetryutils2.Haikuer(debug=(debug or verbose))

    filters = init_filters()
    if not debug:
        stream_source = zmq_stream_source()
        source = poetryutils2.line_iter(stream_source, filters, key='text')
    else:
        source = debug_dict_wrapper(debug_source())

    for beauty in haikuer.generate_from_source(source, key='text'):
        yield format_haiku(beauty)

def a_solitary_poem():
    gen = generate_haiku()
    return gen.next()

def init_filters():
    filters = []
    filters.append(poetryutils2.filters.numeral_filter)
    filters.append(poetryutils2.filters.url_filter)
    filters.append(poetryutils2.filters.ascii_filter)
    filters.append(poetryutils2.filters.low_letter_filter(0.9))
    filters.append(poetryutils2.filters.swears_filter())
    filters.append(poetryutils2.filters.real_word_ratio_filter(0.9))
    filters.append(poetryutils2.filters.syllable_count_filter('5,7'))
    filters.append(poetryutils2.filters.blacklist_filter([
        'oomf'
        ]))

    return filters

def debug_source():
    lines = poetryutils2.utils.lines_from_file('/Users/cmyr/tweetdbm/may09.txt')
    filters = [poetryutils2.filters.url_filter,
        poetryutils2.filters.ascii_filter,
        poetryutils2.filters.low_letter_filter(0.9)]
    source = poetryutils2.line_iter(lines, filters)
    return source


def debug_dict_wrapper(an_iter):
    num = 0
    for line in an_iter:
        screen_name = "user %d" % num
        wrapped = {'text': line, 'user': {'screen_name': screen_name}}
        yield wrapped
        num += 1

def zmq_stream_source():
    stream = zmqstream.zmq_iter()
    return item_stripper(stream)

def item_stripper(stream_iter):
    keys = ['text', 'user']
    for item in stream_iter:
        stripped_item = dict()
        for k in keys:
            stripped_item[k] = item.get(k)
        yield stripped_item



def format_haiku(haiku):
    try:
        haiku_text = [h.info.get('text') for h in haiku]
        haiku_text = '\n'.join(haiku_text)

        haiku_usernames = ['(@)%s' % h.info.get('user').get('screen_name') for h in haiku]
        haiku_usernames = '— ' + ' / '.join(haiku_usernames)

        return "%s\n\n%s" % (haiku_text, haiku_usernames)
    except AttributeError:
        # TODO: debug why we're being sent 'none', sometimes
        print(haiku)


def haiku_test(debug):
    for poem in generate_haiku(debug=debug, verbose=True):
        print(poem)



def main():
    haiku_test(False)



if __name__ == "__main__":
    main()