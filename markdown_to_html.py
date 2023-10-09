"""
A quick script for parsing markdown into html.
Supports:
* Lists
* Headings
* Links
* Images
* Formatting (bold, italics, code)
Unsupported:
* Tables
* Code blocks / pre
* Blockquotes
* Comments
"""

from typing import *
from dataclasses import dataclass, field
import re


@dataclass
class MdParseState:
    list_stack: List[Tuple[str, int]] = field(default_factory=list)


def html_escape(line: str) -> str:
    return (line
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('&', '&amp;')
        .replace('"', '&quot;')
        .replace("'", '&#39;')
    )


def process_formatting(line: str) -> str:
    line = re.sub(r'\*\*([^\s](.*?[^\s])?)\*\*', lambda match: f'<b>{match.group(1)}</b>', line)
    line = re.sub(r'\*([^\s](.*?[^\s])?)\*', lambda match: f'<em>{match.group(1)}</em>', line)
    line = re.sub(r'`(.*?)`', lambda match: f'<code>{html_escape(match.group(1))}</code>', line)
    line = re.sub(r'!\[(.*?)\]\((.*?)\)', lambda match: f'<img src="{match.group(2)}" alt="{match.group(1)}"/>', line)
    line = re.sub(r'\[(.*?)\]\((.*?)\)', lambda match: f'<a href="{match.group(2)}">{match.group(1)}</a>', line)
    return line


def process_line(line: str, result: List[str], state: MdParseState) -> None:
    line = line.strip('\n')
    if not line:
        if len(state.list_stack):
            result.extend(f'</{list_type}>\n' for list_type, _ in reversed(state.list_stack))
            state.list_stack.clear()
        return
    line = process_formatting(line)
    for header_level in range(1, 7):
        if line.startswith(('#' * header_level) + ' '):
            header_contents = line[header_level+1:]
            result.append(f'<h{header_level}><a id="{header_contents.replace(" ", "-")}"></a>{header_contents}</h{header_level}>\n')
            return
    if match := re.match(r'^( *)((\*)|(\d+\.)) ', line):
        level = len(match.group(1))
        list_type = 'ul' if match.group(3) else 'ol'
        item_contents = line[match.end(0):]
        if len(state.list_stack) == 0 or level > state.list_stack[-1][1]:
            result.append(f'<{list_type}>\n')
            result.append(f'<li>{item_contents}</li>\n')
            state.list_stack.append((list_type, level))
        elif level < state.list_stack[-1][1]:
            while state.list_stack and level < state.list_stack[-1][1]:
                result.append(f'</{state.list_stack.pop()[0]}>\n')
            result.append(f'<li>{item_contents}</li>\n')
            state.list_stack.append((list_type, level))
        elif state.list_stack[-1][0] != list_type:
            result.append(f'</{state.list_stack.pop()[0]}>\n')
            result.append(f'<{list_type}>\n')
            result.append(f'<li>{item_contents}</li>\n')
            state.list_stack.append((list_type, level))
        else:
            result.append(f'<li>{item_contents}</li>\n')
        return
    if line.startswith('<'):
        result.append(line)
        result.append('\n')
    else:
        result.append(f'<p>{line}</p>\n')

def markdown_to_html(lines: List[str]) -> str:
    result: List[str] = []
    state = MdParseState()
    for line in lines:
        process_line(line, result, state)
    return ''.join(result)

if __name__ == '__main__':
    import os
    ROOT_DIR = os.path.dirname(__file__) 
    with open(os.path.join(ROOT_DIR, 'wol_locations.md'), 'r', encoding='utf-8') as fp:
        md_contents = fp.readlines()
    html_contents = markdown_to_html(md_contents)
    with open(os.path.join(ROOT_DIR, 'templates', 'template.html'), 'r', encoding='utf-8') as fp:
        template_lines = fp.readlines()
    with open(os.path.join(ROOT_DIR, 'index.html'), 'w', encoding='utf-8') as fp:
        for line in template_lines:
            if '$(content)' in line:
                fp.write(html_contents)
            else:
                fp.write(line)
    print('done')
