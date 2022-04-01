"""
Functions common to all sources.
"""
import configparser

def get_config():
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Get a list of repos from the config file.
    REPO_LIST = []
    for (repo_name, repo_id) in config.items("HUB_REPO_LIST"):
        REPO_LIST.append( (repo_name, repo_id) )

    return {
        'REPO_LIST': REPO_LIST,

        # See https://developer.github.com/v3/issues/#list-repository-issues
        'QUERY': config.get('HUB_ACCESS', 'QUERY'),

        # Gather credentials
        'GITHUB_AUTH': ('token', config.get('HUB_ACCESS', 'GITHUB_AUTH')),
        'ZENHUB_AUTH': config.get('HUB_ACCESS', 'ZENHUB_AUTH'),

        # Output file
        'FILENAME': config.get('OUTPUT', 'FILENAME'),
    }

def get_column_headers():
    return {
        'type': 'Work Item Type',
        'title': 'Title',
        'body': 'Description',
        'tags': 'Tags',
        'assignee': 'Assigned To',
        'priority': 'Priority',
        'state': 'State',
        'author': 'Created By',
        'created': 'Created Date',
        'changed': 'Changed Date',
        'effort': 'Effort',
        'iteration': 'Iteration Path'
    }

def hub_row_data(issue, tags, assignees, priority, DateCreated, DateUpdated, estimate):
    row_dict = {
        'type': 'Epic' if ("is_epic" in issue and issue['is_epic']) else 'Product Backlog Item',
        'title': issue['title'],
        # @TODO: append a link back to GitHub issue to description
        'body': str(issue['body']) + "\n\nOriginal GitHub issue link: " + str(issue['url']),
        'tags': tags,
        'assignee': assignees[:-1],
        'priority': priority,
        'state': issue['state'],
        'author': issue['user']['login'],
        'created': DateCreated,
        'changed': DateUpdated,
        'effort': estimate,
        'iteration': 'ISSUE IMPORT TEST PROJECT'
    }
    return prepare_row(row_dict)

def prepare_row(row_dict):
    row = {}
    for key,title in get_column_headers().items():
        row[title] = row_dict[key]
    return row