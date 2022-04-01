
"""
Functions relevant to ZenHub/GitHub source.
"""
def hub_row_data(issue, tags, assignees, priority, DateCreated, DateUpdated, estimate):
    row_dict = {
        'type': 'Epic' if ("is_epic" in issue and issue['is_epic']) else 'Product Backlog Item',
        'title': issue['title'],
        # @TODO: append a link back to GitHub issue to description
        'body': str(issue['body']) + "\n\nOriginal GitHub issue link: " + str(issue['url']),
        'tags': tags,
        'assignee': assignees[:-1],
        'priority': priority,
        'state': issue['state'],
        'author': issue['user']['login'],
        'created': DateCreated,
        'changed': DateUpdated,
        'effort': estimate,
        'iteration': 'ISSUE IMPORT TEST PROJECT'
    }
    return row_dict