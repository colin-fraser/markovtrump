import json
import pandas as pd
import nltk
from collections import Counter
from numpy.random import choice

START = "____START____"
END = "____END____"


def sample_from_choices(choices):
    words, unnormalized_probs = tuple(zip(*choices.items()))
    denom = sum(unnormalized_probs)
    probs = [d / denom for d in unnormalized_probs]
    return choice(words, p=probs)


def clean_up_tt(tweet):
    tweet = tweet.replace("’", "'").replace("“", '"').replace("”", '"').replace("U.S.A.", "USA")
    return tweet


def append_token(tweet, token):
    if token == END:
        return tweet
    elif tweet == "":
        return token
    elif token in "!%,.\'\":)?":
        tweet += token
    elif tweet[-1] in "$(":
        tweet = tweet + token
    else:
        tweet += (" " + token)
    return tweet


def tweet_from_token_list(token_list):
    tweet = ""
    for token in token_list:
        if token not in (START, END):
            tweet = append_token(tweet, token)
    return tweet


class MCTweet(list):

    def __init__(self, start=START):
        self.append(start)

    def current_ngram(self, n):
        if n == 1:
            return self[-1]
        return tuple(self[-n:])


    def __len__(self):
        return len(self.formatted)


    @property
    def formatted(self):
        return tweet_from_token_list(self)


class MCCorpus:

    def __init__(self, n=3):
        self.n = n
        self.backoff_cutoff = n
        self.tokenizer = nltk.tokenize.TweetTokenizer()
        self.onegrams = dict()
        self.twograms = dict()
        self.threegrams = dict()
        self.exclusion = "\"()"
        self.filter_out_url = True

    def filter_words(self, words):
        words = [w for w in words if w not in self.exclusion]
        if self.filter_out_url:
            words = [w for w in words if "https" not in w]

        # replacements. This is ugly and hacky, fix in a later version.
        for j, word in enumerate(words):
            if word == 'USA':
                words[j] = 'U.S.A.'
        return words

    def fit(self, text_list):
        for tweet in text_list:
            text = clean_up_tt(tweet)
            words = [START] + self.tokenizer.tokenize(text) + [END]
            words = self.filter_words(words)
            for word, nextword in zip(words, words[1:]):
                if word not in self.onegrams:
                    self.onegrams[word] = Counter()
                self.onegrams[word][nextword] += 1
            for word0, word1, nextword in zip(words, words[1:], words[2:]):
                if (word0, word1) not in self.twograms:
                    self.twograms[(word0, word1)] = Counter()
                self.twograms[(word0, word1)][nextword] += 1
            for word0, word1, word2, nextword in zip(words, words[1:], words[2:], words[3:]):
                if (word0, word1, word2) not in self.threegrams:
                    self.threegrams[(word0, word1, word2)] = Counter()
                self.threegrams[(word0, word1, word2)][nextword] += 1

    def predict(self, seed=START, limit_length=280):

        tweet = MCTweet(seed)

        while tweet.current_ngram(1) != END:
            if (tweet.current_ngram(3) in self.threegrams) and (
                    len(self.threegrams[tweet.current_ngram(3)]) >= self.backoff_cutoff):
                tweet.append(sample_from_choices(self.threegrams[tweet.current_ngram(3)]))
            elif (tweet.current_ngram(2) in self.twograms) and (len(self.twograms[tweet.current_ngram(2)]) >= self.backoff_cutoff):
                tweet.append(sample_from_choices(self.twograms[tweet.current_ngram(2)]))
            else:
                tweet.append(sample_from_choices(self.onegrams[tweet.current_ngram(1)]))

            if len(tweet) > limit_length:
                tweet = MCTweet(seed)


        return tweet

if __name__ == '__main__':
    with open("tweets.json", encoding="utf8") as f:
        td = json.load(f)
    tweettext = [t['text'] for t in td[-250:]]
    corpus = MCCorpus(2)
    corpus.fit(tweettext)
    for i in range(20):
        tweet = corpus.predict()
        while tweet[1] in  ["...", ".", "$", "\"", "'"]:
            tweet = corpus.predict()
        print("TWEET: (len=%i)" % len(tweet))
        print(tweet.formatted)