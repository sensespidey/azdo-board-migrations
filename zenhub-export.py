"""
Originally from: https://gist.github.com/unbracketed/3380407
Exports Issues from a specified repository to a CSV file
Uses basic authentication (Github username + password) to retrieve Issues
from a repository that username has access to. Supports Github API v3.


Post here: https://github.com/ZenHubIO/support/issues/1070

Usage:

Add the following to config.ini with appropriate values:

[ACCESS]
AUTH_TOKEN =
ZEN_ACCESS =
QUERY = # See https://developer.github.com/v3/issues/#list-repository-issues
FILENAME = 


Exports Issues from a list of repositories to individual CSV files
Uses basic authentication (Github API Token and Zenhub API Token)
to retrieve Issues from a repository that token has access to.
Supports Github API v3 and ZenHubs current working API.
Derived from https://gist.github.com/Kebiled/7b035d7518fdfd50d07e2a285aff3977
@PinnaclePSM Author Jamie Belcher
"""
import csv
import datetime
import requests
import configparser

def write_issues(r, csvout, repo_name, repo_ID):
    if not r.status_code == 200:
        raise Exception("Request returned status of:"+str(r.status_code))

    r_json = r.json()
    print(str(len(r_json)) + ' issues loaded. Loading ZenHub data...')
    for issue in r_json:
        print(repo_name + ' issue: ' + str(issue['number']))

        zenhub_issue_url = 'https://api.zenhub.io/p1/repositories/' + str(repo_ID) + '/issues/' + str(issue['number']) + '?access_token=' + ACCESS_TOKEN
        zen_r = requests.get(zenhub_issue_url, verify=False).json()
        DateCreated = issue['created_at'][:-10]
        DateUpdated = issue['updated_at'][:-10]
        if 'pull_request' not in issue:
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

            csvout.writerow([repo_name, 
                            issue['number'], issue['title'].encode('utf-8'),
                            issue['body'].encode('utf-8'), 
                            assignees[:-1],
                            issue['state'],
                            Pipeline, DateCreated, DateUpdated,
                            labels[:-1],
                            category, tag, priority,
                            estimate])

def get_issues(repo_data):
    repo_name = repo_data[0]
    repo_ID = repo_data[1]

    issues_for_repo_url = f'https://api.github.com/repos/{repo_name}/issues?{QUERY}'
    print('Retrieving issues.... ' + issues_for_repo_url)
    r = requests.get(issues_for_repo_url, auth=AUTH, verify=False)
    write_issues(r, FILEOUTPUT, repo_name, repo_ID)

    if 'link' in r.headers:
        pages = dict(
            [(rel[6:-1], url[url.index('<') + 1:-1]) for url, rel in
             [link.split(';') for link in
              r.headers['link'].split(',')]])
        while 'last' in pages and 'next' in pages:
            pages = dict(
                [(rel[6:-1], url[url.index('<') + 1:-1]) for url, rel in
                 [link.split(';') for link in
                  r.headers['link'].split(',')]])
            r = requests.get(pages['next'], auth=AUTH, verify=False)
            write_issues(r, FILEOUTPUT, repo_name, repo_ID)
            if pages['next'] == pages['last']:
                break


config = configparser.ConfigParser()
config.read('config.ini')

REPO_LIST = []
for (repo_name, repo_id) in config.items("REPO_LIST"):
    REPO_LIST.append( (repo_name, repo_id) )

AUTH = ('token', config['ACCESS']['AUTH_TOKEN'])
ACCESS_TOKEN = config['ACCESS']['ZEN_ACCESS']

# See https://developer.github.com/v3/issues/#list-repository-issues
QUERY = config['ACCESS']['QUERY']

ISSUES = 0
FILENAME = config['ACCESS']['FILENAME']
OPENFILE = open(FILENAME, 'w', newline='\n')
FILEOUTPUT = csv.writer(OPENFILE, dialect='excel', quoting=csv.QUOTE_NONNUMERIC)

FILEOUTPUT.writerow(('Repository', 
                     'Issue Number', 'Issue Title',
                     'Description', 
                     'Category', 'Tag', 
                     'Assigned To',
                     'Priority', 
                     'State',
                     'Pipeline',
                     'Issue Author',
                     'Created At', 'Updated At', 
                     'Labels', 'Estimate'
                     ))

for repo_data in REPO_LIST:
    get_issues(repo_data)

OPENFILE.close()