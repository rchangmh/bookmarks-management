import json
import datetime
import config
import requests
from autotag_raindrops import call_raindrop_api, get_collection

def pretty_print(obj):
    print(json.dumps(obj, indent=2))

def call_pocket_api(path='get', add_body={}):
    rest_url = f'https://getpocket.com/v3/{path}'
    headers = {'Content-Type': 'application/json'}
    body = {
        'consumer_key': config.pocket_consumer_key,
        'access_token': config.pocket_access_token,
    }
    if path == 'get':
        body = body | {
            'state': 'unread',
            'contentType': 'article',
            'sort': 'newest',
            'detailType': 'simple'
        }
    else:
        body = body | add_body
    r = requests.post(rest_url, headers=headers, json=body)
    return r.json()

def write_articles_json(articles):
    with open(config.pocket_links_path, 'w') as outfile:
        json.dump(articles, outfile)

def get_duplicates():
    with open(config.pocket_links_path, 'r') as readfile:
        jsonfile = json.loads(readfile.read())
    articles = jsonfile['list'].values()
    article_url_set = set()
    duplicate_article_ids = []
    for article in articles:
        article_url = article['resolved_url']
        if article_url in article_url_set:
            duplicate_article_ids += [article['item_id']]
        article_url_set.add(article_url)
    print(f'Unique: {str(len(article_url_set))}')
    print(f'Duplicates: {str(len(duplicate_article_ids))}')
    return duplicate_article_ids

def delete_articles(article_ids):
    actions_list = []
    for article_id in article_ids:
        actions_list += [{
            'action': 'delete', 
            'item_id': article_id,
        }]
    if len(actions_list) > 0:
        r = call_pocket_api(
            path='send',
            add_body={'actions': actions_list},
        )
        print('Deleting...')
        pretty_print(actions_list)
        pretty_print(r)
        refresh_articles_json()
        
def refresh_articles_json():
    write_articles_json(call_pocket_api())

def read_articles_json(filepath):
    with open(filepath, 'r') as readfile:
        articles_json = json.loads(readfile.read())['list']
    return articles_json

def create_raindrop(url, tag, title=None, collection=None):
    raindrop = { 
        'link': url,
        'title': title,
    }
    if collection:
        raindrop = raindrop | { 'collection': collection }
    if tag:
        raindrop = raindrop | { 'tags': [tag] }
    if url == title or title == None or title.startswith('http'):
        raindrop.pop('title')
    return raindrop

def print_article_info(article={}, article_id=None, articles_json={}, collection=None, tag=None, silent=False):
    if article_id:
        article = articles_json[list(filter(lambda key: article_id == key, articles_json.keys()))[0]]
    url = article.get('given_url')
    title = article.get('given_title','').strip() or url
    try:
        if not silent:
            print(f'{title}\n{url}\n')
            return create_raindrop(title=title, url=url, tag=tag, collection=collection)
    except:
        if not silent:
            print(f'{url}\n{url}\n')
            return create_raindrop(url=url, tag=tag, collection=collection)

def print_article_count():
    articles_json = read_articles_json(config.pocket_links_path)
    print(f'Total: {len(articles_json)}')

def filter_by_wordcount(greater_than=80000, less_than=130, return_separate=False, print_output=True):
    greater_than_ids = []
    less_than_ids = []
    articles_json = read_articles_json(config.pocket_links_path)
    for i, article_id in enumerate(articles_json):
        article = articles_json[article_id]
        word_count = int(article.get('word_count', -1))
        if (word_count < less_than or word_count > greater_than) and print_output:
            print_article_info(article)
        if word_count < less_than:
            less_than_ids += [article_id]
        elif word_count > greater_than:
            greater_than_ids += [article_id]
    print(f'Greater than {greater_than}: {len(greater_than_ids)}')
    print(f'Less than {less_than}: {len(less_than_ids)}')
    if return_separate:
        return {
            'greater_than_ids': greater_than_ids,
            'less_than_ids': less_than_ids,
        }
    return greater_than_ids + less_than_ids

def filter_by_domains(filter_domains=[], print_output=True):
    domains = {}
    filtered_domains = {}
    output_ids = []
    articles_json = read_articles_json(config.pocket_links_path)
    for i, article_id in enumerate(articles_json):
        article = articles_json[article_id]
        domain = article.get('domain_metadata', {}).get('name')
        if domain in domains.keys():
            domains[domain] += 1
            if domain in filter_domains:
                if filtered_domains.get(domain):
                    filtered_domains[domain] += 1
                else:
                    filtered_domains[domain] = 1
        else:
            domains[domain] = 1
        if domain in filter_domains:
            if print_output:
                print_article_info(article)
            output_ids += [article_id]
    sorted_domains = dict(sorted(domains.items(), reverse=True, key=lambda item: item[1]))
    if filter_domains:
        pretty_print(filtered_domains)
    else:
        pretty_print(sorted_domains)
    return output_ids

