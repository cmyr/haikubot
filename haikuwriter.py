# coding: utf-8
from __future__ import print_function
from __future__ import unicode_literals

import poetryutils2


def generate_haiku():
    pass

def haiku_test():
    # lines = poetryutils2.utils.lines_from_file('/Users/cmyr/Documents/twitterpoems/20ktst.txt')
    lines = poetryutils2.utils.lines_from_file('/Users/cmyr/tweetdbm/may09.txt')
    haik = poetryutils2.Haikuer()

    filters = [poetryutils2.filters.url_filter,
        poetryutils2.filters.ascii_filter,
        poetryutils2.filters.low_letter_filter(0.9)]

    source = poetryutils2.line_iter(lines, filters)

    for beauty in haik.generate_from_source(source):
        poem = '%s\n%s\n%s\n\n' % (beauty[0], beauty[1], beauty[2])
        print(poem.encode('utf8'))





def main():
    haiku_test()
    # import argparse
    # parser = argparse.ArgumentParser()
    # parser.add_argument('arg1', type=str, help="required argument")
    # parser.add_argument('arg2', '--argument-2', help='optional boolean argument', action="store_true")
    # args = parser.parse_args()


if __name__ == "__main__":
    main()