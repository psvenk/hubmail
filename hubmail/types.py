from typing import (TypedDict, Optional, Union, List, Dict)

class QueryVariables(TypedDict, total=False):
    id: str
    user: str
    repo: str
    number: int
    numThreads: int
    numComments: int
    cursor: Optional[str]
    html: Optional[bool]

class Actor(TypedDict, total=False):
    login: str
    name: str
    email: str
    emailOrNull: Optional[str]

class PageInfo(TypedDict, total=False):
    nextCursor: str

class Issue(TypedDict, total=False):
    id: str
    number: int
    title: str
    author: Actor
    body: str
    bodyHTML: str
    createdAt: str

class PullRequest(TypedDict, total=False):
    id: str
    number: str
    url: str
    title: str
    author: Actor
    body: str
    bodyHTML: str
    createdAt: str

class IssueOrPullRequestConnection(TypedDict, total=False):
    nodes: List[Union[Issue, PullRequest]]
    pageInfo: PageInfo

class IssueComment(TypedDict, total=False):
    databaseId: int
    author: Actor
    body: str
    bodyHTML: str
    createdAt: str

class IssueCommentConnection(TypedDict, total=False):
    nodes: List[IssueComment]
    pageInfo: PageInfo
