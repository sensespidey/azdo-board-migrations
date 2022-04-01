"""
Author: Derek Laventure <derek.laventure@ssc.gc.ca>

Collects issue data from ZenHub/GitHub and generates a CSV suitable for import
into Azure DevOps.

Supports Github API v3 and ZenHubs current working API.
"""
import csv
import datetime
import sys

# Set utf-8 encoding everywhere (https://stackoverflow.com/a/63573649)
sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

# DEBUG
from rich import print as rprint

from common import get_config, get_column_headers, prepare_row, parse_date
from hub import query_github_issues, query_zenhub_issue, hub_row_data, get_github_api_raw

def main():
    config = get_config()
    csv.register_dialect('azdo', 'excel',  doublequote=False, escapechar='\\')

    # @TODO: refactor this common stuff
    # @TODO: move headers into config? or make them 

    # @TODO: use with idiom here (no need to close in that case)

    OPENFILE = open(config['FILENAME'], 'w', newline='\n', encoding="utf-8")
    FILEOUTPUT = csv.DictWriter(OPENFILE, fieldnames=get_column_headers().values(), dialect='excel', quoting=csv.QUOTE_ALL)
    FILEOUTPUT.writeheader()
    config['FILEOUTPUT'] = FILEOUTPUT

    for repo_data in config['REPO_LIST']:
        get_issues(repo_data, config)

    OPENFILE.close()

def get_issues(repo_data, config):
    repo_name = repo_data[0]
    repo_ID = repo_data[1]

  #  issues_for_repo = query if query is not None else f'repos/{repo_name}/issues?' + config["QUERY"]
    issues = query_github_issues(f'repos/{repo_name}/issues', config)

    # @TODO: wrap this in an iterator

    count = len(issues.json())
    print(f'Loaded {count} issues. Loading ZenHub data...')

    issues_list = []
    for issue in issues.json():
        # Ignore pull requests, which github treats as issues
        if 'pull_request' in issue:
            continue

        zen_r = query_zenhub_issue(repo_name, issue['number'], config).json()

        print(f'{repo_name} issue: ' + str(issue['number']))
        issues_list.append(process_issue(issue, zen_r))

        # DEBUG
        #rprint(issue)
        #rprint(zen_r)


    write_issues(issues_list, config['FILEOUTPUT'])

    rprint(issues.headers['link'])

    if 'link' in issues.headers:
        link_header = issues.headers['link']
        pages = get_pages(link_header)
        rprint(pages)
        exit()


        # @TODO: wrap this in an iterator?
        # this goes away in the iterator..
        while 'last' in pages and 'next' in pages:
            pages = get_pages()
            pages = dict(
                [(rel[6:-1], url[url.index('<') + 1:-1]) for url, rel in
                 [link.split(';') for link in
                  issues.headers['link'].split(',')]])

            issues = get_github_api_raw(pages['next'], config)
            write_issues(issues, config['FILEOUTPUT'], repo_name, repo_ID, config['ZENHUB_AUTH'])

            if pages['next'] == pages['last']:
                break
            
def get_pages(link_header):
    return dict(
        [(rel[6:-1], url[url.index('<') + 1:-1]) for url, rel in
            [link.split(';') for link in
            link_header.split(',')]])


def write_issues(issues, csvout):
    for issue in issues:
        csvout.writerow(prepare_row(issue))

def process_issue(issue, zen_r):
    #DateCreated = issue['created_at'][:-10]
    #DateUpdated = issue['updated_at'][:-10]

    DateCreated = parse_date(issue['created_at'])
    DateUpdated = parse_date(issue['updated_at'])

    assignees, tags, category, priority, labels = '', '', '', '', ''

    for i in issue['assignees'] if issue['assignees'] else []:
        assignees += i['login'] + ','

    for x in issue['labels'] if issue['labels'] else []:
        tags += x['name'] + ','

    estimate = zen_r.get('estimate', dict()).get('value', "")

    if issue['state'] == 'closed':
        Pipeline = 'Closed'
    else:
        Pipeline = zen_r.get('pipeline', dict()).get('name', "")

    if not issue.get('body'):
        issue['body'] = ''

    issue['is_epic'] = zen_r['is_epic'] if "is_epic" in zen_r else False

    row_dict = hub_row_data(issue, tags, assignees, priority, DateCreated, DateUpdated, estimate)
    return row_dict


if __name__ == '__main__':
    main()
