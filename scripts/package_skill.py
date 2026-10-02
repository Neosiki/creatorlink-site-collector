#!/usr/bin/env python3
"""스킬 배포용 폴더와 zip을 만든다.

AI 도구마다 스킬을 받는 방식이 다르다. 폴더째 복사하는 도구(Claude Code, Codex, Gemini CLI)와
zip을 올리는 도구(Claude 앱, Gemini 앱, ChatGPT)가 모두 쓸 수 있도록, 필요한 파일만 담은
`creatorlink-site-collector/` 폴더와 같은 이름의 zip을 만든다. zip 안의 최상위 폴더 이름은
SKILL.md의 name과 같아야 업로드가 된다.

사용: python3 scripts/package_skill.py [--out dist]
"""
import argparse, os, re, shutil, sys, zipfile

NAME = 'creatorlink-site-collector'
INCLUDE = ['SKILL.md', 'LICENSE', 'scripts/collect.py', 'docs/SITE_STRUCTURE.md', 'docs/DEVELOPMENT_LOG.md']


def skill_name(skill_md):
    m = re.match(r'---\s*\n(.*?)\n---', open(skill_md, encoding='utf-8').read().replace('\r\n', '\n'), re.S)
    n = re.search(r'^name:\s*(\S+)', m.group(1), re.M) if m else None
    return n.group(1) if n else None


def build(root, out):
    got = skill_name(os.path.join(root, 'SKILL.md'))
    if got != NAME:
        raise SystemExit('SKILL.md의 name(%r)이 %r와 다릅니다.' % (got, NAME))
    missing = [r for r in INCLUDE if not os.path.exists(os.path.join(root, r))]
    if missing:
        raise SystemExit('필요한 파일이 없습니다: %s' % missing)
    dest = os.path.join(out, NAME)
    if os.path.isdir(dest):
        shutil.rmtree(dest)                                  # 이 스크립트가 만든 배포 폴더만 다시 만든다
    for rel in INCLUDE:
        os.makedirs(os.path.dirname(os.path.join(dest, rel)), exist_ok=True)
        shutil.copyfile(os.path.join(root, rel), os.path.join(dest, rel))
    zpath = os.path.join(out, NAME + '.zip')
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        for rel in sorted(INCLUDE):
            zi = zipfile.ZipInfo('%s/%s' % (NAME, rel), date_time=(2026, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            z.writestr(zi, open(os.path.join(root, rel), 'rb').read())
    return dest, zpath


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', default='dist', help='결과를 둘 폴더(기본 dist)')
    a = ap.parse_args(argv)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dest, zpath = build(root, os.path.abspath(a.out))
    print('폴더:', dest)
    print('zip :', zpath)


if __name__ == '__main__':
    main()
