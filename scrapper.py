import snscrape.modules.twitter as sntwitter
from datetime import datetime
from dateutil import parser


# like, id, text
# get tweets that have more than 10 likes
def modify_date(date):
    today_date = parser.parse(date)
    return str(today_date.year)+'-'+str(today_date.month)+'-'+str(today_date.day)


def get_tweets(search_key, start_date, end_date):
    search_key += " since:" + modify_date(start_date) + " until:" + modify_date(end_date)
    my_tweets = {}
    counter = 0
    print(search_key)
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
