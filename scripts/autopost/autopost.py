import os
import json
import tweepy
import requests
from pydash import py_
from datetime import datetime
from image_maker import image_maker_make_file


FB_PAGE_ID = os.environ.get('FB_PAGE_ID')
FB_OAUTH_TOKEN = os.environ.get('FB_OAUTH_TOKEN')

TG_BOT_CHANNEL = os.environ.get('TG_BOT_CHANNEL')
TG_BOT_TOKEN = os.environ.get('TG_BOT_TOKEN')

TW_CONSUMER_KEY = os.environ.get('TW_CONSUMER_KEY')
TW_CONSUMER_SECRET = os.environ.get('TW_CONSUMER_SECRET')
TW_ACCESS_TOKEN = os.environ.get('TW_ACCESS_TOKEN')
TW_ACCESS_TOKEN_SECRET = os.environ.get('TW_ACCESS_TOKEN_SECRET')

IG_ACCOUNT_ID = os.environ.get('IG_ACCOUNT_ID')
IG_OAUTH_TOKEN = os.environ.get('IG_OAUTH_TOKEN')


def should_post_as_image() -> bool:
    # when today date is divisible by 5
    return int(datetime.now().strftime('%d')) % 5 == 0


def twitter_api_v1():
    auth = tweepy.OAuth1UserHandler(TW_CONSUMER_KEY, TW_CONSUMER_SECRET)
    auth.set_access_token(TW_ACCESS_TOKEN, TW_ACCESS_TOKEN_SECRET)
    return tweepy.API(auth)


def twitter_client_v2():
    return tweepy.Client(
        consumer_key=TW_CONSUMER_KEY, consumer_secret=TW_CONSUMER_SECRET,
        access_token=TW_ACCESS_TOKEN, access_token_secret=TW_ACCESS_TOKEN_SECRET
      )


def post_to_telegram_as_text(text: str) -> bool:
    print("\n>>> telegram: posting as text...")
    try:
        tg_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage?"
        tg_url += f"text={requests.utils.quote(text)}"
        tg_url += f"&chat_id={TG_BOT_CHANNEL}"
        response = requests.get(tg_url)
        success = response.status_code == 200
        if not success:
            print(">>> error: failed to post")
            print(f">>> response: {response.text}")
        return success
    except:
        return False


def post_to_telegram_as_image(image_path: str) -> bool:
    print("\n>>> telegram: posting as image...")
    try:
        tg_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto"
        response = requests.post(
            url=tg_url,
            data={'chat_id': TG_BOT_CHANNEL},
            files={'photo': open(image_path, 'rb')}
        )
        success = response.status_code == 200
        if not success:
            print(">>> error: failed to post")
            print(f">>> response: {response.text}")
        return success
    except: 
        return False


def post_to_facebook_as_text(text: str) -> bool:
    print("\n>>> facebook: posting as text...")
    try:
        fb_url = f"https://graph.facebook.com/{FB_PAGE_ID}/feed"
        response = requests.post(fb_url, {
            'message': text,
            'access_token': FB_OAUTH_TOKEN,
        })
        success = response.status_code == 200
        if not success:
            print(">>> error: failed to post")
            print(f">>> response: {response.text}")
        return success
    except:
        return False


def post_to_facebook_as_image(image_path: str) -> bool:
    print("\n>>> facebook: posting as image...")
    try:
        fb_url = f"https://graph.facebook.com/{FB_PAGE_ID}/photos"
        response = requests.post(
            url=fb_url,
            data={'access_token': FB_OAUTH_TOKEN},
            files={'source': open(image_path, 'rb')}
        )
        success = response.status_code == 200
        if not success:
            print(">>> error: failed to post")
            print(f">>> response: {response.text}")
        return success
    except:
        return False


def post_to_twitter_as_text(text: str) -> bool:
    print("\n>>> twitter: posting as text...")
    try:
        tags = '#quotesindonesia #qotdindonesia #kutipan #motivasi #inspirasi'
        text_with_hastag = f'{text}\n\n{tags}'
        v2 = twitter_client_v2()
        tweet = v2.create_tweet(text=text_with_hastag[0:280])
        success = tweet.data['id'] is not None
        if not success:
            print(">>> error: failed to post")
            print(f">>> response: {tweet}")
        return success
    except:
        return False


def post_to_twitter_as_image(image_path: str) -> bool:
    print("\n>>> twitter: posting as image...")
    try:
        v1 = twitter_api_v1()
        v2 = twitter_client_v2()
        media = v1.media_upload(filename=image_path)
        tweet = v2.create_tweet(media_ids=[media.media_id])
        success = tweet.data['id'] is not None
        if not success:
            print(">>> error: failed to post")
            print(f">>> response: {response.text}")
        return success 
    except:
        return False  


