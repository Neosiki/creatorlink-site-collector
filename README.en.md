# creatorlink-site-collector

A small tool that collects artwork images, video URLs and description text from Creatorlink (Addblock) portfolio sites (`*.creatorlink.net`), one menu at a time. It uses Python 3.8+ and the standard library only; Pillow is optional (image size and open checks).

Korean is the primary language of this repository. Full documentation: [docs/INSTALL_AI.md](docs/INSTALL_AI.md) (install for each AI tool), [docs/MANUAL.md](docs/MANUAL.md) (manual), [docs/USAGE_EXAMPLES.md](docs/USAGE_EXAMPLES.md) (examples and FAQ). All of them are in Korean.

## Why it exists

Gallery menus on these sites render only the first 12 works and load the rest through a "load more" request. Scraping what is on screen misses most of the works (in one case 49 images out of 115). This tool calls the same list request the site uses, saves every work, and checks the saved result against the item counts the site reports. After each menu it leaves a report of what was saved and what could not be.

## Install

```bash
git clone https://github.com/Neosiki/creatorlink-site-collector.git
cd creatorlink-site-collector
python3 scripts/collect.py --help
pip install pillow        # optional
```

Verified on Linux. It is written to run the same way on Windows, but that was not verified. If Korean menu names are garbled on Windows, run `$env:PYTHONUTF8=1` in PowerShell first, or use WSL.

## Use

```bash
# 1) list menus and detect the site owner id
python3 scripts/collect.py discover --base https://example.creatorlink.net

# 2) collect one menu (use the "path" value printed by discover; repeat --menu for several)
python3 scripts/collect.py collect --base https://example.creatorlink.net --out ./output --menu <path>

# 3) or collect every menu in turn
python3 scripts/collect.py collect --base https://example.creatorlink.net --out ./output --all

# 4) verify and build one combined mapping file
python3 scripts/collect.py verify --out ./output
python3 scripts/collect.py master --out ./output
```

Add `--lang en` to `collect`, `verify` and `master` for English folder and file names. Exit codes: `collect` returns 0 when complete and 2 when partial or incomplete (run the same command again to resume); `verify` returns 1 when it finds a problem.

A menu is complete when `UNCOVERED` is empty in the `verify` output, every `[saved, total]` pair in `lists` matches, and `rows` equals `files`. `source_file_missing` counts files the site itself has deleted; they cannot be downloaded.

## Use it from an AI tool

Run `python3 scripts/package_skill.py` to build `dist/creatorlink-site-collector/` and a zip with the same name. The folder works for tools that read skill folders (Claude Code, Codex, Gemini CLI); the zip works for tools that take an upload (Claude app, Gemini app, ChatGPT where skills are available). Tools that read `AGENTS.md` (Codex, Cursor, GitHub Copilot, and Gemini CLI with a setting) pick up the file at the repository root. Details and menu paths are in [docs/INSTALL_AI.md](docs/INSTALL_AI.md), written from the vendors' documentation as of 2026-10-02 and not tested by installing on each service.

Chat apps often run code in a sandbox without open internet access, and the Gemini app skills do not support scripts that need internet at all. In that case run the commands on your own computer and paste the `discover` and `verify` output into the chat for the AI to interpret.

## Notes

- Use it only with the site owner's permission. Image copyright belongs to the artist. This repository contains no collected images.
- Captions may contain prices or contact details; check what may be published before reusing them.
- Resolution is limited to the largest size the site stores.
- License: MIT (see [LICENSE](LICENSE)).
