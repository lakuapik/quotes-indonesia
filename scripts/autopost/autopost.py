import os
import json
import requests
from pydash import py_
from twython import Twython
from datetime import datetime
from image_maker import image_maker_make_file


FB_PAGE_ID = os.environ.get('FB_PAGE_ID')
FB_OAUTH_TOKEN = os.environ.get('FB_OAUTH_TOKEN')

TG_BOT_CHANNEL = os.environ.get('TG_BOT_CHANNEL')
TG_BOT_TOKEN = os.environ.get('TG_BOT_TOKEN')

TW_API_KEY = os.environ.get('TW_API_KEY')
TW_API_SECRET = os.environ.get('TW_API_SECRET')
TW_OAUTH_TOKEN = os.environ.get('TW_OAUTH_TOKEN')
TW_OAUTH_SECRET = os.environ.get('TW_OAUTH_SECRET')

IG_ACCOUNT_ID = os.environ.get('IG_ACCOUNT_ID')
IG_OAUTH_TOKEN = os.environ.get('IG_OAUTH_TOKEN')


quotes_file = open('quotes.json', 'r+')
quotes = json.loads(quotes_file.read())
unposted_quotes = py_.filter(quotes, lambda q: (
    # q['posted_facebook_at'] == ''
    # and q['posted_instagram_at'] == ''
    q['posted_telegram_at'] == ''
    and q['posted_twitter_at'] == ''
))


def should_post_as_image() -> bool:
    # when today date is divisible by 5
    return int(datetime.now().strftime('%d')) % 5 == 0


def post_to_telegram_as_text(text: str) -> bool:
    tg_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage?"
    tg_url += f"text={requests.utils.quote(text)}"
    tg_url += f"&chat_id={TG_BOT_CHANNEL}"
    response = requests.get(tg_url)

    return response.status_code == 200


def post_to_telegram_as_image(image_path: str) -> bool:
    tg_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto"
    response = requests.post(
        url=tg_url,
        data={'chat_id': TG_BOT_CHANNEL},
        files={'photo': open(image_path, 'rb')}
    )

    return response.status_code == 200


def post_to_facebook_as_text(text: str) -> bool:
    fb_url = f"https://graph.facebook.com/{FB_PAGE_ID}/feed"
    response = requests.post(fb_url, {
        'message': text,
        'access_token': FB_OAUTH_TOKEN,
    })

    return response.status_code == 200


def post_to_facebook_as_image(image_path: str) -> bool:
    fb_url = f"https://graph.facebook.com/{FB_PAGE_ID}/photos"
    response = requests.post(
        url=fb_url,
        data={'access_token': FB_OAUTH_TOKEN},
        files={'source': open(image_path, 'rb')}
    )

    return response.status_code == 200


def post_to_twitter_as_text(text: str) -> bool:
    tags = '#quotesindonesia #qotdindonesia #kutipan #motivasi #inspirasi'
    twitr = Twython(TW_API_KEY, TW_API_SECRET, TW_OAUTH_TOKEN, TW_OAUTH_SECRET, client_args={'timeout': 10})
    text_with_hastag = f'{text}\n\n{tags}'
    tweet = twitr.update_status(status=text_with_hastag[0:280])

    return tweet.get('created_at') is not None


def post_to_twitter_as_image(image_path: str) -> bool:
    twitr = Twython(TW_API_KEY, TW_API_SECRET, TW_OAUTH_TOKEN, TW_OAUTH_SECRET, client_args={'timeout': 10})
    media = twitr.upload_media(media=open(image_path, 'rb'))
    tweet = twitr.update_status(media_ids=[media['media_id']])

    return tweet.get('created_at') is not None


def post_to_instagram(image_path: str) -> bool:
    files = {'files[]': open(image_path, 'rb')}
    image_uploaded = requests.post('https://tmp.ninja/upload.php', files=files)
    if image_uploaded.status_code != 200:
        return False
    image_url = image_uploaded.json()['files'][0]['url']
    ig_base_url = f"https://graph.facebook.com/{IG_ACCOUNT_ID}"
    caption = '#quotes_idna #quotesindonesia #qotdindonesia #katakatabijak #katatokoh #kutipan #motivasi #inspirasi'
    response_post = requests.post(f"{ig_base_url}/media", {
        'image_url': image_url,
        'caption': caption,
        'access_token': IG_OAUTH_TOKEN,
    })
    if response_post.status_code != 200:
        return False
    creation_id = response_post.json()['id']
    response_publish = requests.post(f"{ig_base_url}/media_publish", {
        'creation_id': creation_id,
        'access_token': IG_OAUTH_TOKEN,
    })

    return response_publish.status_code == 200


def rewrite_quotes_file() -> None:
    quotes_file.seek(0)
    quotes_file.write(json.dumps(quotes, indent=2))
    quotes_file.truncate()


def autopost() -> None:
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
    # post_ig = post_to_instagram(image_path)
    # if post_ig:
    #     py_.set(quotes, f"{quote_index}.posted_instagram_at", now)
    # print(f"\n> posted to instagram as text: {post_ig}")

    if (should_post_as_image()):
        post_tg = post_to_telegram_as_image(image_path)
        if post_tg:
            py_.set(quotes, f"{quote_index}.posted_telegram_at", now)
        print(f"\n> posted to telegram as image: {post_tg}")

        # post_fb = post_to_facebook_as_image(image_path)
        # if post_fb:
        #     py_.set(quotes, f"{quote_index}.posted_facebook_at", now)
        # print(f"\n> posted to facebook as image: {post_fb}")

        post_tw = post_to_twitter_as_image(image_path)
        if post_tw:
            py_.set(quotes, f"{quote_index}.posted_twitter_at", now)
            print(f"\n> posted to twitter as image: {post_tw}")

    else:  # as text
        post_tg = post_to_telegram_as_text(formatted_quote)
        if post_tg:
            py_.set(quotes, f"{quote_index}.posted_telegram_at", now)
        print(f"\n> posted to telegram as text: {post_tg}")

        # post_fb = post_to_facebook_as_text(formatted_quote)
        # if post_fb:
        #     py_.set(quotes, f"{quote_index}.posted_facebook_at", now)
        # print(f"\n> posted to facebook as text: {post_fb}")

        post_tw = post_to_twitter_as_text(formatted_quote)
        if post_tw:
            py_.set(quotes, f"{quote_index}.posted_twitter_at", now)
        print(f"\n> posted to twitter as text: {post_tw}")

    rewrite_quotes_file()

    print(f"\n> done")


if __name__ == "__main__":
    autopost()
    quotes_file.close()
