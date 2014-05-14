# coding=utf-8

from __future__ import print_function
import time
import sys
import shelve
import random
import json

from twitter.oauth import OAuth
from twitter.stream import TwitterStream
from twitter.api import Twitter, TwitterError, TwitterHTTPError

# import haikubot
import haikuwriter

from haikucreds import (CONSUMER_KEY, CONSUMER_SECRET,
                        ACCESS_KEY, ACCESS_SECRET, BOSS_USERNAME)


POST_INTERVAL = 60


class HaikuDemon(object):

    """
    I sit idle, calm
    waiting for the call that wakes
    so I may hold forth
    """

    def __init__(self, post_interval=POST_INTERVAL, debug=False):
        super(HaikuDemon, self).__init__()
        self._debug = debug
        self.post_interval = post_interval * 60
        self.twitter = twitter = Twitter(
            auth=OAuth(ACCESS_KEY,
                       ACCESS_SECRET,
                       CONSUMER_KEY,
                       CONSUMER_SECRET),
            api_version='1.1')

    def run(self):
        try:
            # self._check_post_time()
            while True:
                self.entertain_the_huddled_masses()
                self.sleep(self.post_interval)

        except KeyboardInterrupt:
            print('exiting')
            sys.exit(0)

    # def _check_post_time(self):
    #     # last_post = self.datasource.last_post()
    #     temps_perdu = time.time() - last_post
    #     if last_post and temps_perdu < (self.post_interval / 2):
    #         print('skipping post. %d elapsed, post_interval %d' %
    #               (temps_perdu, self.post_interval))

    #         self.sleep(self.post_interval - temps_perdu)

    def entertain_the_huddled_masses(self):
        haiku = haikuwriter.a_solitary_poem()
        self.post(haiku)


    def post(self, formatted_haiku):
        if self._debug:
            print(formatted_haiku)
            return True

        try:
            success = self.twitter.statuses.update(status=formatted_haiku)
            print('posted haiku:\n\n%s' % formatted_haiku)
            return success
        except TwitterError as err:
            http_code = err.e.code

            if http_code == 403:
                # get the response from the error:
                response = json.JSONDecoder().decode(err.response_data)
                response = response.get('errors')
                if response:
                    response = response[0]

                    error_code = int(response.get('code'))
                    if error_code == 187:
                        print('attempted to post duplicate')
                        # status is a duplicate
                        return True
                    else:
                        print('unknown error code: %d' % error_code)

            else:
                # if http_code is *not* 403:
                print('received http response %d' % http_code)
                # assume either a 404 or a 420, and sleep for 10 mins
                time.sleep(600)
                return False

    def sleep(self, interval):
        interval = int(interval)
        randfactor = random.randrange(0, interval)
        interval = interval * 0.5 + randfactor
        sleep_chunk = 10  # seconds

        print('sleeping for %d minutes' % (interval / 60))

        while interval > 0:
            sleep_status = ' %s remaining \r' % (
            format_seconds(interval))
            sys.stdout.write(sleep_status.rjust(35))
            sys.stdout.flush()
            time.sleep(sleep_chunk)
            interval -= sleep_chunk

        print('\n')

    # def send_dm(self, message):
    #     """sends me a DM if I'm running out of haiku"""
    #     try:
    #         self.twitter.direct_messages.new(user=BOSS_USERNAME, text=message)
    #     except TwitterError as err:
    #         print(err)

def format_seconds(seconds):
    """
    convert a number of seconds into a custom string representation
    """
    d, seconds = divmod(seconds, (60 * 60 * 24))
    h, seconds = divmod(seconds, (60 * 60))
    m, seconds = divmod(seconds, 60)
    time_string = ("%im %0.2fs" % (m, seconds))
    if h or d:
        time_string = "%ih %s" % (h, time_string)
    if d:
        time_string = "%id %s" % (d, time_string)
    return time_string


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--post-interval', type=int,
                        help='interval (in minutes) between posts')
    parser.add_argument('-d', '--debug',
                        help='run with debug flag', action="store_true")
    args = parser.parse_args()

    kwargs = {}
    kwargs['debug'] = args.debug
    kwargs['post_interval'] = args.post_interval or POST_INTERVAL

    print(kwargs)
    print(type(kwargs['post_interval']))

    daemon = HaikuDemon(**kwargs)
    return daemon.run()


if __name__ == "__main__":
    main()
