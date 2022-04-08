"""
Functions common to all sources.
"""
import configparser
import csv
from dateutil.parser import parse as date_parse
import pytz


def get_config():
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Get a list of repos from the config file.
    #@TODO: don't need IDs for these anymore, but perhaps destination "Iteration Path" string?
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
        'OUTPUT_FILE': config.get('OUTPUT', 'FILENAME'),
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
        'iteration': 'Iteration Path',
    }

def init_fileoutput(file):
    """Setup CSV DictWriter with appropriate quoting/delimiting for AzDo import."""
    fields = get_column_headers().values()
    #csv.register_dialect('azdo', 'excel',  doublequote=False, escapechar='\\')
    writer = csv.DictWriter(file, fieldnames=fields, dialect='excel', quoting=csv.QUOTE_ALL)
    writer.writeheader()
    return writer

def prepare_row(row_dict):
    row = {}
    for key,title in get_column_headers().items():
        row[title] = row_dict[key]
    return row

def parse_date(date_str):
    # This is what we need for AzDo import, in UTC (as provided by GitHub)
    dst_fmt='%m/%d/%Y %I:%M:%S %p'
    dt = date_parse(date_str)
    dt_local = dt.strftime(dst_fmt)
    return dt_local
