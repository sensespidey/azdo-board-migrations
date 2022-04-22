"""
Author: Derek Laventure <derek.laventure@ssc.gc.ca>

Loads issue data exported from Jira and generates a CSV suitable for import into
Azure DevOps.

@TODO: describe steps for exporting the initial .xlsx
 """

import csv
import sys

# Set utf-8 encoding everywhere
# Set utf-8 encoding everywhere (https://stackoverflow.com/a/63573649)
sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

# DEBUG
from rich import print as rprint

from lib.common import get_config, init_fileoutput, init_main, parse_date, prepare_row

def main(config):
    rprint(config)
    with open(config['OUTPUT_FILE'], 'w', newline='\n', encoding='utf-8') as file:
        outfile = init_fileoutput(file)
        rprint(outfile)

        # Now read the input file, transform and write
        with open(config['JIRA_INPUT'], mode='r') as jira_csv:
            jira_csv_reader = csv.DictReader(jira_csv)
            line_count = 0
            for row in jira_csv_reader:
                print("New row")
                rprint(row)
                if line_count == 0:
                    print(f'Column names are {", ".join(row)}')
                    line_count += 1
                else:
                    issue = parse_jira_issue(row, config['JIRA_ITERATION'])
                    write_issue(issue, outfile)

def get_jira_mapping():
    return {
        'type': 'Issue Type',
        'title': 'ï»¿Summary',
        'body': 'Description',
        'tags': 'Labels',
        'assignee': 'Assignee',
        'priority': 'Priority',
        'state': 'Resolution',
        'author': 'Reporter',
        'created': 'Created',
        'changed': 'Updated',
        'effort': '',
        'iteration': '',
        'area': '',
        'github': '',
    }

def parse_jira_issue(row, iteration):
    # Here make a mapping of fields in the destination CSV, populated by data from the source row
    # This is very quick and dirty, as it's a one-time operation, and the fields
    # on both ends are subject to change for any particular use-case.
    issue = {}
    for key,val in get_jira_mapping().items():
        rprint(val)
        #val = row[val]
        if key == 'type':
            if row[val] == 'Story':
                issue[key] = 'Product Backlog Item'
            else:
                issue[key] = 'Epic'
        elif key == 'created' or key == 'changed':
            issue[key] = parse_date(row[val])
        elif key in ('assignee', 'author', 'effort'):
            issue[key] = ''
        elif key == 'iteration':
            issue[key] = iteration
        elif key == 'priority':
            if row[val] == 'Normal':
                issue[key] = 2
            elif row[val] == 'Urgent':
                issue[key] = 1
            else:
                issue[key] = 2
        elif key == 'state':
            issue[key] = 'New'
            if row[val] == 'Closed':
                issue['tags'] = 'closed'
        else:
            issue[key] = row[val]
    return issue

def write_issue(issue, csvout):
    print("Writing row for issue: ")
    rprint(prepare_row(issue))
    csvout.writerow(prepare_row(issue))

if __name__ == '__main__':
    config = init_main()

    if "JIRA_INPUT" not in config:
        exit('config.ini does not contain a JIRA_INPUT section. Please see README.md for details.')

    main(config)