def post_to_instagram(image_path: str) -> bool:
    print("\n>>> instagram: posting...")
    try:
        files = {'file': open(image_path, 'rb')}
        image_uploaded = requests.post('https://tmpfiles.org/api/v1/upload', files=files)
        if image_uploaded.status_code != 200:
            print(">>> error: failed to upload to tmpfiles.org")
            print(f">>> response: {image_uploaded.text}")
            return False
        image_url = image_uploaded.json()['data']['url']
        image_url = image_url[:21] + 'dl/' + image_url[21:]
        ig_base_url = f"https://graph.facebook.com/v18.0/{IG_ACCOUNT_ID}"
        caption = '#quotes_idna #quotesindonesia #qotdindonesia #katakatabijak #katatokoh #kutipan #motivasi #inspirasi'
        response_post = requests.post(f"{ig_base_url}/media", {
            'image_url': image_url,
            'caption': caption,
            'access_token': IG_OAUTH_TOKEN,
        })
        if response_post.status_code != 200:
            print(">>> error: failed to create post")
            print(f">>> response: {response_post.text}")
            return False
        creation_id = response_post.json()['id']
        response_publish = requests.post(f"{ig_base_url}/media_publish", {
            'creation_id': creation_id,
            'access_token': IG_OAUTH_TOKEN,
        })
        success_publish = response_publish.status_code == 200
        if not success_publish:
            print(">>> error: failed to publish post")
            print(f">>> response: {response_publish.text}")
        return success_publish
    except:
        return False


def autopost() -> None:
    #
    quotes_file = open('quotes.json', 'r+')
    quotes = json.loads(quotes_file.read())
    unposted_quotes = py_.filter(quotes, lambda q: (
        q['posted_facebook_at'] == ''
        and q['posted_instagram_at'] == ''
        and q['posted_telegram_at'] == ''
        and q['posted_twitter_at'] == ''
    ))

    print(f"\n> available {len(unposted_quotes)}/{len(quotes)}")

    now = datetime.utcnow().isoformat()
    quote = py_.sample(unposted_quotes)  # random
    quote_index = py_.find_index(quotes, lambda q: q['id'] == quote['id'])

    formatted_quote = f"{quote['quote']} --{quote['by']}"
    print(f"\n> chosen: id={quote['id']} \n>> {formatted_quote}")

    # note: using bytesio for multiple times wont work, dont know why
    # so we use image_path instead of image as bytesio
    image_path = image_maker_make_file(quote['by'], quote['quote'])

    # for instagram, always post as image
    post_ig = post_to_instagram(image_path)
    if post_ig:
        py_.set(quotes, f"{quote_index}.posted_instagram_at", now)
    print(f"\n> posted to instagram as text: {post_ig}")

    if (should_post_as_image()):
        #
        post_tg = post_to_telegram_as_image(image_path)
        if post_tg:
            py_.set(quotes, f"{quote_index}.posted_telegram_at", now)
        print(f"\n> posted to telegram as image: {post_tg}")

        post_fb = post_to_facebook_as_image(image_path)
        if post_fb:
            py_.set(quotes, f"{quote_index}.posted_facebook_at", now)
        print(f"\n> posted to facebook as image: {post_fb}")

        post_tw = post_to_twitter_as_image(image_path)
        if post_tw:
            py_.set(quotes, f"{quote_index}.posted_twitter_at", now)
            print(f"\n> posted to twitter as image: {post_tw}")

    else:  # as text
        #
        post_tg = post_to_telegram_as_text(formatted_quote)
        if post_tg:
            py_.set(quotes, f"{quote_index}.posted_telegram_at", now)
        print(f"\n> posted to telegram as text: {post_tg}")

        post_fb = post_to_facebook_as_text(formatted_quote)
        if post_fb:
            py_.set(quotes, f"{quote_index}.posted_facebook_at", now)
        print(f"\n> posted to facebook as text: {post_fb}")

        post_tw = post_to_twitter_as_text(formatted_quote)
        if post_tw:
            py_.set(quotes, f"{quote_index}.posted_twitter_at", now)
        print(f"\n> posted to twitter as text: {post_tw}")

    # rewrite quotes file
    quotes_file.seek(0)
    quotes_file.write(json.dumps(quotes, indent=2))
    quotes_file.truncate()

    print(f"\n> done")

    quotes_file.close()


if __name__ == "__main__":
    autopost()
