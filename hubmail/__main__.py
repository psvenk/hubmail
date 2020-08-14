from hubmail import Hubmail

import argparse
import textwrap
import asyncio
import os

def get_parser():
    parser = argparse.ArgumentParser(
        prog="hubmail",
        description=textwrap.dedent(f"""\
            Export GitHub issues and pull requests as email messages
            in mbox format (RFC 4155).
            """))
    subparsers = parser.add_subparsers(
        title="subcommands", dest="subcommand", required=True)

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "user", metavar="USER",
        help="The username of the owner of the repository")
    parent_parser.add_argument(
        "repo", metavar="REPO",
        help="The name of the repository")
    parent_parser.add_argument(
        "-c", "--comments", metavar="N", type=int, nargs="?", default=0,
        const=None,
        help=textwrap.dedent("""\
            Include the first %(metavar)s comments is %(metavar)s is positive,
            otherwise the latest %(metavar)s comments
            [default: all comments if -c provided, otherwise no comments]
            """))
    parent_parser.add_argument(
        "-w", "--wrap", metavar="COLS", type=int, nargs="?", const=72,
        help=textwrap.dedent("""\
            Wrap each line of text to %(metavar)s columns
            [default: 72 if -w provided]
            """))
    parent_parser.add_argument(
        "--extended-subject", action="store_true",
        help=textwrap.dedent("""\
            Include the repository name and thread number in each email's
            subject line (like GitHub notification emails)
            """))
    parent_parser.add_argument(
        "--html", action="store_true",
        help=textwrap.dedent("""\
            Generate multipart emails with a HTML part (rendered Markdown
            from GitHub)
            """))

    issue_parser = subparsers.add_parser(
        "issue", parents=[parent_parser],
        usage="%(prog)s [options] USER REPO NUMBER",
        description="Export one issue in mbox format")
    pull_parser = subparsers.add_parser(
        "pull", parents=[parent_parser],
        usage="%(prog)s [options] USER REPO NUMBER",
        description="Export one pull request in mbox format")

    issue_parser.add_argument(
        "number", metavar="NUMBER", type=int,
        help="The number of the issue")
    pull_parser.add_argument(
        "number", metavar="NUMBER", type=int,
        help="The number of the pull request")

    repo_parent_parser = argparse.ArgumentParser(
        add_help=False, parents=[parent_parser])

    issues_parser = subparsers.add_parser(
        "issues", parents=[repo_parent_parser],
        usage="%(prog)s [options] USER REPO",
        description="Export issues from a repository in mbox format")
    pulls_parser = subparsers.add_parser(
        "pulls", parents=[repo_parent_parser],
        usage="%(prog)s [options] USER REPO",
        description="Export pull requests from a repository in mbox format")

    issues_parser.add_argument(
        "-t", "--threads", metavar="N", type=int,
        help=textwrap.dedent("""\
            Include the first %(metavar)s threads is %(metavar)s is positive,
            otherwise the latest %(metavar)s threads [default: all threads]
            """))
    pulls_parser.add_argument(
        "-t", "--threads", metavar="N", type=int,
        help=textwrap.dedent("""\
            Include the first %(metavar)s threads is %(metavar)s is positive,
            otherwise the latest %(metavar)s threads [default: all threads]
            """))

    return parser

def main():
    asyncio.run(Hubmail(get_parser().parse_args()).main())

if __name__ == "__main__":
    main()
