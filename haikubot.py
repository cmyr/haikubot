from __future__ import print_function
import gdbm
import cPickle as pickle
import os
import re
import sys
import shelve
import random
import time

import anydbm
import poetryutils


HAIKU_REVIEW_FILE = 'haikureview.dat'
SHARED_DATA_FILE = 'haiku.dat'
DATA_SOURCE_DIR = '~/code/anagramer/data/anagrammdbmen.db/archive/'
DATA_SOURCE_DIR = os.path.expanduser(DATA_SOURCE_DIR)

HAIKU_STATUS_NEW = 'new'
HAIKU_STATUS_APPROVED = 'approved'
HAIKU_STATUS_POSTED = 'posted'
HAIKU_STATUS_FAILED = 'failed'


class HaikuBot(object):
    """
    you twitter poets
    beauty is your lost verses
    I find them. save them.
    """
    def __init__(self, review=True):
        super(HaikuBot, self).__init__()
        self.processed_files = list()
        self.review = list()
        self.shared_data = None
        if review:
            # we don't want to open shared data unless it's review
            self._load()
        self._iter = iter(self.review)

    def __len__(self):
        return len(self.review)

    def _load(self, for_review=True):
        # if we have existing state, open it up.
        try:
            self.shared_data = shelve.open(SHARED_DATA_FILE, 'w', writeback=True)
        except anydbm.error:
            print('error loading shared data')
            self.shared_data = shelve.open(SHARED_DATA_FILE, 'c', writeback=True)
            self.shared_data['to_post'] = list()
            self.shared_data['processed'] = list()
        
        if for_review:
            try:
                data = pickle.load(open(HAIKU_REVIEW_FILE, 'r'))
                self.review = data['haiku']
                self.processed_files = data['processed']
            except IOError:
                return


    def _close(self, for_review=True):
        print('closing')
        self.shared_data.close()
        if for_review:
            d = {'haiku': self.review, 'processed': self.processed_files}
            pickle.dump(d, open(HAIKU_REVIEW_FILE, 'w'))
        

    def run(self, review=False, source=None):
        if not acquire_lock():
            print('failed to acquire lock')
            return
        try:
            if not len(self.review):
                if not source:
                    source = self._get_source()
                lines = self._extract_lines(source)
                self.review = self._generate_haiku(lines)
            if review:
                simple_gui(self)

            self._close()
        finally:    
            release_lock()

    def approve(self, haiku):
        print('approved')
        self.review.remove(haiku)
        haiku['status'] = HAIKU_STATUS_APPROVED
        self.shared_data['to_post'].append(haiku)


    def remove(self, haiku):
        self.review.remove(haiku)

    def _generate_haiku(self, lines):

        haikus = list()

        lines = [l for l in lines if not poetryutils.contains_url(l[0])]
        # these are tuples, now
        fives = [(x,y) for x,y in lines if poetryutils.count_syllables(x) == 5]
        sevens = [(x,y) for x,y in lines if poetryutils.count_syllables(x) == 7]
        random.shuffle(fives)
        random.shuffle(sevens)

        while len(fives) and len(sevens):
            try:
                h = [fives.pop(), sevens.pop(), fives.pop()]
            except IndexError:
                # empty list
                break
            haikus.append(self._format_haiku(h))

        return haikus

    def _format_haiku(self, haiku):
        text = [x for x, y in haiku]
        text = '\n'.join(text)

        ids = tuple([y for x,y in haiku])
        return {'text': text, 'tweets': ids, 'status':HAIKU_STATUS_NEW}


    def _get_source(self):
        files = os.listdir(DATA_SOURCE_DIR)
        files = [f for f in files if f not in self.processed_files]
        source = files.pop()
        self.processed_files.append(source)

    def _extract_lines(self, source):
        print('extracting lines')
        lines = []
        db = gdbm.open(source)
        k = db.firstkey()
        seen = 0
        prevk = k
        while k is not None:
            seen += 1
            prevk = k
            try:
                lines.append(_tweet_from_dbm(db[k]))
            except ValueError:
                k = db.nextkey(k)
                continue
            sys.stdout.write('seen: %i\r' % seen)
            sys.stdout.flush()

            k = db.nextkey(k)
        db.close()
        return [(x['text'], x['id']) for x in lines]

# things below this are related to the 'public API' our daemon
# uses to find and post and confirm posting, etc

    def count(self):
        """returns how many haiku are awaiting posting"""
        self._open_datasource()
        count = len(self.shared_data['to_post'])
        self._close_datasource()
        return count

    def _open_datasource(self):
        success = acquire_lock()
        while not success:
            print('waiting for lock')
            time.sleep(30)
            success = acquire_lock()

        self._load(False)
        return True

    def _close_datasource(self):
        self.shared_data.close()
        release_lock()
        return True

    def haiku_for_post(self):
        """
        returns the next approved haiku to be posted
        """
        if not self._open_datasource():
            return
        try:
            haiku = self.shared_data['to_post'][0]
        except IndexError:
            haiku = None

        self._close_datasource()
        return haiku

    def post_failed(self, haiku):
        self._open_datasource()
        self.shared_data['to_post'].remove(haiku)
        haiku['status'] = HAIKU_STATUS_FAILED
        self.shared_data['processed'].append(haiku)
        self._close_datasource()

    def post_succeeded(self, haiku):
        self._open_datasource()
        self.shared_data['to_post'].remove(haiku)
        haiku['status'] = HAIKU_STATUS_POSTED
        self.shared_data['processed'].append(haiku)
        self._close_datasource()



def _tweet_from_dbm(dbm_tweet):
    tweet_values = re.split(unichr(0017), dbm_tweet.decode('utf-8'))
    t = dict()
    t['id'] = int(tweet_values[0])
    t['hash'] = tweet_values[1]
    t['text'] = tweet_values[2]
    return t


def simple_gui(model):
    """
    cli utility for reviewing generated haiku
    """
    to_review = iter(model.review)
    h = to_review.next()

    print('\n%d haiku to review\n' % len(model))
    while h:
        # just debug for now
        print(h['text'], '\n')
        while True:
            inp = raw_input('(y/n):')
            if inp.lower() in ['y', 'yes']:
                model.approve(h)
                break
            elif inp.lower() in ['n', 'no']:
                model.remove(h)
                break
            elif inp.lower() in ['q']:
                return
        try:
            h = to_review.next()
        except StopIteration:
            h = None



LOCK_FILE = 'haiku.lock'

def acquire_lock():
    if os.access(LOCK_FILE, os.F_OK):
        return False

    with open(LOCK_FILE, 'w') as f:
        f.write(str(time.time()))

    return True


def release_lock():
    os.remove(LOCK_FILE)


def main():


    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', type=str, help="source file (mostly for debugging)")
    parser.add_argument('-r', '--review', help='review hits (CLI)', action="store_true")
    parser.add_argument('--debug', help='run with debug settings', action="store_true")
    parser.add_argument('--test-sources', action="store_true")
    args = parser.parse_args()

    # if args.debug:
    #     # source = ''
    #     h = HaikuBot()
    #     h.run(True, source)

    if args.test_sources:
        h = HaikuBot()
        print(h._get_source())

    else:
        # normal run
        h = HaikuBot()
        h.run(review=args.review)



if __name__ == "__main__":
    main()