hubmail
=======

A tool to export GitHub issues and pull requests as email messages.

# Differences from similar tools

The only similar tool of which I am aware is [export-pull-requests][0] by Skye
Shaw, which exports only metadata and uses CSV format instead of email format.
Please let me know if you have found another tool with the same aim as hubmail;
I would be eager to check it out!

[0]: https://github.com/sshaw/export-pull-requests

# Dependencies

Python 3 (latest version recommended), request, docopt, dotenv, dateutil

# Roadmap

- Multipart email support (Markdown as text/plain and HTML)
  + I don't think it would be very helpful to use the plaintext body
  ([`bodyText` in GitHub's GraphQL API][0]) because that would lose some
  information such as hyperlinks and images.
- Expand issue support
- Add support for issue comments
- Support pull requests in addition to issues
- Write documentation
- `mbox` export
  + Currently the output of `hubmail` can be saved to a file with extension
  `.eml` and viewed in Thunderbird
- Keep track of rate limit and pause if it is reached

And possibly:
- Add support for edited issues
  + It may be useful just to act as if the issue was never edited, as Git does
  with commits

[0]: https://developer.github.com/v4/interface/comment/

# License

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

<!-- vim: set tw=80: -->
