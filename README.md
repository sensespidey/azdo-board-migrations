# Introduction 

This repository contains Python scripts to facilitate migrating Work Items into Azure DevOps from a few external sources:

- Zenhub/Github
- Jira
- GitLab

The primary goal is to collect issue data and generate a CSV file appropriate for import into an Azure DevOps project.

# Getting Started

To make use of this code, you need to set up appropriate credentials, and create a config.ini file to contain them.

## Credentials

The following credentials are needed:

- GitHub Personal Access Token (link)
- ZenHub Access Key (link)


##  Config.ini


Add the following to config.ini with appropriate values:

```
[ACCESS]
AUTH_TOKEN = <GitHub Personal Access Token>
ZEN_ACCESS = <ZenHub Access Key>
QUERY = # See https://developer.github.com/v3/issues/#list-repository-issues
FILENAME = 

[REPO_LIST]
sensespidey/example-agile-project = 473431083
```

The REPO_LIST should have the ID of the GitHub repository, which you can get by querying the GitHub API like so:

```
curl --location --request GET 'https://api.github.com/repos/ssc-spc-ccoe-cei/gcpboard' \
--header 'Authorization: token <insert GitHub PAT>'
```
# Usage

To grab issues from Zen

# Credits

These scripts were derived from the following sources:

* https://gist.github.com/unbracketed/3380407
* https://github.com/ZenHubIO/support/issues/1070
* https://gist.github.com/Kebiled/7b035d7518fdfd50d07e2a285aff3977 @PinnaclePSM Author Jamie Belcher