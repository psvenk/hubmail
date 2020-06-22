hubmail
=======

A tool to export GitHub issues and pull requests as email messages.

## Differences from similar tools

The only similar tool of which I am aware is [export-pull-requests][0] by Skye
Shaw, which exports only metadata and uses CSV format instead of email format.
Please let me know if you have found another tool with the same aim as hubmail;
I would be eager to check it out!

[0]: https://github.com/sshaw/export-pull-requests

## Dependencies

Python 3.8, aiohttp, dateutil

Optional: dotenv (for storing the API key in a `.env` file)

This may also work on Python 3.7, but I have not tested that.

## Usage

1. Create a peronal access token on GitHub's website following [these
   instructions][1].
2. Set the environment variable `HUBMAIL_TOKEN` to your token. If you have the
   Python `dotenv` library installed, you can alternatively create a file
   `.env` with the line `HUBMAIL_TOKEN=your_token_here`.
3. Run `./hubmail` for usage information.

For example, to fetch all issues and pull requests from `user/repo`, wrapped to
72 characters and with the first 20 comments on each, output to the file
`repo.mbox`:
```console
$ ./hubmail issues -c20 -w72 user repo >  repo.mbox
$ ./hubmail pulls  -c20 -w72 user repo >> repo.mbox
```

[1]: https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line

## Testing

Create a file with contents like the following and put it at `test/config`:
```sh
#!/bin/sh
dir=messages
# Send all messages to this file (leave blank to disable)
all=all.mbox

# Format:
# ARGUMENTS:FILENAME
cmds="
issue -c -w --  myuser myrepo 1:file1.mbox
pull  -c20 -w72 myuser myrepo 2:file1.mbox
"
```
Then run `./test/test` to run `hubmail` and output files to the chosen
directory with the chosen filenames.

## Roadmap

- Allow fetching the last N issues/pull requests instead of the first N
- Add support for including thread info in subject line (like GitHub
  notification emails)
- Assign different message IDs to different commits in a pull request
- Include non-comment actions; e.g., pull request reviews and merges
- Keep track of rate limit and pause if it is reached
- Multipart email support with HTML part

And possibly:
- Add support for edited issues
  + It may be useful just to act as if the issue was never edited, as Git does
  with commits

## Bugs

- If a commit in a pull request has a subject spanning multiple lines, the
  message ID is put after the first line
  + Maybe this can be solved by using `email.message.EmailMessage`

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
