#!/usr/bin/env python3
"""Turns a saved SMF forum page into plain text, one post at a time.

Usage: forum-text.py PAGE.html > out.txt

Keeps the post bodies (class "inner"), the poster and the date where present. The
output is another person's writing: keep it under build/ (git-ignored), summarise it in
the docs, do not copy it into the repository.
"""
import html
import re
import sys

page = open(sys.argv[1], encoding="utf-8", errors="replace").read()
posts = re.split(r'<div class="post_wrapper', page)[1:] or re.split(r'<div class="windowbg', page)[1:]
for n, post in enumerate(posts, 1):
    who = re.search(r'<h4>\s*(?:<a [^>]*>)?([^<]+)', post)
    when = re.search(r'(?:&#171;|«)\s*<strong>[^<]*</strong>\s*([^&<»]+)', post)
    body = re.search(r'<div class="inner"[^>]*>(.*?)</div>\s*</div>\s*<div class="moderatorbar"|<div class="inner"[^>]*>(.*)', post, re.S)
    text = (body.group(1) or body.group(2)) if body else post
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"</(p|div|li|tr)>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text).strip()
    print("=== post %d  %s  %s" % (n, who.group(1).strip() if who else "?", when.group(1).strip() if when else ""))
    print(text[:80000])
    print()
