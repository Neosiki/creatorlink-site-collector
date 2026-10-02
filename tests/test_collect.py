import json, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import collect

OWNER, ACCT = 'tester', 'a' * 32
H1, H2, LOGO = '1' * 32, '2' * 32, '9' * 32

HOME = f'''<html><body>
<img src="//storage.googleapis.com/cr-resource/image/{ACCT}/{OWNER}/{LOGO}.JPG" data-attach="true">
<ul><li><a href="/gallery-one">Gallery One</a></li><li><a href="/css/x.css">css</a></li>
<li><a href="/gallery-one/view/5">view</a></li><li><a href="/about">About</a></li></ul>
</body></html>'''

class DiscoverTest(unittest.TestCase):
    def test_menus_exclude_assets_and_views(self):
        collect.fetch = lambda url, **k: HOME
        menus, home = collect.discover_menus('https://x.test')
        self.assertEqual([p for _, p in menus], ['gallery-one', 'about'])
        self.assertEqual(menus[0][0], 'Gallery One')

    def test_detect_site(self):
        s = collect.detect_site(HOME + f'<script>x="storage.googleapis.com/cr-resource/image/{ACCT}/{OWNER}/"</script>')
        self.assertEqual((s['owner'], s['acct'], s['logo']), (OWNER, ACCT, LOGO))

class MediaTest(unittest.TestCase):
    def test_owner_only_variants_and_logo(self):
        t = (f'<img src="//storage.googleapis.com/cr-resource/image/{ACCT}/{OWNER}/800/{H1}.JPG">'
             f'<img src="//storage.googleapis.com/cr-resource/image/{ACCT}/{OWNER}/{LOGO}.JPG">'
             f'<img src="//storage.googleapis.com/cr-resource/image/{ACCT}/someoneelse/{H2}.jpg">'
             f'<img src="/700/{H2}.jpg">'
             '<div style="background-image:url(\'https://lh3.googleusercontent.com/AbC_-1=s0\')"></div>')
        got = collect.media_candidates(t, OWNER, ACCT, LOGO)
        keys = [k for k, _, _ in got]
        self.assertIn('st:' + H1, keys)
        self.assertNotIn('st:' + LOGO, keys)                         # 사이트 로고 제외
        self.assertEqual(keys.count('st:' + H2), 1)                  # 다른 계정 이미지는 제외, 상대경로 썸네일만 인정
        cands = dict((k, c) for k, c, _ in got)
        self.assertTrue(cands['st:' + H1][0].endswith(f'/{OWNER}/{H1}.JPG'))   # 원본이 첫 후보
        self.assertTrue(cands['st:' + H1][1].endswith(f'/1920/{H1}.JPG'))
        self.assertEqual(cands['lh3:AbC_-1'], ['https://lh3.googleusercontent.com/AbC_-1=s0'])

class CaptionTest(unittest.TestCase):
    def test_placeholders_removed(self):
        self.assertEqual(collect.clean_caption({'title': '제목', 'caption': '텍스트를 변경할 수 있습니다.', 'content': ''}), ('', ''))
        self.assertEqual(collect.clean_caption({'title': '화엄사', 'caption': 'Print 20x24<br />Edition of 15', 'content': ''}), ('화엄사', 'Print 20x24 Edition of 15'))

class ApiTest(unittest.TestCase):
    def test_full_list_replaces_truncated_first_screen(self):
        first = [{'pid': '77', 'page': 'p', 'seq': '1', 'image': H1 + '.jpg', 'title': '', 'caption': '', 'content': ''}]
        page = 'var x={"view":"12","total":3,"list":' + json.dumps(first) + '};'
        full = [dict(first[0], seq=str(i), image=('%032d' % i) + '.jpg') for i in range(3)]
        calls = []
        def fake(url, data=None, **k):
            calls.append((url, data)); return json.dumps({'list': full, 'total': {'list_total': 3}})
        collect.fetch = fake
        items, meta = collect.api_items('https://x.test', OWNER, page)
        self.assertEqual(len(items), 3)
        self.assertEqual(meta['77'], dict(page='p', total=3, got=3, api_ok=True))
        self.assertIn('/pid/77/sid/tester/spage/p/view/5000', calls[0][0])

    def test_api_failure_falls_back_and_is_flagged(self):
        first = [{'pid': '77', 'page': 'p', 'seq': '1', 'image': H1 + '.jpg', 'title': '', 'caption': '', 'content': ''}]
        page = '"list":' + json.dumps(first)
        def boom(*a, **k): raise OSError('down')
        collect.fetch = boom
        orig_sleep = collect.time.sleep; collect.time.sleep = lambda s: None
        try:
            items, meta = collect.api_items('https://x.test', OWNER, page)
        finally:
            collect.time.sleep = orig_sleep
        self.assertEqual(len(items), 1); self.assertFalse(meta['77']['api_ok'])

class MiscTest(unittest.TestCase):
    def test_ext_sniff_and_safe_name(self):
        self.assertEqual(collect.sniff_ext(b'\xff\xd8\xff\xe0'), '.jpg')
        self.assertEqual(collect.sniff_ext(b'\x89PNG\r\n\x1a\n'), '.png')
        self.assertEqual(collect.safe_name('MORE GALLERIES 판매작품/x'), 'MORE_GALLERIES_판매작품_x')

    def test_video_embeds(self):
        t = '<iframe src="https://www.youtube.com/embed/abc123?wmode=transparent"></iframe><video src="//cdn.x/a.mp4"></video>'
        urls = [m.group(0) for m in list(collect.VIDEO_RE.finditer(t)) + list(collect.EMBED_RE.finditer(t))]
        self.assertEqual(len(urls), 2)

if __name__ == '__main__':
    unittest.main()
