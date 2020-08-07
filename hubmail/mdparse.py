# This file is part of hubmail.
# SPDX-License-Identifier: LGPL-2.1-or-later

import json

from mistletoe import Document
from mistletoe.ast_renderer import ASTRenderer

def get_image_urls(text):
    """Gets image URLs from a Markdown document"""
    with ASTRenderer() as renderer:
        ast = json.loads(renderer.render(Document(text)))
    return _get_image_urls(ast)

def _get_image_urls(ast):
    """Returns an array of URLs given a mistletoe AST"""
    if ast["type"] == "Image" and ast["src"]:
        return [ast["src"]]
    elif "children" in ast:
        return sum([_get_image_urls(child) for child in ast["children"]], [])
    else:
        return []
