from __future__ import print_function
import requests
import json
from requests_oauthlib import OAuth1
from haikucreds import (CONSUMER_KEY, CONSUMER_SECRET,
                          ACCESS_KEY, ACCESS_SECRET)


# disable logging from requests
import logging
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

class StreamConnectionError(Exception):
    """our streaming connection didn't fire"""
    pass

class TwitterStream(object):
    """
    very basic single-purpose object for connecting to the streaming API
    in most use-cases python-twitter-tools or tweepy would be preferred
    BUT we need both gzip compression and the 'language' parameter
    """
    def __init__(self,
        consumer_key = CONSUMER_KEY,
         consumer_secret = CONSUMER_SECRET,
        access_key = ACCESS_KEY,
        access_secret = ACCESS_SECRET):
        self._access_key = access_key
        self._access_secret = access_secret
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret

    def stream_iter(self,
        endpoint='sample',
        languages='None',
        user_agent='@cmyr custom streaming client 4 research & fun',
        just_text=False,
        stall_warnings=True):
        auth = OAuth1(self._consumer_key, self._consumer_secret,
                      self._access_key, self._access_secret)

        url = 'https://stream.twitter.com/1.1/statuses/%s.json' % endpoint
        query_headers = {'Accept-Encoding': 'deflate, gzip',
                         'User-Agent': user_agent}
        query_params = dict()
        lang_string = None
        if languages:
            if type(languages) is list:
                lang_string = ','.join(languages)
            elif isinstance(languages, basestring):
                lang_string = languages

        if lang_string:
            query_params['language'] = lang_string
        if stall_warnings:
            query_params['stall_warnings'] = True
        try:    
            stream_connection = requests.get(url, auth=auth, stream=True,
                                             params=query_params, headers=query_headers)
        except requests.exceptions.ConnectionError as err:
            raise StreamConnectionError()


        

        def de_json(an_iterator):
            for json_item in an_iterator:
                if not json_item:
                    continue
                try:
                    item = json.loads(json_item)
                    if item.get('text'):
                        yield item
                except ValueError:
                    print('value error decoding json %s' % json_item)


        if not just_text:
            return de_json(stream_connection.iter_lines())
        else:
            def text_stripper(an_iterator):
                for item in an_iterator:
                    if item.get('text'):
                        yield item.get('text')
            return text_stripper(de_json(stream_connection.iter_lines()))


if __name__ == '__main__':
    anagram_stream = TwitterStream(CONSUMER_KEY, CONSUMER_SECRET,
                                   ACCESS_KEY, ACCESS_SECRET)

    stream_connection = anagram_stream.stream_iter(languages=['en'], just_text=True)
    for line in stream_connection:
        print(line)
        # if line:
        #     try:
        #         tweet = json.loads(line)
        #         print(tweet)
        #         # if tweet.get('text'):
        #         #     print(tweet.get('text'))
        #     except ValueError:
        #         print(line)

