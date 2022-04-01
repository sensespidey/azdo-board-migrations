
"""
Functions relevant to ZenHub/GitHub source.
"""
def query_github_issues(query, config):
    print('Retrieving issues.... ' + query)
    issues = get_github_api(query, config)

    if not issues.status_code == 200:
        raise Exception("Request returned status of:"+str(issues.status_code))
    else:
        return issues

def query_zenhub_issue(repo_name, issue_num, config):
    repo_ID = get_repo_id(repo_name, config)
    ZENHUB_AUTH = config['ZENHUB_AUTH']
    zenhub_issue_url = zenhub_api_base() + f'{repo_ID}/issues/{issue_num}?access_token={ZENHUB_AUTH}'

    print(f'Retrieving ZenHub data for {repo_name}: {issue_num} ({zenhub_issue_url})')
    return requests.get(zenhub_issue_url, verify=False)

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
    return row_dict

def get_repo_id(repo_name, config):
    repo_json = get_github_api(f'repos/{repo_name}', config).json()
    return repo_json['id']

def get_github_api(endpoint, config):
    return get_github_api_raw(github_api_base() + endpoint, config)

def get_github_api_raw(url, config):
    return requests.get(url, auth=config['GITHUB_AUTH'], verify=False)

def github_api_base():
    return 'https://api.github.com/'

def zenhub_api_base():
    return 'https://api.zenhub.io/p1/repositories/'
