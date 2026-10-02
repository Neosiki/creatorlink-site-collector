# AI 도구별 설치 가이드

작성 기준일은 2026-10-02입니다. 각 서비스의 메뉴 경로와 조건은 공식 문서(문서 끝에 링크)를 보고 적었고, 서비스 화면에서 직접 설치해 확인하지는 않았습니다. 화면이 다르면 공식 문서를 우선하십시오. `scripts/collect.py` 자체는 Linux에서 실행해 확인했습니다.

## 0. 먼저 알아 둘 것: 수집은 어디서 실행되는가

이 도구는 스크립트가 인터넷에서 이미지를 내려받아 폴더에 저장합니다. 그래서 AI 도구를 둘로 나누어 생각해야 합니다.

| 구분 | 도구 | 수집 실행 | 권장 방식 |
|---|---|---|---|
| 내 컴퓨터에서 명령을 실행하는 에이전트 | Claude Code, Codex(CLI·IDE), Gemini CLI, Cursor, GitHub Copilot 에이전트, Windsurf | 가능 | 스킬 또는 AGENTS.md를 설치하고 "이 사이트를 수집해 줘"라고 요청 |
| 채팅 앱 | Claude 앱, ChatGPT, Gemini 앱 | 환경에 따라 다름 | 스킬을 설치하되, 인터넷이 막히면 내 PC에서 명령을 실행하고 결과를 AI에게 붙여 넣어 해석 |

Gemini 앱의 스킬은 공식 도움말에 "인터넷이 필요한 스크립트는 지원하지 않는다"고 적혀 있어, 이 도구의 수집 단계를 앱 안에서 돌릴 수 없습니다. Claude 앱과 ChatGPT도 코드 실행 환경의 네트워크 허용 범위에 따라 사이트 접속이 막힐 수 있습니다. 설치한 뒤 AI에게 `discover`를 먼저 시켜 보고, 403이나 연결 오류가 나면 아래 "PC에서 직접 실행하고 AI에게는 해석만" 방식으로 바꾸십시오.

## 1. 공통 준비

Python 3.8 이상이 필요합니다. 설치할 패키지는 없습니다(Pillow는 선택).

```bash
git clone https://github.com/Neosiki/creatorlink-site-collector.git
cd creatorlink-site-collector
python3 --version        # Windows는 python --version
python3 -m unittest discover -s tests    # 선택: 테스트 11개
```

### 스킬 배포 파일 만들기

도구마다 폴더째 복사하거나 zip을 올립니다. 아래 명령 한 번으로 둘 다 만들어집니다.

```bash
python3 scripts/package_skill.py        # 결과: dist/creatorlink-site-collector/ 와 dist/creatorlink-site-collector.zip
```

zip 안의 최상위 폴더 이름이 `SKILL.md`의 `name`(`creatorlink-site-collector`)과 같아야 Claude 앱 업로드가 됩니다. 이 스크립트가 그 구조로 만듭니다. 포함되는 파일은 `SKILL.md`, `LICENSE`, `scripts/collect.py`, `docs/SITE_STRUCTURE.md`, `docs/DEVELOPMENT_LOG.md` 다섯 개입니다.

## 2. 도구별 설치

### Claude Code

개인 스킬로 설치하면 모든 프로젝트에서 쓰입니다.

```bash
# macOS / Linux
mkdir -p ~/.claude/skills && cp -r dist/creatorlink-site-collector ~/.claude/skills/
```
```powershell
# Windows PowerShell
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse dist\creatorlink-site-collector "$HOME\.claude\skills\"
```

한 프로젝트에서만 쓰려면 그 프로젝트의 `.claude/skills/`에 같은 폴더를 복사합니다. Claude Code를 다시 시작한 뒤 "Creatorlink 사이트에서 이미지를 모두 수집하는 스킬을 쓸 수 있어?"라고 물어 인식됐는지 확인합니다. 사용은 "`https://○○.creatorlink.net`의 이미지를 메뉴별로 전부 모아 줘"처럼 요청하면 됩니다.

### Claude 앱(claude.ai, 데스크톱)

1. `dist/creatorlink-site-collector.zip`을 준비합니다.
2. 설정(Settings) > Capabilities > Skills에서 Upload skill을 눌러 zip을 올립니다.
3. 조건: Pro, Max, Team, Enterprise 플랜이고 코드 실행과 파일 생성 기능이 켜져 있어야 합니다. 개인 단위 설치라 팀원마다 올려야 합니다.
4. 올린 뒤 대화에서 "creatorlink-site-collector 스킬로 `https://○○.creatorlink.net` 메뉴 목록부터 보여 줘"라고 요청합니다. 접속이 막히면 3절의 PC 직접 실행 방식을 씁니다.

