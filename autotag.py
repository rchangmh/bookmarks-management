from raindropio import API, Collection, CollectionRef, Raindrop
import requests
import time
import config

token = config.test_token
api = API(token)

def call_raindrop_api(api_path, raindrop_id, error_response, method='GET', json=None):
    headers = {'Authorization': f'Bearer {token}'}
    try:
        if method == 'PUT':
            response = requests.put(f'https://api.raindrop.io/rest/v1/{api_path}/{raindrop_id}', headers=headers, json=json)
        else:
            response = requests.get(f'https://api.raindrop.io/rest/v1/{api_path}/{raindrop_id}', headers=headers)
        if response.status_code == 429:
            retry_time = int(response.headers['Retry-After'])
            print(f'Too many requests, retrying in {retry_time}...')
            time.sleep(retry_time)
            return call_raindrop_api(method, api_path, raindrop_id, error_response)
        elif response.status_code == 404:
            print(f'Got 404 for: https://app.raindrop.io/my/0/item/{raindrop_id}')
            # print(f'\nrequests.get("https://api.raindrop.io/rest/v1/{api_path}/{raindrop_id}", headers={headers})\n')
            return error_response
        return response.json()
    except Exception as error:
        print(f'Error calling {api_path}, {raindrop_id}: {error}')
        # print(f'\nrequests.get("https://api.raindrop.io/rest/v1/{api_path}/{raindrop_id}", headers={headers})\n')
        return error_response

def get_suggested_tags(raindrop_id):
    return call_raindrop_api(
        api_path='tags/suggests', 
        raindrop_id=raindrop_id,
        error_response={}
    ).get('tags', [])

def tag_raindrop(raindrop_id, tags=[]):
    return call_raindrop_api(
        api_path='raindrop',
        raindrop_id=raindrop_id,
        error_response=None,
        method='PUT',
        json={'tags': tags}
    )

def if_need_tags(raindrop_id, less_than=2):
    tags = call_raindrop_api(
        api_path='raindrop',
        raindrop_id=raindrop_id,
        error_response={}
    ).get('item', {}).get('tags', [])
    return len(tags) < less_than

def main():
    collection = Collection.get(api, '26107681')
    # collection = CollectionRef.Unsorted
    page = 0
    # items = Raindrop.search(api, collection=collection, page=page)
    while (items := Raindrop.search(api, collection=collection, page=page)):
        print(f'PAGE {page}:')
        for index, item in enumerate(items):
            try:
                need_tags = if_need_tags(item.id)
                if need_tags:
                    print(f'+ {index}: {item.title}')
                    suggested_tags = get_suggested_tags(item.id)
                    if suggested_tags:
                        print(f'  {suggested_tags}')
                        tag_raindrop(item.id, suggested_tags)
            except Exception as error:
                print(f'Issues with https://app.raindrop.io/my/0/item/{item.id}, {error}, skipping...')
        page += 1

main()