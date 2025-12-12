from argparse import ArgumentParser
from bisect import bisect_left
from collections import defaultdict
from datetime import date, timedelta
from functools import partial
from itertools import pairwise
from pathlib import Path
import re
from urllib.parse import urlparse, parse_qs
import xml.etree.ElementTree as etree

from markdown import markdown
from markdown.inlinepatterns import InlineProcessor
from markdown.extensions import Extension
from ruamel.yaml import YAML
from jinja2 import Environment, FileSystemLoader


class AnchorTargetSyntaxProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        el = etree.Element('a')
        el.set('href', m.group('url'))
        el.set('target', m.group('target'))
        el.text = m.group('text')

        return el, m.start(), m.end()


class AnchorTargetSyntaxExtension(Extension):
    def extendMarkdown(self, md):
        md.inlinePatterns.register(
            AnchorTargetSyntaxProcessor(r'\[(?P<text>[^\]]+)\]\((?P<url>[^;)]+);\s+(?P<target>[^;)]+)\)', md),
            'anchor_target_syntax',
            180
        )

def ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

def to_id(value):
    value = value.lower()
    value = re.sub(r'\s+', '-', value)         # replace whitespace with hyphens
    value = re.sub(r'[^a-z0-9\-_]', '', value) # remove invalid characters
    value = re.sub(r'^([^a-z]+)', '', value)   # ensure it starts with a letter
    return value

def strip_outer_tag(string):
    if (m := re.fullmatch(r'<.+?>(.+)</.+?>', string, re.DOTALL)) is not None:
        return m.group(1)
    return string

parser = ArgumentParser()
parser.add_argument('source', type=Path)
parser.add_argument('dest', type=Path)
args = parser.parse_args()

env = Environment(loader=FileSystemLoader("."))
env.filters['markdown'] = partial(markdown, extensions=[AnchorTargetSyntaxExtension()])
env.filters['ordinal'] = ordinal
env.filters['to_id'] = to_id
env.filters['strip_outer_tag'] = strip_outer_tag


yaml = YAML(typ='safe')
with open('content.yml') as f:
    events = yaml.load(f)

events = [
    ev | {
        # parse the key `v=…` from https://youtube.com/watch?v=…&…
        'youtube_key': ''.join(parse_qs(urlparse(ev['youtube']).query).get('v', [])),
    } for ev in events
]

events = sorted(events, key=lambda e: e['date'])
event_dates = [ev['date'] for ev in events]
upcoming_idx = bisect_left(event_dates, date.today())

events = [*reversed(events)]
upcoming_idx = len(events) - upcoming_idx

if upcoming_idx == 0: # no yaml entry for an upcoming event
    upcoming, past_events = None, events
else:
    upcoming, *past_events = events[upcoming_idx-1:]
past_events = [pe for pe in past_events if not pe['cancelled']]


for src_path in args.source.rglob('*.j2'):
    rel_path = src_path.relative_to(args.source).with_suffix("")
    dst_path = args.dest / rel_path
    template = env.get_template(str(src_path))

    content = template.render(
        upcoming=upcoming,
        past_events=past_events,
        current_page=str(rel_path.parent / rel_path.stem),
    )
    dst_path.write_text(content)