업로드가 실패하면 zip 안 최상위 폴더 이름이 스킬 이름과 같은지 확인하십시오. 스킬은 코드를 실행하므로 올리기 전에 `scripts/collect.py`를 읽어 보시기를 권합니다.

### ChatGPT

- **스킬을 쓸 수 있는 경우**: 공식 도움말은 ChatGPT Business, Enterprise, Healthcare, Edu(워크스페이스 설정에 따름)에서 스킬을 지원한다고 합니다. Plugins > Plugin Directory > Skills 탭 > Create > Upload from your computer 순서로 올립니다. 올린 뒤 대화에서 `@creatorlink-site-collector`로 부르거나, 작업 설명이 맞으면 ChatGPT가 알아서 고릅니다. 업로드 파일 형식(zip 여부)은 도움말에 명시되어 있지 않으니, 안 되면 `dist/creatorlink-site-collector/` 폴더를 올려 보십시오.
- **스킬이 없는 플랜**: Project의 지침란이나 Custom GPT의 지침란에 저장소의 `AGENTS.md` 내용을 붙여 넣고, 수집 명령은 내 PC에서 실행합니다(3절).

### OpenAI Codex(CLI, IDE 확장)

두 가지 방식이 있고 함께 써도 됩니다.

- **스킬**: Codex는 저장소의 `.agents/skills`, 개인용 `$HOME/.agents/skills`에서 스킬을 읽습니다.
  ```bash
  mkdir -p ~/.agents/skills && cp -r dist/creatorlink-site-collector ~/.agents/skills/
  ```
  Codex에서 `$creatorlink-site-collector`로 직접 부르거나, 요청이 맞으면 자동으로 골라 씁니다. 스킬 변경은 자동 감지되고, 안 보이면 Codex를 재시작합니다.
- **AGENTS.md**: 이 저장소를 clone해서 그 폴더에서 Codex를 실행하면 루트의 `AGENTS.md`를 자동으로 읽습니다. 모든 저장소에 적용하려면 `~/.codex/AGENTS.md`에 내용을 넣습니다. 합쳐진 지침이 32KiB(기본값)를 넘으면 뒤쪽이 잘립니다.

### Gemini 앱(웹, 모바일, Mac 앱)

1. 설정 > Skills(gemini.google.com)로 갑니다.
2. Upload를 눌러 `SKILL.md`가 들어 있는 폴더 또는 zip(`dist/creatorlink-site-collector.zip`)을 올립니다. 스킬 이름은 소문자와 하이픈만 쓸 수 있고, 이 스킬 이름은 조건에 맞습니다. 전체 크기는 100MB 이하여야 합니다.
3. 조건: 만 18세 이상, 개인 Google 계정(업무·학교 계정 제외), Keep Activity 켜기입니다.
4. 이 앱의 스킬은 인터넷이 필요한 스크립트를 실행하지 못합니다. 그래서 수집 자체는 PC에서 하고, Gemini에게는 `verify` 출력과 대응표 CSV를 붙여 넣어 점검·정리를 맡기는 용도로 쓰십시오(3절).

### Gemini CLI

- **스킬**: `~/.gemini/skills/`(개인), `.gemini/skills/`(작업 폴더, 신뢰한 폴더만), `.agents/skills/`(별칭)에서 발견합니다.
  ```bash
  mkdir -p ~/.gemini/skills && cp -r dist/creatorlink-site-collector ~/.gemini/skills/
  # 또는
  gemini skills install dist/creatorlink-site-collector
  ```
  Gemini CLI 안에서 `/skills list`로 보이는지, 새로 넣은 직후에는 `/skills reload`를 실행합니다. 공식 문서에 설치 명령이 URL도 받는다고 나오지만, 이 저장소의 GitHub 주소로는 확인하지 않았습니다. 폴더 경로로 설치하는 방법을 권합니다.
- **GEMINI.md 방식**: Gemini CLI는 기본으로 `GEMINI.md`를 읽습니다. 이 저장소의 `AGENTS.md`를 쓰려면 설정 파일(`settings.json`)에 파일 이름을 추가합니다.
  ```json
  { "context": { "fileName": ["AGENTS.md", "GEMINI.md"] } }
  ```
  적용된 내용은 `/memory show`로 볼 수 있습니다.

### Cursor

