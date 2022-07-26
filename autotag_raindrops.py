from raindropio import API, Collection, CollectionRef, Raindrop
import requests
import time
import config

token = config.raindrop_test_token
api = API(token)

def call_raindrop_api(api_path, id='', error_response={}, method='GET', json=None):
    headers = {'Authorization': f'Bearer {token}'}
    try:
        if method == 'PUT':
            response = requests.put(f'https://api.raindrop.io/rest/v1/{api_path}/{id}', headers=headers, json=json)
        elif method == 'DELETE':
            response = requests.delete(f'https://api.raindrop.io/rest/v1/{api_path}/{id}', headers=headers, json=json)
        elif method == 'POST':
            response = requests.post(f'https://api.raindrop.io/rest/v1/{api_path}', headers=headers, json=json)
        else:
            response = requests.get(f'https://api.raindrop.io/rest/v1/{api_path}/{id}', headers=headers)
        if response.status_code == 429:
            retry_time = int(response.headers['Retry-After']) + 5
            print(f'\nToo many requests, retrying in {retry_time}...\n')
            time.sleep(retry_time)
            return call_raindrop_api(method, api_path, id, error_response)
        elif response.status_code == 404:
            print(f'    Got 404 for: https://app.raindrop.io/my/0/item/{id}')
            # print(f'\nrequests.get("https://api.raindrop.io/rest/v1/{api_path}/{raindrop_id}", headers={headers})\n')
            return error_response
        return response.json()
    except Exception as error:
        print(f'    Error calling {api_path}, {id}: {error}')
        # print(f'\nrequests.get("https://api.raindrop.io/rest/v1/{api_path}/{raindrop_id}", headers={headers})\n')
        return error_response

def get_collection(name, return_object=False):
    collections = call_raindrop_api(
        api_path='collections',
    ).get('items')
    for collection in collections:
        if collection.get('title') == name:
            if return_object:
                return Collection.get(api, collection['_id'])
            else:
                return {'$id': collection['_id']} # Format for assigning collection to raindrop.
    return None

def get_suggested_tags(raindrop_id):
    suggested_tags = call_raindrop_api(
        api_path='tags/suggest', 
        id=raindrop_id,
        error_response={}
    ).get('tags', [])
    suggested_tags = list(filter(lambda tag: len(tag) < 30, suggested_tags))
    return suggested_tags

def tag_raindrop(raindrop_id, tags=[]):
    current_tags = call_raindrop_api(
        api_path='raindrop',
        id=raindrop_id,
        error_response={}
    ).get('item', {}).get('tags', [])
    return call_raindrop_api(
        api_path='raindrop',
        id=raindrop_id,
        error_response=None,
        method='PUT',
        json={'tags': tags + current_tags}
    )

def if_need_tags(raindrop_id, less_than):
    tags = call_raindrop_api(
        api_path='raindrop',
        id=raindrop_id,
        error_response={}
    ).get('item', {}).get('tags', [])
    return len(tags) < less_than

def main(collection_ids=[], start_page=0):
    print('Tagging bookmarks in your Raindrop collection.\n')
    collection_id = input(f'Target collection ID: (default: {collection_ids})\n> ')
    collection_ids = [collection_id] if collection_id else collection_ids
    start_page = int(str(input(f'Start page from: (current: {start_page})\n> ')) or str(start_page))
    tag_threshold = int(input(f'Tag threshold: (default: 3)\n> ') or 0) or 3
    print(f'\nTagging links with less than {tag_threshold} tag(s) in collections: {collection_ids}, starting at page {start_page}...\n')
    for i, collection_id in enumerate(collection_ids):
        if collection_id == 'unsorted':
            collection = CollectionRef.Unsorted
        else:
            collection = Collection.get(api, collection_id)
        page = start_page if i == 0 else 0
        while (items := Raindrop.search(api, collection=collection, page=page)):
            print(f'\nID: {collection_id} | PAGE: {page}\n')
            for index, item in enumerate(items):
                try:
                    need_tags = if_need_tags(item.id, less_than=tag_threshold)
                    if need_tags:
                        try:
                            print(f'+ {item.title}')
                        except Exception as error:
                            print(f' + ___ {error}')
                        suggested_tags = get_suggested_tags(item.id)
                        if suggested_tags:
                            print(f'    {suggested_tags}')
                            tag_raindrop(item.id, suggested_tags)
                except Exception as error:
                    print(f'Issues with https://app.raindrop.io/my/0/item/{item.id}, {error}, skipping...')
            page += 1

if __name__ == '__main__':
    main(
        config.raindrop_collection_ids, 
        config.collection_start_page,
    )