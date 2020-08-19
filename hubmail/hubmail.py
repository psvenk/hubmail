"""hubmail: a tool to export GitHub issues and pull requests as email messages
"""
# SPDX-License-Identifier: LGPL-2.1-or-later

import sys
import os
import email.policy
from email.message import EmailMessage
from email.headerregistry import Address
from email.parser import HeaderParser
from time import time, gmtime, asctime
from urllib.parse import urlparse
import textwrap
import re
import mimetypes
import posixpath

from typing import (Any, Optional, Dict, Literal, List, cast, AsyncIterator,
                    Union, Tuple)
from hubmail.types import (QueryVariables, Issue, PullRequest,
                           IssueOrPullRequestConnection, IssueComment,
                           IssueCommentConnection, Actor)
from datetime import datetime

try:
    from hubmail.mdparse import get_image_urls
except: pass

import aiohttp
from dateutil.parser import isoparse

_QUERY_FILE_NAME = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "data", "queries.graphql"
)

with open(_QUERY_FILE_NAME, "r") as queryFile:
    _QUERY = queryFile.read()

def fatal(*args: Any, **kwargs: Any) -> None:
    print(*args, **kwargs, file=sys.stderr) # type: ignore
    sys.exit(1)

NULL_ACTOR: Actor = {
    "login": "ghost",
    "name": "ghost",
    "email": "",
    "emailOrNull": "",
}
REGEX_FROM = re.compile(r"^From", flags=re.MULTILINE)
REGEX_FROM_SPACE = re.compile(r"^From ", flags=re.MULTILINE)
REGEX_PATCH = re.compile(r"^\[PATCH( .*?)?]", flags=re.MULTILINE)

