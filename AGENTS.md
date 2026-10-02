# creatorlink-site-collector 작업 지침

Creatorlink(애드블록) 사이트(`*.creatorlink.net`)의 작품 이미지, 영상 주소, 설명 글을 메뉴 단위로 수집하는 저장소입니다. 이 파일은 Codex, Cursor, GitHub Copilot, Gemini CLI(설정 필요) 등 AGENTS.md를 읽는 도구와, 지침란에 붙여넣는 ChatGPT·Gemini 앱·Claude 앱 프로젝트에서 같이 씁니다. 스킬 형식(`SKILL.md`)과 내용이 같습니다.

## 먼저 확인할 것
1. 수집 권한: 사이트 운영자(작가, 매장)가 도록 제작 같은 용도로 쓰도록 허락했는지 사용자에게 묻습니다. 저작권은 작가에게 있습니다.
2. 네트워크: 사이트 도메인, `storage.googleapis.com`, `lh3.googleusercontent.com` 세 곳에 접속할 수 있어야 합니다. 하나라도 막히면 403이 나옵니다. 막힌 채로 완료라고 보고하지 않습니다.
3. 코드를 실행할 수 없거나 인터넷이 막힌 환경(채팅 앱의 샌드박스 등)이면 수집을 직접 하려 하지 말고, 사용자 PC에서 실행할 명령을 알려 주고 결과(`verify` 출력, 대응표)를 받아 해석합니다.

## 명령(Python 3.8 이상, 표준 라이브러리만 사용)
```
python3 scripts/collect.py discover --base https://<사이트>.creatorlink.net
python3 scripts/collect.py collect  --base https://<사이트>.creatorlink.net --out ./output --menu <path>
python3 scripts/collect.py collect  --base https://<사이트>.creatorlink.net --out ./output --all
python3 scripts/collect.py verify   --out ./output
python3 scripts/collect.py master   --out ./output
```
- `--menu`에는 `discover` 출력의 `path` 값을 넣습니다(메뉴 이름이 아닙니다). 여러 번 지정할 수 있습니다.
- 종료 코드 0은 완료, 2는 일부만 받음(`PARTIAL`) 또는 불완전, 1은 `verify`에서 문제 발견입니다. `PARTIAL`이면 같은 명령을 다시 실행하면 이어받습니다. 백그라운드 실행은 쓰지 않습니다.

## 절차
1. `discover`로 메뉴와 소유자 id를 확인합니다.
2. 메뉴 하나를 `collect --menu`로 받고 `verify`를 돌려 보고합니다. 사용자가 허락하면 `--all`로 이어갑니다.
3. 끝나면 `verify`와 `master`를 실행합니다.

## 보고에 넣을 것(메뉴마다)
이미지 장수, 최대·최소 가로 크기, 총 용량, 영상 유무, 목록 API 작품 수 대비 저장 수, 받지 못한 항목과 이유. 상세 페이지 404 개수는 따로 적되 작품이 빠진 것처럼 쓰지 않습니다(사진은 목록 데이터로 확보됩니다).

## 규칙
- "전부 확보"라고 말하기 전에 `verify`의 `UNCOVERED`가 비어 있고 `lists`의 (받은 수, 전체 수)가 같은지 확인합니다.
- `source_file_missing`은 사이트에서 파일이 삭제된 경우라 받을 수 없습니다. 숨기지 말고 개수를 보고합니다.
- 캡션에 가격이나 작가 연락처가 있을 수 있습니다. 도록 등에 옮기기 전에 공개 범위를 사용자에게 알립니다.
- 해상도는 사이트 저장소의 최대 크기가 한계입니다. 인쇄용 원본은 작가에게 따로 받아야 합니다.
- 이전 실행의 남은 파일은 지우지 않고 `_이전파일`(영문 모드는 `_stale`)로 옮깁니다. 삭제는 사용자가 합니다.
- 수집한 이미지는 저장소에 커밋하지 않습니다(`.gitignore`에 `output/` 포함).

더 자세한 내용은 `docs/MANUAL.md`(사용 매뉴얼), `docs/USAGE_EXAMPLES.md`(사례와 FAQ), `docs/SITE_STRUCTURE.md`(사이트 구조)를 봅니다.
