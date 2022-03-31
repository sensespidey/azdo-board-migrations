"""
Author: Derek Laventure <derek.laventure@ssc.gc.ca>

Collects issue data from ZenHub/GitHub and generates a CSV suitable for import
into Azure DevOps.

Supports Github API v3 and ZenHubs current working API.
"""
import csv
import datetime
import requests
import configparser

# DEBUG
from rich import print as rprint

def write_issues(r, csvout, repo_name, repo_ID):
    if not r.status_code == 200:
        raise Exception("Request returned status of:"+str(r.status_code))

    r_json = r.json()
    print(str(len(r_json)) + ' issues loaded. Loading ZenHub data...')
    for issue in r_json:
        print(repo_name + ' issue: ' + str(issue['number']))

        zenhub_issue_url = 'https://api.zenhub.io/p1/repositories/' + str(repo_ID) + '/issues/' + str(issue['number']) + '?access_token=' + ACCESS_TOKEN
        zen_r = requests.get(zenhub_issue_url, verify=False).json()

        # DEBUG
        rprint(issue)
        rprint(zen_r)

        DateCreated = issue['created_at'][:-10]
        DateUpdated = issue['updated_at'][:-10]

        # Ignore pull requests, which github treats as issues
        if 'pull_request' in issue:
            continue

        global ISSUES
        ISSUES += 1
        assignees, tag, category, priority, labels = '', '', '', '', ''

        for i in issue['assignees'] if issue['assignees'] else []:
            assignees += i['login'] + ','

        for x in issue['labels'] if issue['labels'] else []:
            if "Category" in x['name']:
                category = x['name'][11:11 + len(x['name'])]
            elif "Tag" in x['name']:
                tag = x['name'][6:6 + len(x['name'])]
            elif "Priority" in x['name']:
                priority = x['name'][11:11 + len(x['name'])]
            else:
                labels += x['name'] + ','

        estimate = zen_r.get('estimate', dict()).get('value', "")

        if issue['state'] == 'closed':
            Pipeline = 'Closed'
        else:
            Pipeline = zen_r.get('pipeline', dict()).get('name', "")

        if not issue.get('body'):
            issue['body'] = ''

        row_dict = {
            #'ID': issue['number'],
            # @TODO: make this depend on is_epic
            'Work Item Type': 'Work Item Type',
            'Title': issue['title'],
            'Description': issue['body'],
            'Tags': tag,
            'Assigned To': assignees[:-1],
            'Priority': priority,
            'State': issue['state'],
            'Created By': issue['user']['login'],
            'Created Date': DateCreated,
            'Changed Date': DateUpdated,
            'Effort': estimate,
            #'Parent': 'Parent',
            'Iteration Path': 'Backlog',
        }
        csvout.writerow(row_dict)

def get_issues(repo_data):
    repo_name = repo_data[0]
    repo_ID = repo_data[1]

    issues_for_repo_url = f'https://api.github.com/repos/{repo_name}/issues?{QUERY}'
    print('Retrieving issues.... ' + issues_for_repo_url)

    # @TODO: wrap this in an iterator
    r = requests.get(issues_for_repo_url, auth=AUTH, verify=False)
    write_issues(r, FILEOUTPUT, repo_name, repo_ID)

    if 'link' in r.headers:
        pages = dict(
            [(rel[6:-1], url[url.index('<') + 1:-1]) for url, rel in
             [link.split(';') for link in
              r.headers['link'].split(',')]])
        # @TODO: wrap this in an iterator?
        # this goes away in the iterator..
        while 'last' in pages and 'next' in pages:
            pages = dict(
                [(rel[6:-1], url[url.index('<') + 1:-1]) for url, rel in
                 [link.split(';') for link in
                  r.headers['link'].split(',')]])
            r = requests.get(pages['next'], auth=AUTH, verify=False)
            write_issues(r, FILEOUTPUT, repo_name, repo_ID)
            if pages['next'] == pages['last']:
                break


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config-gcpboard.ini')

    # Get a list of repos from the config file.
    REPO_LIST = []
    for (repo_name, repo_id) in config.items("REPO_LIST"):
        REPO_LIST.append( (repo_name, repo_id) )

    # Gather credentials
    AUTH = ('token', config['ACCESS']['AUTH_TOKEN'])
    ACCESS_TOKEN = config['ACCESS']['ZEN_ACCESS']

    # See https://developer.github.com/v3/issues/#list-repository-issues
    QUERY = config['ACCESS']['QUERY']

    ISSUES = 0
    FILENAME = config['ACCESS']['FILENAME']

    # @TODO: refactor this common stuff
    # @TODO: move headers into config? or make 
    csv.register_dialect('azdo', 'excel',  doublequote=False, escapechar='\\')
    col_headers = [
        #'ID',
        'Work Item Type',
        'Title',
        #'Title 2',
        'Description',
        'Tags',
        'Assigned To',
        'Priority',
        'State',
        'Created By',
        'Created Date',
        'Changed Date',
        'Effort',
        #'Parent',
        'Iteration Path',
    ]
    # @TODO: use with idiom here (no need to close in that case)
    OPENFILE = open(FILENAME, 'w', newline='\n')
    FILEOUTPUT = csv.DictWriter(OPENFILE, fieldnames=col_headers, dialect='excel', quoting=csv.QUOTE_ALL)
    FILEOUTPUT.writeheader()

    for repo_data in REPO_LIST:
        get_issues(repo_data)

    OPENFILE.close()