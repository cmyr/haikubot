# coding=utf-8

from __future__ import print_function
import time
import haikubot
import shelve
import random
import json

from twitter.oauth import OAuth
from twitter.stream import TwitterStream
from twitter.api import Twitter, TwitterError, TwitterHTTPError

from haikucreds import (CONSUMER_KEY, CONSUMER_SECRET,
                          ACCESS_KEY, ACCESS_SECRET)


POST_INTERVAL = 240 


class HaikuDemon(object):
    """
    I sit idle, calm
    waiting for the call that wakes
    so I may hold forth
    """
    def __init__(self, post_interval=POST_INTERVAL, debug=False):
        super(HaikuDemon, self).__init__()
        self.datasource = haikubot.Haikunator(review=False)
        self._debug = debug
        self.post_interval = post_interval * 60
        self.twitter = twitter = Twitter(
            auth=OAuth(ACCESS_KEY,
                ACCESS_SECRET,
                CONSUMER_KEY,
                CONSUMER_SECRET),
            api_version='1.1')
        
    def run(self):
        while True:
            self.entertain_the_huddled_masses()
            self.sleep()

    def entertain_the_huddled_masses(self):

        count = self.datasource.count()
        print('datasource count = %d' % count)
        if not count:
            return

        haiku = self.datasource.haiku_for_post()
        formatted_haiku = self.format_haiku(haiku)
        if not formatted_haiku:
            print('failed to format haiku?')
            return
        if self.post(formatted_haiku):
            self.datasource.post_succeeded(haiku)
        else:
            self.datasource.post_failed(haiku)

    def format_haiku(self, haiku):
        if not self._debug:
            usernames = self.get_user_names(haiku['tweets'])
        else:
            usernames = ('user1', 'user2', 'user3')

        usernames = ['@%s' % n for n in usernames]
        usernames_string = u'– ' + ' / '.join(usernames)
        formatted_haiku = '%s\n\n%s' % (haiku['text'], usernames_string)
        return formatted_haiku

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


    def sleep(self):
        randfactor = random.randrange(0, self.post_interval)
        sleep_interval = self.post_interval * 0.5 + randfactor
        time.sleep(sleep_interval)
        pass




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