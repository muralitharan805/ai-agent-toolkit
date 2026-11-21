#!/usr/bin/env python3
"""Export the Context Manager browser UI for static hosting."""
import argparse
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='Destination for index.html, app.js, and style.css')
    output = parser.parse_args().output
    source = Path(__file__).parent / 'static'
    if output.resolve() == source.resolve():
        parser.error('Choose a destination outside the local static source directory')
    output.mkdir(parents=True, exist_ok=True)
    html = (source / 'index.html').read_text(encoding='utf-8')
    html = html.replace('<head>', '<head><meta name="context-manager-mode" content="hosted">'
                        '<meta name="robots" content="noindex">', 1)
    (output / 'index.html').write_text(html, encoding='utf-8')
    for name in ('app.js', 'style.css'):
        shutil.copyfile(source / name, output / name)


if __name__ == '__main__':
    main()
