hubmail
=======

A tool to export GitHub issues and pull requests as email messages.

## Differences from similar tools

The only similar tool of which I am aware is [export-pull-requests][0] by Skye
Shaw, which exports only metadata and uses CSV format instead of email format.

[0]: https://github.com/sshaw/export-pull-requests

## Dependencies

Python 3.8, [aiohttp][aiohttp], [dateutil][dateutil]

Optional: [mistletoe][mistletoe] (for attaching linked images),
[argparse-manpage][argparse-manpage] (for building a man page), POSIX shell
(for running the testing script)

`hubmail` may also work on Python 3.7, but I have not tested it there.

If you use pip, you can run `pip install -r requirements.txt` to install all
required and optional dependencies.

[aiohttp]: https://pypi.org/project/aiohttp/
[dateutil]: https://pypi.org/project/python-dateutil/
[mistletoe]: https://pypi.org/project/mistletoe/
[argparse-manpage]: https://pypi.org/project/argparse-manpage/

## Usage

1. Create a peronal access token on GitHub's website following [these
   instructions][1] with the scopes `public_repo`, `read:user`, and
   `user:email`.
2. Set the environment variable `HUBMAIL_TOKEN` to your token.
3. Run `./run_hubmail -h` for usage information, and
   `./run_hubmail SUBCOMMAND -h` for usage information for a subcommand (e.g.
   `issue`, `pull`).

To install `hubmail` to your `$PATH`, run `python3 setup.py install`. This will
also install man page documentation if you have `argparse-manpage` installed
(run `man 1 hubmail` or `man -l man/hubmail.1` to view it).

For example, to fetch the oldest 10 issues and the newest 5 pull requests from
`user/repo`, wrapped to 72 characters and with the first 20 comments on each,
output to the file `repo.mbox`:
```console
$ hubmail issues -t10 -c20 -w72 user repo >  repo.mbox
$ hubmail pulls  -t-5 -c20 -w72 user repo >> repo.mbox
```

[1]: https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line

## Testing

Create a file with contents like the following and put it at `test/config`:
```sh
#!/bin/sh

# Location of hubmail executable
# (hubmail if you have installed it in your $PATH; ./run_hubmail otherwise)
hubmail=./run_hubmail

dir=messages

# Send all messages to this file (leave blank to disable)
all=all.mbox

# Format of each line: ARGUMENTS:FILENAME
cmds="
issue -c -w --  myuser myrepo 1:file1.mbox
pull  -c20 -w72 myuser myrepo 2:file1.mbox
"
```
Then run `./test/test` to run `hubmail` and output files to the chosen
directory with the chosen filenames.

## Features

- Outputs in the mbox format as specified in
  [RFC 4155](https://tools.ietf.org/html/rfc4155)
- Can fetch one issue or pull request (by number), or many issues or pull
  requests in a repository, optionally with comments with support for forward
  and reverse pagination
- Pull requests are exported as both patches and discussions
- The Message-ID, In-Reply-To, and References headers are used to support
  conversation threading
- Optional text wrapping with quote recognition
- Supports comments authored by users, organizations, and bots
- Supports formatting subject line like GitHub notification emails
- Linked images are downloaded and added as attachments
- Supports compiling multipart emails with Markdown rendered to HTML

## Roadmap

- Add support for changing message IDs to differ from the GitHub notification
  emails
- Include non-comment actions; e.g., pull request reviews and merges
- Keep track of rate limit and pause if it is reached
- Add support for keeping usernames instead of real names (or both?)
- More graceful error handling (e.g. when a repository is not found)

And possibly:
- Add support for edited issues
  + It may be useful just to act as if the issue was never edited, as Git does
  with commits

## Bugs

`asyncio` throws exceptions on Windows about cancelling overlapping futures and
the event loop being closed, but hubmail works fine otherwise on Windows (the
exceptions can be ignored by redirecting stderr)

## License

SPDX-License-Identifier: LGPL-2.1-or-later

hubmail: a tool to export GitHub issues and pull requests as email messages

Copyright (c) 2020 psvenk

This library is free software; you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the Free
Software Foundation; either version 2.1 of the License, or (at your option) any
later version.

This library is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
details.

You should have received a copy of the GNU Lesser General Public License along
with this library; if not, write to the Free Software Foundation, Inc., 51
Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

<!-- vim: set tw=79: -->
