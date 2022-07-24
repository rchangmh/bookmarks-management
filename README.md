# Bookmarks Management

## Raindrop Autotagging

The `/autotag_raindrops.py` script iterates through every link in a given [Raindrop](raindrop.io) collection and automatically tags the link with all suggested tags (assuming you are a Pro subscriber). Because the API is throttled to 120 requests a minute, a large collection will take a while to complete.

You will need to add your Raindrop token and collection ID to `/config.py`. You can get the collection ID from the URL on the Raindrop web app.

Before running, create `/config.py` file (in the root directory) with the following:

```
test_token = 'xxxxx'
collection_ids = ['unsorted', '1234567']
start_page = 0
```

## Raindrop Tag Management

Tagging Raindrops with all suggested tags will result in _a lot_ of tags. You can use the `/manage_tags.py` script to clear out all tags with _n_ bookmarks.

Add the following to `/config.py`:

```
raindrop_tags_path = './tags_list.py'
```

## Pocket Management

The `/manage_pocket.py` script helps clear out your unread [Pocket](https://getpocket.com/) queue: removing duplicates, filtering on domain, word count, and/or age. Add the following to `/config.py` and run the script in a REPL:

```
pocket_consumer_key = 'xxxxx'
pocket_access_token = 'xxxxx'
pocket_links_path = './pocket_articles.json'
```
