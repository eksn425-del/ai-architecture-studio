"""Render the existing K SVG without redesign; build-only Playwright/Pillow deps."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', type=Path, required=True, help='Existing Chromium/Edge executable; no automatic download')
    parser.add_argument('--png', type=Path, required=True, help='256 px intermediate on project artifact drive')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1]/'app/static/kstudio.ico')
    args = parser.parse_args()
    from playwright.sync_api import sync_playwright
    from PIL import Image
    source = Path(__file__).resolve().parents[1]/'app/static/k-monogram.svg'
    svg = source.read_text(encoding='utf-8')
    args.png.parent.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=str(args.browser), headless=True)
        page = browser.new_page(viewport={'width':256,'height':256},device_scale_factor=1)
        page.set_content('<!doctype html><meta charset="utf-8"><style>html,body{margin:0;width:256px;height:256px;background:#f5f3e9}svg{display:block;width:256px;height:256px}</style>'+svg)
        page.screenshot(path=str(args.png), full_page=False, animations='disabled')
        browser.close()
    sizes=[(n,n) for n in (16,24,32,48,64,128,256)]
    with Image.open(args.png) as image:
        image.convert('RGBA').save(args.output,format='ICO',sizes=sizes)
    with Image.open(args.output) as image:
        assert image.ico.sizes()==set(sizes)
    print(json.dumps({'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'output':str(args.output),'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),
        'sizes':[n[0] for n in sizes],'background':'#f5f3e9','original_svg_unchanged':True},ensure_ascii=False))


if __name__ == '__main__':
    main()
