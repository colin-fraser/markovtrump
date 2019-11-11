import tweepy
import json
from secrets import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
from trumpbot import MCCorpus
from os import path
import argparse
import boto3


CORPUS_SIZE = 200

MAX_TWEETS = 10
SOURCE_READER_ID = "realDonaldTrump"
LOCAL_TWEETS = path.expanduser("~/tweets.json")


def build_tweet(corpus: MCCorpus, redraw_if=["...", ".", "$", "\"", "'", "RT"]):
    tweet = corpus.predict()
    while tweet[1] in redraw_if:  # redraw if the first token is not what we want
        tweet = corpus.predict()
    return tweet


def send_tweet(tweet, api: tweepy.API):
    return api.update_status(tweet.formatted)


def save_tweet_id_record(timeline):
    with open(LOCAL_TWEETS, 'w') as f:
        json.dump([t.id for t in timeline], f)
    return True

if __name__ == '__main__':

    ### agparse stuff
    parser = argparse.ArgumentParser()
    parser.add_argument("--phone", "-p")
    parser.add_argument("--force", "-f")
    phone = parser.parse_args().phone
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
        if phone:
            print("Connecting to AWS")
            texter = boto3.client("sns")
        for i in range(min(n_new_tweets, MAX_TWEETS)):
            tweet = build_tweet(corpus)
            sent = send_tweet(tweet, api)
            print(tweet.formatted)
            if phone:
                print("Sending text notification")
                texter.publish(PhoneNumber=phone, Message="TWEET: %s" % tweet.formatted)
        save_tweet_id_record(timeline)
