import praw
import prawcore
import tweepy
import codecs
import soundcloud
import time
import handles
import keys
import datetime as dt


def main():
    """
    Run our loop to stay logged in and refreshing the subreddit.
    """
    subreddit = setup_connection_reddit('teecolz')

    auth = tweepy.OAuthHandler(keys.CONSUMER_KEY, keys.CONSUMER_SECRET)
    auth.set_access_token(keys.ACCESS_TOKEN, keys.ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True)

    while 1:
        tweetScanner(api, subreddit)
        print '[sleep] .................Refreshing in 30 sec.................'
        time.sleep(30)

def setup_connection_reddit(subreddit):
    """
    Log in to reddit
    """
    print "[bot] setting up connection with Reddit"
    red = praw.Reddit(client_id=keys.CLIENT_ID, client_secret=keys.CLIENT_SECRET,
                      password=keys.PASSWORD, user_agent=keys.USER_AGENT, username=keys.USERNAME)
    subreddit = red.subreddit(subreddit)
    print red.user.me()
    return subreddit

def check_if_new_soundcloud(subreddit, name, url):
    """
    sc
    """
    client = soundcloud.Client(client_id=keys.SOUNDCLOUD_CLIENT_ID)
    # print client.get('/me').username

    try:
        track = client.get('/resolve', url=url)
        posted_at = track.obj.get('created_at')[:19]
    except TypeError:
        print "--------------ERROR URL Is Invalid---------------"
        time.sleep(10)

    current_time = time.strftime("%Y/%m/%d %H:%M:%S", time.gmtime())

    posted_at_time = posted_at[11:]
    current_time_time = current_time[11:]

    # print posted_at
    # print current_time


    start_dt = dt.datetime.strptime(posted_at_time, '%H:%M:%S')
    end_dt = dt.datetime.strptime(current_time_time, '%H:%M:%S')
    diff = (end_dt - start_dt)
    difference_in_minutes = diff.seconds/60

    # print(difference_in_minutes)
    # print(diff)

    try:
        posted_by = str(track.obj.get('user').get('username'))
        track_title = str(track.obj.get('title'))
    except UnicodeEncodeError as e:
        print e
        time.sleep(2)

    if posted_at[:10] == current_time[:10]:
        # print 'same day'
        if difference_in_minutes < 120:
            print ("FRESH TRACK: %s - %s" % (posted_by, track_title))
            post_to_reddit(subreddit, url, track, name)

def post_to_reddit(subreddit, url, track, name):
    """
    handles posting to Reddit
    """
    try:
        # posted_by = str(track.obj.get('user').get('username'))
        track_title = str(track.obj.get('title'))

        if "-" in track_title:
            title = "[FRESH] " + track_title
        elif name.lower() in track_title.lower():
            title = "[FRESH] " + track_title
        else:
            title = "[FRESH] " + name + " - " + track_title

        subreddit.submit(title, url=url, resubmit=False)

        print "POSTED: " + title + " >>> " + url + " by " + name


    except praw.exceptions.APIException as e:
        print "--------------REDDIT Praw API Erorr---------------"
        print e
        time.sleep(10)
    # pylint: disable=E0712
    except praw.exceptions as e:
        print "--------------REDDIT Praw ERROR---------------"
        print e
        time.sleep(30)
    except prawcore.PrawcoreException as e:
        print "--------------REDDIT Prawcore ERROR---------------"
        print e
        time.sleep(30)

# In this example, the handler is time.sleep(15 * 60),
# but you can of course handle it in any way you want.

def limit_handled(cursor):
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            print "Waiting..."
            time.sleep(15 * 60)

def tweetScanner(api, subreddit):
    """
    Handles all access to Twitter
    """
    for tweet in limit_handled(tweepy.Cursor(api.home_timeline).items(50)):
        screen_name = tweet.user.screen_name
        if is_song(tweet):
            if is_known_artist(screen_name):
                for name, handle in handles.HANDLES.iteritems():
                    if str(screen_name).lower() == handle.strip("@").lower():
                        for link in tweet.entities['urls']:
                            expanded_link = link['expanded_url']
                            check_if_new_soundcloud(subreddit, name, expanded_link)

def is_song(tweet):
    """
    is it a song?
    """
    isSong = False
    knownLinks = ['soundcloud'] # , 'youtu'
    if 'urls' in tweet.entities:
        for link in tweet.entities['urls']:
            expanded_link = link['expanded_url']
            if any(knownLink in expanded_link for knownLink in knownLinks):
                print expanded_link
                isSong = True
                return isSong

def is_known_artist(handle):
    """
    Checks if artist is in our Known Artists list
    """
    known = False

    # Scan through known twitter handles
    for key in handles.HANDLES:
        knownHandle = handles.HANDLES.get(key).strip('@')
        if handle.lower() == knownHandle.lower():
            print "Known Artist: " + handle
            known = True
    if not known:
        print "Unknown User: " + handle
    return known

if __name__ == '__main__':
    main()
