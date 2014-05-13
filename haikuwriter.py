# coding: utf-8
from __future__ import print_function
from __future__ import unicode_literals

import poetryutils2
import twitterstream

def generate_haiku():
    haikuer = poetryutils2.Haikuer(debug=True)


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

    source = poetryutils2.line_iter(twitter_stream_source(), filters)
    for beauty in haikuer.generate_from_source(source):
        poem = '%s\n%s\n%s\n\n' % (beauty[0], beauty[1], beauty[2])
        print(poem.encode('utf8'))


def debug_source():
    lines = poetryutils2.utils.lines_from_file('/Users/cmyr/tweetdbm/may09.txt')
    filters = [poetryutils2.filters.url_filter,
        poetryutils2.filters.ascii_filter,
        poetryutils2.filters.low_letter_filter(0.9)]
    source = poetryutils2.line_iter(lines, filters)

def twitter_stream_source():
    streamer = twitterstream.TwitterStream()
    stream = streamer.stream_iter(
        languages=['en'],
        user_agent="@haiku9000",
        just_text=True
        )
    return stream

def haiku_test():
    generate_haiku()
    # lines = poetryutils2.utils.lines_from_file('/Users/cmyr/Documents/twitterpoems/20ktst.txt')
    






def main():
    haiku_test()
    # import argparse
    # parser = argparse.ArgumentParser()
    # parser.add_argument('arg1', type=str, help="required argument")
    # parser.add_argument('arg2', '--argument-2', help='optional boolean argument', action="store_true")
    # args = parser.parse_args()


if __name__ == "__main__":
    main()