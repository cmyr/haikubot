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

import haikubot
from haikucreds import (CONSUMER_KEY, CONSUMER_SECRET,
                        ACCESS_KEY, ACCESS_SECRET, BOSS_USERNAME)


POST_INTERVAL = 240


class HaikuDemon(object):

    """
    I sit idle, calm
    waiting for the call that wakes
    so I may hold forth
    """

    def __init__(self, post_interval=POST_INTERVAL, debug=False):
        super(HaikuDemon, self).__init__()
        self.datasource = haikubot.HaikuBot(review=False)
        self._debug = debug
        self.post_interval = post_interval * 60
        self.twitter = twitter = Twitter(
            auth=OAuth(ACCESS_KEY,
                       ACCESS_SECRET,
                       CONSUMER_KEY,
                       CONSUMER_SECRET),
            api_version='1.1')
        self.sent_warnings = (False, False, False)
        self.warning_level = 0

    def run(self):
        self._check_post_time()
        while True:
            self.entertain_the_huddled_masses()
            self.sleep(self.post_interval)

    def _check_post_time(self):
        last_post = self.datasource.last_post()
        temps_perdu = time.time() - last_post
        if last_post and temps_perdu < (self.post_interval / 2):
            print('skipping post. %d elapsed, post_interval %d' %
                  (temps_perdu, self.post_interval))

            self.sleep(self.post_interval - temps_perdu)

    def entertain_the_huddled_masses(self):

        count = self.datasource.count()
        self._check_count(count)
        print('datasource count = %d' % count)
        if not count:
            return

        haiku = self.datasource.haiku_for_post()
        formatted_haiku = self.format_haiku(haiku)

        if formatted_haiku and self.post(formatted_haiku):
            self.datasource.post_succeeded(haiku)
        else:
            self.datasource.post_failed(haiku)
            self.entertain_the_huddled_masses()

    def format_haiku(self, haiku):
        try:
            if not self._debug:
                usernames = self.get_user_names(haiku['tweets'])
            else:
                usernames = ('user1', 'user2', 'user3')

            usernames = ['@%s' % n for n in usernames]
            usernames_string = u'– ' + ' / '.join(usernames)
            formatted_haiku = '%s\n\n%s' % (haiku['text'], usernames_string)
            return formatted_haiku

        except TwitterError as err:
            response = json.JSONDecoder().decode(err.response_data)
            response = response.get('errors')
            print(response)
            return None

    def get_user_names(self, tweets):
        usernames = []
        for t in tweets:
            tweet = self.twitter.statuses.show(
                id=str(t),
                include_entities='false')
            if tweet:
                usernames.append(tweet.get('user').get('screen_name'))

        return usernames

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
        randfactor = random.randrange(0, interval)
        interval = interval * 0.5 + randfactor
        sleep_chunk = 10  # seconds

        print('sleeping for %d minutes' % (interval / 60))

        while interval > 0:
            sleep_status = ' %s remaining \r' % (
                haikubot.format_seconds(interval))
            sys.stdout.write(sleep_status.rjust(35))
            sys.stdout.flush()
            time.sleep(sleep_chunk)
            interval -= sleep_chunk

        print('\n')

    def send_dm(self, message):
        """sends me a DM if I'm running out of haiku"""
        try:
            self.twitter.direct_messages.new(user=BOSS_USERNAME, text=message)
        except TwitterError as err:
            print(err)

    def _check_count(self, count):
        """checks to see if we're close to running out of haiku to tweet"""

        good_until = count * self.post_interval
        message = 'haikubot will run out of haiku in %s' % haikubot.format_seconds(
            good_until)
        should_post = False
        if good_until == 0 and self.warning_level < 4:
            message = 'EMPTY!'
            should_post = True
            self.warning_level = 4
        elif good_until > 0 and self.warning_level == 4:
            self.warning_level = 0

        if good_until < 24 * 60 * 60 and self.warning_level < 3:
            message = 'ONE DAY: ' + message
            should_post = True
            self.warning_level = 3
        elif good_until < 72 * 60 * 60 and self.warning_level < 2:
            message = 'Three days: ' + message
            should_post = True
            self.warning_level = 2
        elif good_until < 168 * 60 * 60 and self.warning_level < 1:
            message = 'One week: ' + message
            should_post = True
        elif good_until > 168 * 60 * 60:
            self.warning_level = 0

        # this... is not my proudest hour
        if should_post:
            if self._debug:
                print(message)
            else:
                self.send_dm(message)


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
