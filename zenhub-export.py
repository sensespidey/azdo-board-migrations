"""
Author: Derek Laventure <derek.laventure@ssc.gc.ca>

Collects issue data from ZenHub/GitHub and generates a CSV suitable for import
into Azure DevOps.

Supports Github API v3 and ZenHubs current working API.
"""
import csv
import datetime
import requests
import sys

# Set utf-8 encoding everywhere (https://stackoverflow.com/a/63573649)
sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

# DEBUG
from rich import print as rprint

from common import get_config, hub_row_data

def main():
    config = get_config()

    # @TODO: refactor this common stuff
    # @TODO: move headers into config? or make 
    csv.register_dialect('azdo', 'excel',  doublequote=False, escapechar='\\')
    col_headers = [
        'Work Item Type',
        'Title',
        'Description',
        'Tags',
        'Assigned To',
        'Priority',
        'State',
        'Created By',
        'Created Date',
        'Changed Date',
        'Effort',
        'Iteration Path',
    ]
    # @TODO: use with idiom here (no need to close in that case)
    OPENFILE = open(config['FILENAME'], 'w', newline='\n', encoding="utf-8")
    FILEOUTPUT = csv.DictWriter(OPENFILE, fieldnames=col_headers, dialect='excel', quoting=csv.QUOTE_ALL)
    FILEOUTPUT.writeheader()
    config['FILEOUTPUT'] = FILEOUTPUT

    for repo_data in config['REPO_LIST']:
        get_issues(repo_data, config)

    OPENFILE.close()


def get_issues(repo_data, config):
    repo_name = repo_data[0]
    repo_ID = repo_data[1]

    issues_for_repo_url = f'https://api.github.com/repos/{repo_name}/issues?{config["QUERY"]}'
    print('Retrieving issues.... ' + issues_for_repo_url)

    # @TODO: wrap this in an iterator
    r = requests.get(issues_for_repo_url, auth=config['GITHUB_AUTH'], verify=False)
    write_issues(r, config['FILEOUTPUT'], repo_name, repo_ID, config['ZENHUB_AUTH'])

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
            r = requests.get(pages['next'], auth=config['GITHUB_AUTH'], verify=False)
            write_issues(r, config['FILEOUTPUT'], repo_name, repo_ID, config['ZENHUB_AUTH'])
            if pages['next'] == pages['last']:
                break
            
def write_issues(r, csvout, repo_name, repo_ID, ZENHUB_AUTH):
    if not r.status_code == 200:
        raise Exception("Request returned status of:"+str(r.status_code))

    r_json = r.json()
    print(str(len(r_json)) + ' issues loaded. Loading ZenHub data...')
    for issue in r_json:
        print(repo_name + ' issue: ' + str(issue['number']))

        zenhub_issue_url = 'https://api.zenhub.io/p1/repositories/' + str(repo_ID) + '/issues/' + str(issue['number']) + '?access_token=' + ZENHUB_AUTH
        zen_r = requests.get(zenhub_issue_url, verify=False).json()

        # DEBUG
        rprint(issue)
        rprint(zen_r)

        DateCreated = issue['created_at'][:-10]
        DateUpdated = issue['updated_at'][:-10]

        # Ignore pull requests, which github treats as issues
        if 'pull_request' in issue:
            continue

        assignees, tags, category, priority, labels = '', '', '', '', ''

        for i in issue['assignees'] if issue['assignees'] else []:
            assignees += i['login'] + ','

        for x in issue['labels'] if issue['labels'] else []:
            tags += x['name'] + ','
#            if "Category" in x['name']:
#                category = x['name'][11:11 + len(x['name'])]
#            elif "Tag" in x['name']:
#                tag = x['name'][6:6 + len(x['name'])]
#            elif "Priority" in x['name']:
#                priority = x['name'][11:11 + len(x['name'])]
#            else:
#                labels += x['name'] + ','

        estimate = zen_r.get('estimate', dict()).get('value', "")

        if issue['state'] == 'closed':
            Pipeline = 'Closed'
        else:
            Pipeline = zen_r.get('pipeline', dict()).get('name', "")

        if not issue.get('body'):
            issue['body'] = ''

        issue['is_epic'] = zen_r['is_epic'] if "is_epic" in zen_r else False

        row_dict = hub_row_data(issue, tags, assignees, priority, DateCreated, DateUpdated, estimate)
        csvout.writerow(row_dict)

if __name__ == '__main__':
    main()