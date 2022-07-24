from autotag_raindrops import call_raindrop_api
import config

def get_tags_with_count(tag_count_at_or_below=1):
    get_tags = call_raindrop_api(
        api_path='tags',
        error_response=[],
    )
    tags = []
    for tag_obj in get_tags.get('items'):
        tag = tag_obj['_id']
        count = tag_obj['count']
        if count <= tag_count_at_or_below:
            tags += [tag]
    return tags

def delete_tags(tags):
    delete_tags = call_raindrop_api(
        api_path='tags',
        method='DELETE',
        json={'tags': tags}
    )

def generate_tag_list_file(path, bookmark_count=1, print_output_only=False):
    print(f'Generating list of tags in {path} with {bookmark_count} or less bookmark(s)...')
    output = ["tags = ["]
    for tag in get_tags_with_count(bookmark_count):
        output += [(f"    \"{tag}\",")]
    output += [']']
    str_output = ('\n').join(output)
    if print_output_only:
        print(str_output)
    else:
        with open(path, 'w') as f:
                f.write(str_output)

def main():
    tag_count_at_or_below = 1
    generate_tag_list_file(config.raindrop_tags_path, bookmark_count=tag_count_at_or_below)
    if input(f'Delete tags from {config.raindrop_tags_path}? (yes/N)\n> ') == 'yes':
        from tags_list import tags as tags_to_delete
        delete_tags(tags_to_delete)

if __name__ == '__main__':
    main()
