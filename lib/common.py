"""
Functions common to all sources.
"""
import configparser
import csv
from dateutil.parser import parse as date_parse
import pytz
import sys

from rich import print as rprint

def get_column_headers():
    """This represents the set of AzDo Work Item Fields we populate for import. Some are not /really/ used, but in the import template anyway."""
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
        'area': 'Area Path',
        'github': 'GitHub backref'
    }

def prepare_row(row_dict):
    """Take a dict keyed by the above column headers, and prepare it for writing to AzDo CSV"""
    row = {}
    for key,title in get_column_headers().items():
        row[title] = row_dict[key]
    return row

def get_config(INI_FILE='config.ini'):
    config = configparser.ConfigParser()
    config.read(INI_FILE)

    # Minimum requirement: an output file (CSV)
    in_config = {
        # Output file
        'OUTPUT_FILE': config.get('OUTPUT', 'FILENAME'),
    } 

    # Collect the mode-specific config elements, if available.
    in_config.update(get_hub_config(config))
    in_config.update(get_jira_config(config))
    return in_config

def get_hub_config(config):
    if "HUB_REPO_LIST" not in config:
        return {}

    # Get a list of repos from the config file.
    REPO_LIST = []
    for (repo_name, repo_id) in config.items("HUB_REPO_LIST"):
        REPO_LIST.append( (repo_name, repo_id) )

    return {
        'REPO_LIST': REPO_LIST,
        # See https://developer.github.com/v3/issues/#list-repository-issues
        'QUERY': config.get('HUB_OPTS', 'QUERY'),
        'AREA_PATH': config.get('HUB_OPTS', 'AREA_PATH'),

        # Gather credentials
        'GITHUB_AUTH': ('token', config.get('HUB_ACCESS', 'GITHUB_AUTH')),
        'ZENHUB_AUTH': config.get('HUB_ACCESS', 'ZENHUB_AUTH'),
    }

def get_jira_config(config):
    if "JIRA_INPUT" not in config:
        return {}

    return {
        'JIRA_INPUT': config.get('JIRA_INPUT', 'FILENAME'),
        'JIRA_ITERATION': config.get('JIRA_INPUT', 'ITERATION'),
    }

def init_main():
    # @TODO: add support for --verbose and --help
    #opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]
    args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]

    if not args:
        exit('Please provide a config.ini file as first argument. See README.md for details.')

    print("Config file: "+args[0])
    config = get_config(args[0])
    return config

def init_fileoutput(file):
    """Setup CSV DictWriter with appropriate quoting/delimiting for AzDo import."""
    fields = get_column_headers().values()
    #csv.register_dialect('azdo', 'excel',  doublequote=False, escapechar='\\')
    writer = csv.DictWriter(file, fieldnames=fields, dialect='excel', quoting=csv.QUOTE_ALL)
    writer.writeheader()
    return writer

def parse_date(date_str):
    """This is what we need for AzDo import, corresponding to local user preferences."""
    dst_fmt='%m/%d/%Y %I:%M:%S %p'
    dt = date_parse(date_str)
    dt_local = dt.strftime(dst_fmt)
    return dt_local