def get_timestamp_from_days_ago(days):
    return (datetime.datetime.now() - datetime.timedelta(days=days)).timestamp()

def filter_older_than_days(days=365, print_output=True):
    output_ids = []
    days = int(days)
    articles_json = read_articles_json(config.pocket_links_path)
    for i, article_id in enumerate(articles_json):
        article = articles_json[article_id]
        # added_timestamp = float(article['time_added'])
        added_timestamp = float(article['time_updated'])
        if added_timestamp < get_timestamp_from_days_ago(days):
            output_ids += [article_id]
            if print_output:
                print_article_info(article)
    print(f'Articles added {days} days ago: {len(output_ids)}')
    return output_ids

def filter_out_favorites():
    output_ids = []
    favorite_count = 0
    non_favorite_count = 0
    articles_json = read_articles_json(config.pocket_links_path)
    for i, article_id in enumerate(articles_json):
        article = articles_json[article_id]
        favorited = article['favorite'] == '1'
        if not favorited:
            output_ids += [article_id]
            non_favorite_count += 1
        else:
            favorite_count += 1
    print(f'Favorites: {favorite_count}\nOther: {non_favorite_count}')
    return output_ids

def matching_all_lists(*lists):
    matching_items = []
    for item in lists[0]:
        matching_count = 0
        for other_list in lists[1:]:
            if item in other_list:
                matching_count += 1
        if matching_count == len(lists[1:]):
            matching_items += [item]
    print(f'Matching: {len(matching_items)}')
    return matching_items

def archive_to_raindrop(raindrops):
    max_items = 100
    responses = []
    while len(raindrops) > 0:
        responses += [call_raindrop_api(
            api_path='raindrops',
            method='POST',
            json={'items': raindrops[0:max_items]},
        )]
        del raindrops[0:max_items]
    return responses

def main():
    refresh = input(f'\nIs "{config.pocket_links_path}" up to date? (Y/n)\n> ') == 'n'
    if refresh:
        print('Fetching updated articles...')
        refresh_articles_json()
    filters = []
    if input('\nRemove duplicates only? (y/N)\n> ')== 'y':
        duplicate_ids = get_duplicates()
        if input('\nDelete duplicates? (yes/N)\n> ') == 'yes':
            delete_articles(duplicate_ids)
            return
    if (input('\nOnly include non-favorited articles? (Y/n)\n> ') or 'y') == 'y':
        filters += [filter_out_favorites()]
    if input('\nRemove articles by age? (y/N)\n> ') == 'y':
        default_days = int(365*2.5)
        age = int(input(f'\nHow many days? ({default_days})\n> ') or default_days)
        filters += [filter_older_than_days(days=age, print_output=False)]
    if input('\nRemove articles based on domain? (y/N)\n> ') == 'y':
        filter_by_domains()
        default_domains = ['The Economist', 'The New York Times', 'Bloomberg']
        domains = input(f'\nWhich domains? (sep = \',\')\n(Defaults: {default_domains})\n> ').split(',')
        domains = default_domains if domains == [''] else [domain.strip() for domain in domains]
        filters += [filter_by_domains(domains, print_output=False)]
    if input('\nFilter by article wordcount? (y/N)\n> ') == 'y':
        filters += [filter_by_wordcount(
            # greater_than=int(input('\nArticles with word counts greater than? (50000)\n> ') or 50000),
            less_than=int(input('\nArticles with word counts less than? (250)\n> ') or 250),
            print_output=False,
        )]
    matching_article_ids = matching_all_lists(*filters)
    if (input('\nPrint and export all matching articles? (Y/n)\n> ') or 'y') == 'y':
        raindrops = []
        print(f'Pocket IDs: {matching_article_ids}\n')
        collection = get_collection('Pocket Archive')
        articles_json = read_articles_json(config.pocket_links_path)
        for article_id in matching_article_ids:
            raindrops += [print_article_info(
                article_id=article_id,
                collection=collection,
                articles_json=articles_json,
                tag='pocket-export',
            )]
        if (input('\nArchive articles to Raindrop.io? (Y/n)\n> ') or 'y') == 'y':
            print(f'Archiving {len(raindrops)} links...')
            archive_responses = archive_to_raindrop(raindrops=raindrops)
            print(f'Complete: {archive_responses[0].get("result")}')
            if input('\nPrint response? (y/N)\n> ') == 'y':
                try:
                    pretty_print(archive_responses)
                except Exception as error:
                    print(error)
    if input('\nDelete articles? (yes/N)\n> ') == 'yes':
        delete_articles(matching_article_ids)
    return

if __name__ == '__main__':
    main()