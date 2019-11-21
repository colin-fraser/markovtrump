import tweepy
import json
from secrets import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
from trumpbot import MCCorpus
from os import path
import argparse


CORPUS_SIZE = 200
MAX_TWEETS = 10
SOURCE_READER_ID = "realDonaldTrump"
LOCAL_TWEETS = path.expanduser("~/tweets.json")


def build_tweet(corpus: MCCorpus, reply_id=None, redraw_if=["...", ".", "$", "\"", "'", "RT"]):
    tweet = corpus.predict()
    while tweet[1] in redraw_if:  # redraw if the first token is not what we want
        tweet = corpus.predict()
    return tweet


def send_tweet(tweet, api: tweepy.API, in_reply_to_status_id=None, 
               auto_populate_reply_metadata=False):
    return api.update_status(status=tweet.formatted, in_reply_to_status_id=in_reply_to_status_id,
                             auto_populate_reply_metadata=auto_populate_reply_metadata)


def save_tweet_id_record(timeline):
    with open(LOCAL_TWEETS, 'w') as f:
        json.dump([t.id for t in timeline], f)
    return True

if __name__ == '__main__':

    ### agparse stuff
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", "-f", action="store_const", const=True)
    force = parser.parse_args().force  # force a tweet

    ### auth stuff
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    ### main stuff
    timeline = api.user_timeline(SOURCE_READER_ID, count=CORPUS_SIZE, tweet_mode='extended')
    if not path.exists(LOCAL_TWEETS):
        save_tweet_id_record(timeline)
    with open(LOCAL_TWEETS) as f:
        local_tweets = json.load(f)
    n_new_tweets = len([t for t in timeline if t.id not in local_tweets])
    if force:
        n_new_tweets += 1
    print("%i new tweets found" % n_new_tweets)
    tweettext = [t.full_text for t in timeline]
    print("%i tweets retrieved" % len(tweettext))

    corpus = MCCorpus(2)
    corpus.fit(tweettext)

    if n_new_tweets > 0:
        tweets_to_send = min(n_new_tweets, MAX_TWEETS)
        for i in range(tweets_to_send):
            reply_id = None
            auto_populate_reply_metadata = False
            if i == tweets_to_send:
                reply_id = timeline[-1].id
                print("Repling to %s" % reply_id)
            tweet = build_tweet(corpus, reply_id, auto_populate_reply_metadata)
            sent = send_tweet(tweet, api, in_reply_to_status_id=reply_id,
                    auto_populate_reply_metadata=auto_populate_reply_metadata)
            print(tweet.formatted)
        save_tweet_id_record(timeline)
