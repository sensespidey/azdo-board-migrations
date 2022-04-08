"""
Author: Derek Laventure <derek.laventure@ssc.gc.ca>

Collects issue data from ZenHub/GitHub and generates a CSV suitable for import
into Azure DevOps.

Supports Github API v3 and ZenHubs current working API.
"""
import sys

# Set utf-8 encoding everywhere (https://stackoverflow.com/a/63573649)
sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

# DEBUG
from rich import print as rprint

from common import get_config, init_fileoutput, prepare_row
from hub import HubIssues

def main():
    config = get_config()
    with open(config['OUTPUT_FILE'], 'w', newline='\n', encoding='utf-8') as file:
        outfile = init_fileoutput(file)
        for repo_data in config['REPO_LIST']:
            for issues in HubIssues(repo_data, config):
                write_issues(issues, outfile)

def write_issues(issues, csvout):
    """Takes a list of the latest <100 issues, with keys set from the source data, normalizes and writes it to our file."""
    for issue in issues:
        print("Writing row for issue: ")
        rprint(prepare_row(issue))
        csvout.writerow(prepare_row(issue))

if __name__ == '__main__':
    main()