- 이 저장소를 clone해서 Cursor로 열면 루트의 `AGENTS.md`를 지침으로 씁니다(루트 전용, 범위 지정 불가).
- 필요할 때만 불러 쓰려면 `.cursor/rules/creatorlink-collector.mdc`를 만듭니다. 설명(`description`)이 있으면 에이전트가 요청에 맞을 때 스스로 가져다 씁니다.
  ```
  ---
  description: Creatorlink(애드블록) 사이트의 이미지·영상 주소·설명 글을 메뉴 단위로 수집할 때 쓴다
  alwaysApply: false
  ---
  이 저장소의 AGENTS.md 지침을 따른다. 수집은 scripts/collect.py의 discover, collect, verify, master 순서로 실행한다.
  ```
- 규칙은 Agent와 Inline Edit에 적용되고 Cursor Tab에는 적용되지 않습니다.

### GitHub Copilot

- 저장소 어디에 있든 가장 가까운 `AGENTS.md`가 우선 적용됩니다. 이 저장소는 루트에 있으므로 별도 설정이 필요 없습니다.
- 다른 저장소에서 쓰려면 그 저장소에 `.github/copilot-instructions.md`를 만들고 `AGENTS.md`의 내용을 넣습니다.
- Copilot은 풀 리퀘스트의 head 브랜치에 있는 지침을 읽습니다.

### Windsurf와 그 밖의 에이전트

`AGENTS.md`를 읽는 도구는 저장소 루트의 파일을 그대로 씁니다. 그렇지 않은 도구는 규칙·메모리·프로젝트 지침 기능에 `AGENTS.md` 내용을 붙여 넣으십시오. Windsurf의 규칙 파일 위치는 이번에 공식 문서로 확인하지 못했습니다.

## 3. PC에서 직접 실행하고 AI에게는 해석만 맡기는 방식

수집이 막히는 환경에서는 이렇게 나누면 어느 AI에서든 쓸 수 있습니다.

1. 내 PC 터미널에서 실행합니다.
   ```bash
   python3 scripts/collect.py discover --base https://○○.creatorlink.net
   python3 scripts/collect.py collect  --base https://○○.creatorlink.net --out ./output --menu <path>
   python3 scripts/collect.py verify   --out ./output
   ```
2. `discover` 출력과 `verify` 출력(한 줄 JSON)을 AI 대화창에 붙여 넣고 "AGENTS.md 지침대로 메뉴별 보고를 만들어 줘"라고 요청합니다.
3. 대응표 CSV(`파일명대응표.csv`)는 캡션 정리, 도록 순서 정리, 누락 점검에 AI를 쓰는 데 알맞습니다. 캡션에 가격과 연락처가 들어 있을 수 있으니 올리기 전에 확인하십시오.

## 4. 설치 확인 체크리스트

- [ ] `python3 scripts/collect.py --help`가 하위 명령 네 개를 보여 준다.
- [ ] `discover`가 메뉴 목록과 `owner`를 출력한다(403이면 네트워크 허용 목록을 확인).
- [ ] AI에게 "이 스킬(또는 지침)로 무엇을 할 수 있는지 설명해 줘"라고 했을 때 `discover → collect → verify → master` 순서를 말한다.
- [ ] 메뉴 하나를 받고 `verify`의 `ok`가 `true`다.

## 5. 업데이트와 제거

저장소에서 `git pull`을 하고 `python3 scripts/package_skill.py`를 다시 실행한 뒤, 복사한 폴더를 교체하거나 zip을 다시 올립니다. 제거는 복사한 폴더를 지우거나, 앱의 스킬 목록에서 삭제합니다(Gemini CLI는 `gemini skills uninstall creatorlink-site-collector`).

## 참고한 공식 문서

- Claude: [Agent Skills 개요](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview), [Claude에서 스킬 사용하기](https://support.claude.com/en/articles/12512180-using-skills-in-claude)
- ChatGPT: [Skills in ChatGPT](https://help.openai.com/en/articles/20001066-skills-in-chatgpt)
- Codex: [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [Codex 스킬 만들기](https://learn.chatgpt.com/codex/build-skills)
- Gemini: [Gemini 앱 스킬 만들기와 관리](https://support.google.com/gemini/answer/17094296), [Gemini CLI 스킬 시작하기](https://geminicli.com/docs/cli/tutorials/skills-getting-started/), [GEMINI.md 컨텍스트](https://google-gemini.github.io/gemini-cli/docs/cli/gemini-md.html)
- Cursor: [Rules](https://docs.cursor.com/context/rules)
- GitHub Copilot: [저장소 사용자 지침](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions)
