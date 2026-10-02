import os, sys, tempfile, unittest, zipfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import package_skill as ps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class PackageSkillTest(unittest.TestCase):
    def test_zip_structure_matches_skill_name(self):
        with tempfile.TemporaryDirectory() as out:
            dest, zpath = ps.build(ROOT, out)
            names = zipfile.ZipFile(zpath).namelist()
            self.assertTrue(all(n.startswith(ps.NAME + '/') for n in names))
            self.assertIn(ps.NAME + '/SKILL.md', names)
            self.assertIn(ps.NAME + '/scripts/collect.py', names)
            self.assertTrue(os.path.isfile(os.path.join(dest, 'SKILL.md')))

    def test_skill_name_in_frontmatter(self):
        self.assertEqual(ps.skill_name(os.path.join(ROOT, 'SKILL.md')), ps.NAME)

    def test_rebuild_is_idempotent(self):
        with tempfile.TemporaryDirectory() as out:
            ps.build(ROOT, out)
            _, z2 = ps.build(ROOT, out)
            self.assertEqual(len(zipfile.ZipFile(z2).namelist()), len(ps.INCLUDE))


if __name__ == '__main__':
    unittest.main()
