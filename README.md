# Quotes Indonesia

<img src="logo.png" width="150px"/>

Long story short, i have a quote posting social media page on facebook, twitter, telegram, and instagram.

This is tools i used to manage those social medias, including scheduling, autopost, and quote image maker.

## Raw Quotes

You can download raw quote resources on [`raw`](raw) folder.

## Social Media Tagline

Kami menyebarkan quote motivasi dari tokoh - tokoh dunia yang menyegarkan dan menggerakkan jiwa untuk berubah bersama menuju kebaikan.

* Facebook: https://fb.me/indonesiaquotes
* Twitter: https://twitter.com/quotes_idn
* Instagram: https://instagram.com/quotes_idna
* Telegram: https://t.me/quotesindonesia

## My Notes

### Running Script

1. Goto directory `scripts/autopost`
2. Setup environment variable, see `scripts/autopost/.env.sample.sh`
3. Install python dependencies `pip install -r requirements.txt`
4. Run autopost with `python autopost.py`

### Getting token

* For facebook page, get `pages_show_list`, `pages_read_engagement`, and `pages_manage_posts` permission
* For instagram, get `instagram_basic` and `instagram_content_publish` permission