class Hubmail:
    def __init__(self, arguments: Any) -> None:
        self.type: str = arguments.subcommand
        self.user: str = arguments.user
        self.repo: str = arguments.repo
        self.comments: Optional[int] = arguments.comments
        self.wrap: Optional[int] = arguments.wrap
        self.extended_subject: bool = arguments.extended_subject
        self.html: bool = arguments.html

        self.number: Optional[int]
        try:
            self.number = arguments.number
        except AttributeError:
            pass

        self.threads: Optional[int]
        try:
            self.threads = arguments.threads
        except AttributeError:
            pass

        self.total_threads = 0

        self.policy = email.policy.default.clone(
            max_line_length = self.wrap,
            raise_on_defect = True,
        )
        self.patch_policy = email.policy.default.clone(
            max_line_length = None,
            refold_source = "none",
            raise_on_defect = True,
        )

    async def _run_query(self, opname: str, variables: QueryVariables) -> Any:
        assert self.session, "No session initialized"
        async with self.session.post(
            "https://api.github.com/graphql",
            json={
                "query": _QUERY,
                "variables": variables,
                "operationName": opname
            },
            headers={"Authorization": f"Bearer {self.token}"}
        ) as resp:
            assert resp.status == 200
            result = await resp.json()
            assert "errors" not in result, result["errors"]
            return result

    async def _get_thread(
        self, thread_type: Literal["issue", "pullRequest"], user: str,
        repo: str, number: int
    ) -> Union[Issue, PullRequest]:
        query = thread_type[0].upper() + thread_type[1:]
        variables: QueryVariables = {
            "user": user,
            "repo": repo,
            "number": number,
            "html": self.html,
        }
        result = cast(Union[Issue, PullRequest],
                      (await self._run_query(query, variables))
                      ["data"]["repository"][thread_type])
        assert result is not None
        return result

    async def _get_threads(
        self, threads_type: Literal["issues", "pullRequests"], user: str,
        repo: str
    ) -> AsyncIterator[List[Union[Issue, PullRequest]]]:
        query = threads_type[0].upper() + threads_type[1:]
        # Get threads from end (reverse order) if negative number of threads
        # specified
        if self.threads is not None and self.threads < 0:
            query += "FromEnd"
            reverse_order = True
        else:
            reverse_order = False
        num_threads = abs(self.threads) if self.threads is not None else None
        variables: QueryVariables = {
            "user": user, "repo": repo,
            "numThreads": (
                20 if num_threads is None or num_threads >= 20
                else num_threads
            ),
            "cursor": None,
            "html": self.html,
        }
        while True:
            result = cast(IssueOrPullRequestConnection,
                          (await self._run_query(query, variables))
                          ["data"]["repository"][threads_type])
            if reverse_order:
                result["nodes"] = result["nodes"][::-1]
            self.total_threads += len(result["nodes"])
            if num_threads is None or self.total_threads <= num_threads:
                yield result["nodes"] or []
            else:
                # Remove the excess threads
                yield result["nodes"][:-(self.total_threads - num_threads)]
                break
            variables["cursor"] = result["pageInfo"]["nextCursor"]
            if not variables["cursor"]:
                break

    async def _get_comments(self, id: str) -> AsyncIterator[List[IssueComment]]:
        # Get threads from end (reverse order) if negative number of comments
        # specified
        if self.comments is not None and self.comments < 0:
            query = "CommentsFromEnd"
            reverse_order = True
        else:
            query = "Comments"
            reverse_order = False
        num_comments = (abs(self.comments) if self.comments is not None
                        else None)
        variables: QueryVariables = {
            "id": id,
            "numComments": (
                20 if num_comments is None or num_comments >= 20
                else num_comments
            ),
            "cursor": None,
            "html": self.html,
        }
        total_comments = 0
        while True:
            result = cast(IssueCommentConnection,
                          (await self._run_query(query, variables))
                          ["data"]["node"]["comments"])
            if reverse_order:
                result["nodes"] = result["nodes"][::-1]
            total_comments += len(result["nodes"])
            if num_comments is None or total_comments <= num_comments:
                yield result["nodes"] or []
            else:
                # Remove the excess comments
                yield result["nodes"][:-(total_comments - num_comments)]
                break
            # Get new cursor; break if end of comments reached
            variables["cursor"] = result["pageInfo"]["nextCursor"]
            if not variables["cursor"]:
                break

    async def _format_email(self, name: str, address: str, timestamp: datetime,
                            subject: str, body: str, message_id: str, *,
                            in_reply_to: str = "", references: str = "",
                            html: Optional[str] = None) -> str:
        body = body.replace("\r\n", "\n")

        cols = self.wrap or 0
        if cols > 0:
            body = "\n".join(
                textwrap.fill(
                    line, cols, expand_tabs=False, replace_whitespace=False,
                    break_long_words=False, break_on_hyphens=False,
                    subsequent_indent=(
                        "> " if line.startswith("> ")
                        else ">" if line.startswith(">")
                        else ""))
                for line in body.splitlines())

        # Replace "From" at the beginning of a line with ">From"
        # (see https://www.jwz.org/doc/content-length.html)
        body = REGEX_FROM.sub(r">From", body)

        msg = EmailMessage(policy=self.policy)
        msg.set_content(body)

        if html:
            msg.add_alternative(html, subtype="html")

        # Identify image URLs and add the images as attachments
        try:
            for url in get_image_urls(body):
                async with self.session.get(url) as resp:
                    assert resp.status == 200
                    img_data: bytes = await resp.read()
                    maintype, subtype = (mimetypes.guess_type(url)[0] or
                                         "application/octet-stream").split("/")
                    filename = posixpath.basename(urlparse(url).path)
                    msg.add_attachment(
                        img_data, maintype=maintype, subtype=subtype,
                        filename=filename
                    )
        except:
            pass

        try:
            msg["From"] = Address(name, addr_spec=address)
        except IndexError:
            msg["From"] = Address(name)
        msg["Date"] = timestamp
        msg["Subject"] = subject
        if message_id:
            msg["Message-ID"] = message_id
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to

        if references and in_reply_to:
            msg["References"] = f"{references} {in_reply_to}"
        elif references:
            msg["References"] = references
        elif in_reply_to:
            msg["References"] = in_reply_to

        # For some reason as_string does not include the unixfrom line
        # and as_bytes uses the quoted-printable encoding despite purportedly
        # supporting native Unicode.
        return msg.as_bytes(policy=self.policy, unixfrom=True).decode()

    async def _format_issue(self, user: str, repo: str, issue: Issue) -> str:
        number = issue["number"]
        author = issue["author"] or NULL_ACTOR
        assert number and author
        subject = (f"[{user}/{repo}] {issue['title']} (#{number})"
                   if self.extended_subject else issue["title"])
        html = issue["bodyHTML"] if self.html else None
        result = await self._format_email(
            author.get("name") or author.get("login") or "",
            author.get("email") or author.get("emailOrNull") or "",
            isoparse(issue["createdAt"]), subject, issue["body"],
            f"<{user}/{repo}/issues/{number}@github.com>", html=html)
        if self.comments == 0:
            return result
        return result + "\n\n".join([i async for i in self._format_comments(
            issue["id"], f"Re: {subject}",
            (user, repo, "issues", str(number)))])

    async def format_issue(self, user: str, repo: str, number: int) -> str:
        issue = cast(Issue,
                     await self._get_thread("issue", user, repo, number))
        return await self._format_issue(user, repo, issue)

    async def _format_pull(self, user: str, repo: str,
                           pull: PullRequest) -> str:
        number = pull["number"]
        author = pull["author"] or NULL_ACTOR
        assert number and author
        subject = (f"[{user}/{repo}] {pull['title']} (#{number})"
                   if self.extended_subject else pull["title"])
        thread_info = (user, repo, "pull", str(number))
        message_id = f"<{'/'.join(thread_info)}@github.com>"
        html = pull["bodyHTML"] if self.html else None
        result = await self._format_email(
            author.get("name") or author.get("login") or "",
            author.get("email") or author.get("emailOrNull") or "",
            isoparse(pull["createdAt"]), subject, pull["body"],
            message_id, html=html)

        # Get pull request patches
        async with self.session.get(f"{pull['url']}.patch") as resp:
            assert resp.status == 200
            for rawtext in REGEX_FROM_SPACE.split(await resp.text())[1:]:

                unixfrom, text = rawtext.split("\n", 1)
                commit_sha = unixfrom.split(" ", 1)[0]

                # Keep headers separate from body so that patch is not mangled
                # (e.g. if patch contains CRLF, don't convert to LF)
                headers, body = text.split("\n\n", 1)
                msg = HeaderParser(policy=self.patch_policy).parsestr(headers)
                if self.extended_subject:
                    msg_subject = msg["Subject"]
                    del msg["Subject"]
                    msg["Subject"] = REGEX_PATCH.sub(
                        r"[PATCH {}/{}#{}\1]".format(user, repo, number),
                        msg_subject)
                msg["Message-ID"] = (
                    f"<{'/'.join(thread_info)}/{commit_sha}@github.com>")
                msg["In-Reply-To"] = message_id
                msg["References"] = message_id
                result += (
                    "\n" + "From " + unixfrom + "\n"
                    + msg.as_string(policy=self.policy) + body)

        if self.comments == 0:
            return result
        return result + "\n".join([i async for i in self._format_comments(
            pull["id"], f"Re: {subject}", thread_info)])

    async def format_pull(self, user: str, repo: str, number: int) -> str:
        pull = cast(PullRequest,
                    await self._get_thread("pullRequest", user, repo, number))
        return await self._format_pull(user, repo, pull)

    async def _format_issues(self, user: str, repo: str) -> AsyncIterator[str]:
        async for issues in cast(AsyncIterator[List[Issue]],
                                 self._get_threads("issues", user, repo)):
            for issue in issues:
                yield await self._format_issue(user, repo, issue)

    async def format_issues(self, user: str, repo: str) -> str:
        return "\n\n".join([i async for i in self._format_issues(user, repo)])

    async def _format_pulls(self, user: str, repo: str) -> AsyncIterator[str]:
        async for pulls in cast(AsyncIterator[List[PullRequest]],
                                self._get_threads("pullRequests", user, repo)):
            for pull in pulls:
                yield await self._format_pull(user, repo, pull)

    async def format_pulls(self, user: str, repo: str) -> str:
        return "\n\n".join([i async for i in self._format_pulls(user, repo)])

    async def _format_comments(
        self, id: str, subject: str, thread_info: Tuple[str, str, str, str]
    ) -> AsyncIterator[str]:
        user, repo, _, number = thread_info
        async for comments in self._get_comments(id):
            result = ""
            orig_message_id = f"<{'/'.join(thread_info)}@github.com>"
            for comment in comments:
                author = comment["author"] or NULL_ACTOR
                message_id = f"<{'/'.join(thread_info)}/c{comment['databaseId']}@github.com>"
                html = comment["bodyHTML"] if self.html else None
                result += "\n\n" + await self._format_email(
                    author.get("name") or author.get("login") or "",
                    author.get("email") or author.get("emailOrNull") or "",
                    isoparse(comment["createdAt"]), subject, comment["body"],
                    message_id, in_reply_to=orig_message_id, html=html)
            yield result

    async def main(self) -> None:
        self.token = os.getenv("HUBMAIL_TOKEN")
        if not self.token:
            fatal("No API token found. Have you set the HUBMAIL_TOKEN " +
                   "environment variable?")

        async with aiohttp.ClientSession() as self.session:
            if self.type == "issue":
                assert self.number is not None
                print(await self.format_issue(
                    self.user, self.repo, self.number))
            elif self.type == "pull":
                assert self.number is not None
                print(await self.format_pull(
                    self.user, self.repo, self.number))
            elif self.type == "issues":
                print(await self.format_issues(self.user, self.repo))
            elif self.type == "pulls":
                print(await self.format_pulls(self.user, self.repo))
            else:
                fatal(f"Subcommand {self.type} not yet implemented")
