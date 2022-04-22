
"""
Functions relevant to ZenHub/GitHub source.
"""

import requests
from lib.common import parse_date

# DEBUG
from rich import print as rprint

def query_github_issues(query, config):
    print('Retrieving issues.... ' + query)
    issues = get_github_api(query, config)
    issues.raise_for_status()

    if not issues.status_code == 200:
        rprint(issues.headers)
        raise Exception("Request returned status of:"+str(issues.status_code))
    else:
        return issues

def query_zenhub_issue(repo_name, issue_num, config):
    repo_ID = get_repo_id(repo_name, config)
    ZENHUB_AUTH = config['ZENHUB_AUTH']
    zenhub_issue_url = zenhub_api_base() + f'{repo_ID}/issues/{issue_num}?access_token={ZENHUB_AUTH}'

    print(f'Retrieving ZenHub data for {repo_name}: {issue_num} ({zenhub_issue_url})')
    return requests.get(zenhub_issue_url, verify=False)

def get_repo_id(repo_name, config):
    repo_json = get_github_api(github_api_base() + f'repos/{repo_name}', config).json()
    return repo_json['id']

def get_github_api(url, config):
    """Takes a full API url and queries it with auth details."""
    return requests.get(url, auth=config['GITHUB_AUTH'], verify=False)

def github_api_base():
    return 'https://api.github.com/'

def zenhub_api_base():
    return 'https://api.zenhub.io/p1/repositories/'

class HubIssues:
    """Iterator class over ZenHub issues"""

    def __init__(self, repo_data, config):
        self.config = config
        self.last_page = False
        self.repo_name = repo_data[0]
        self.iteration = repo_data[1]
        self.area = config['AREA_PATH']
        self.query_url = github_api_base() + f'repos/{self.repo_name}/issues?' + config['QUERY']
        #self.query_url = 'https://api.github.com/repositories/332794551/issues?page=4'

    def __iter__(self):
        return self

    def __next__(self):
        if self.query_url == None:
            raise StopIteration

        # Start by getting the current batch of issues from the API
        print(f"Next iteration: {self.query_url}")
        issues = query_github_issues(self.query_url, self.config)

        # Then loop over them and collect the ZenHub data for each.
        issues_list = []
        for issue in issues.json():
            # Ignore pull requests, which github treats as issues
            if 'pull_request' in issue:
                continue

            # Collect Zenhub details on this issue, in JSON format.
            zen_r = query_zenhub_issue(self.repo_name, issue['number'], self.config).json()

            # process_issue takes the issue object and the zen_r object and creates a sanitized object, keyed by our defined column_headers
            #@TODO: figure out a way to enforce the link between processed fields and column_headers/keys
            print(f'{self.repo_name} issue: ' + str(issue['number']))
            issues_list.append(self.process_issue(issue, zen_r))

        # Now set up the next page of github issues (if any).
        self.set_new_query_url(issues)

        # And return the current list of issues.
        return issues_list

    def process_issue(self, issue, zen_r):
        """Take raw issue data from GitHub and ZenHub API, process into import dictionary format."""
        # DEBUG
        print("Processing issue... " + str(issue['url']))
        rprint(issue)
        rprint(zen_r)

        # Work Item Type
        if ("is_epic" in zen_r and zen_r['is_epic']):
            issue['wit'] = 'Epic'
        else:
            issue['wit'] = 'Product Backlog Item'

        body = ''
        if issue.get('body'):
            body = str(issue['body'])

        # The GitHub API returns the URL in API format, so we convert it to a Web UI link.
        issue['url'] = issue['url'].replace('https://api.github.com/repos', 'https://github.com')
        issue['body'] = body + "\n\nOriginal GitHub issue link: " + str(issue['url'])

        tags = ''
        for x in issue['labels'] if issue['labels'] else []:
            tags += x['name'] + ' , '

        # We can't import a closed issue, but we give it a closed tag so we can manually close it after import.
        Pipeline = zen_r.get('pipeline', dict()).get('name', "")
        print("PIPELINE VALUE: " + Pipeline)
        if Pipeline == 'Closed' or Pipeline == 'Done':
            issue['estimate'] = ''
            tags += 'closed'

        assignees = ''
        for i in issue['assignees'] if issue['assignees'] else []:
            assignees += i['login'] + ','

        return {
            'type': issue['wit'],
            'title': issue['title'][0:255],
            'body': issue['body'],
            'tags': tags,
            # User mappings don't carry over, so we lose assignee and author fields.
            #'assignee': assignees[:-1],
            'assignee': '',
            #'author': issue['user']['login'],
            'author': '',
            'priority': 2,
            # We always set the state to New, since other states don't import correctly.
            'state': 'New',
            'created': parse_date(issue['created_at']),
            'changed': parse_date(issue['updated_at']),
            'effort': zen_r.get('estimate', dict()).get('value', ""),
            'iteration': self.iteration,
            'area': self.area,
            'github': issue['url'],
        }

    def set_new_query_url(self, issues):
        """Take a recent issues request, check for a next page of results to query."""

        # If the link header is missing, we're done.
        if not 'link' in issues.headers:
            self.query_url = None
            return

        # Parse the link header to get a list of pages.
        pages = self.get_pages(issues.headers['link'])

        # If we're already on the last page, we're done.
        if not "next" in pages:
            self.query_url = None
            return

        # Otherwise, request the next url.
        self.query_url = pages['next']

    def get_pages(self, link_header):
        """Parse the link header in the API response to find next/last pages links."""
        return dict(
            [(rel[6:-1], url[url.index('<') + 1:-1]) for url, rel in
                [link.split(';') for link in
                link_header.split(',')]])