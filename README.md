# Introduction

This repository contains Python scripts to facilitate migrating Work Items into Azure DevOps from a few external sources:

- Zenhub/Github
- Jira
- GitLab

The primary goal is to collect issue data and generate a CSV file appropriate for import into an Azure DevOps project.

See details below depending on which data source you are working with (currently ZenHub/GitHub and Jira are supported).

# Getting Started

The 2 main entrypoint scripts for this repository are:

* `zenhub-export.py` - uses GitHub+ZenHub APIs to compile a CSV of issues for a given repository.
* `jira-tranzform.py` - takes a JIRA-exported CSV file and transforms its format into one suited to import into Azure DevOps.

Each of the scripts takes a config.ini file as its primary argument, and expects
that file to provide its required parameters to consume, transform, and output
the necessary file.

For JIRA sources, we don't access an API, so no credentials are needed. Instead, the config files specify a previously-exported CSV file as the source data (see below for details).

## Create a local virtualenv, install requirements

```
python3 -m venv env
source env/bin/activate
python3 -m pip install -r requirements.txt
```

## Credentials

To make use of the Hub code, you need to set up appropriate credentials, and
create a config.ini file to contain them.

The following credentials are needed:

- GitHub Personal Access Token (https://github.com/settings/tokens)
- ZenHub Access Key (https://app.zenhub.com/settings/tokens)

##  Config.ini

See `config.ini.example` for a complete example.

Each script uses a simple group-based INI-style config file to provide at least
an output file for the script to write to.  Generally one config file for each
source and output CSV file is recommended.

```
[OUTPUT]
FILENAME = issues.csv
```

### Hub (git/zen) config

Add the following to config.ini with appropriate values:

```
[HUB_ACCESS]
AUTH_TOKEN = <GitHub Personal Access Token>
ZEN_ACCESS = <ZenHub Access Key>

[HUB_OPTS]
QUERY = state=all&per_page=100 # See https://developer.github.com/v3/issues/#list-repository-issues
AREA_PATH = ISSUE IMPORT TEST PROJECT\Staging

[HUB_REPO_LIST]
# Repo org/name = Iteration path in AzDo
sensespidey/example-agile-project = ISSUE IMPORT TEST PROJECT
```

The HUB_REPO_LIST maps a github namespace/repo to a Project-level (or lower)
Iteration in Azure DevOps, so we can target a set of issues going into a (sub)team-level board, if needed.

Related, the QUERY option provided here allows us to narrow down the list of
issues pulled, and potentially "break down" the issues we pull into logical groups, as needed. Combined with targeted Iteration paths, this may provide for interesting use-cases.

### JIRA config

Add the following to config.ini with appropriate values:

```
[JIRA_INPUT]
FILENAME = Jira-Dump-28-March.csv
ITERATION = ISSUE IMPORT TEST PROJECT
AREA = ISSUE IMPORT TEST PROJECT\Staging
```

# Usage

## Hub (git/zen) issue preparation

To pull issues from ZenHub/GitHub APIs, we setup a config.ini as above, and run it as, eg:

```
python zenhub-export.py config-gcpboard.ini
```

## Jira issue preparation

To transform an exported set of issues in JIRA's full-column CSV format, we run:

```
python jira-transform.py config-jira.ini
```

## Azure DevOps Import

One thing of note in the common output logic here, the "closed" tag is added when we detect that the source had issues considered Closed in the list. AzDo won't let us import these by CSV directly, so one needs to manually close issues with that tag (and then remove the tag), when importing:

1. Go to the project
2. Queries -> Import Work Items
3. Upload CSV file, then preview list of imported data items in draft.
4. Review for issues, and save the whole set.
5. Filter for `closed` tag, and manually close that set of issues.
6. Remove the `closed` tag from this set as well.
7. Consider adding a tag specific to this particular import, if needed.

# Credits

These scripts were derived from the following sources:

* https://gist.github.com/unbracketed/3380407
* https://gist.github.com/Kebiled/7b035d7518fdfd50d07e2a285aff3977 @PinnaclePSM Author Jamie Belcher
