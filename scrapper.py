import snscrape.modules.twitter as sntwitter


# like, id, text
# get tweets that have more than 10 likes
def get_tweets(search_key):
    search_key += " since:2022-04-02"
    my_tweets = {}
    counter = 0
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(search_key).get_items()):
        if counter == 5:
            break
        # print(tweet.__dict__)  # lists the attributes of the tweet object. Some of them: replyCount, retweetCount, likeCount, quoteCount, media, retweetedTweet, inReplyToUser, inReplyToTweetId,
        # print(tweet.url, "like: ", tweet.likeCount)
        counter += 1
        # TODO
        #  separete original tweets and replies to other tweets
        #  categorize tweets related to different projects
        #  resim içeren (tweet.media) tweetleri tweet URL'i, tweet sahibi ile beraber kaydet, bu resimler kod çalıştığında figure olarak ekrana yansıyabilsin.

        like_and_text = tuple([tweet.content, tweet.likeCount])
        my_tweets[tweet.id] = tweet.url

    return my_tweets
