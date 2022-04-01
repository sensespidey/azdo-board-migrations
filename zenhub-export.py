"""
Author: Derek Laventure <derek.laventure@ssc.gc.ca>

Collects issue data from ZenHub/GitHub and generates a CSV suitable for import
into Azure DevOps.

Supports Github API v3 and ZenHubs current working API.
"""
import csv
import sys

# Set utf-8 encoding everywhere (https://stackoverflow.com/a/63573649)
sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

# DEBUG
from rich import print as rprint

from common import get_config, get_column_headers, prepare_row
from hub import HubIssues

def main():
    config = get_config()
    
    # @TODO: Is this doing anything?
    csv.register_dialect('azdo', 'excel',  doublequote=False, escapechar='\\')

    # @TODO: use with idiom here (no need to close in that case)
    OPENFILE = open(config['FILENAME'], 'w', newline='\n', encoding="utf-8")
    # @TODO: move headers into config? or make them 
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
    issue_iter = HubIssues(repo_name, config)
    for issues in issue_iter:
        write_issues(issues, config['FILEOUTPUT'])

def write_issues(issues, csvout):
    for issue in issues:
        csvout.writerow(prepare_row(issue))

if __name__ == '__main__':
    main()
