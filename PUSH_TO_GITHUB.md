# GitHub에 올리는 방법

이 폴더는 이미 `git init`과 첫 커밋이 끝난 상태입니다. 클라우드 세션에는 GitHub 계정이 연결되어 있지 않아 직접 푸시하지 못했습니다. 아래 둘 중 하나로 올리면 됩니다. 저장소는 비공개(private)로 먼저 만드는 것을 권합니다. 공개 여부는 수담님이 정합니다.

## 방법 A. GitHub CLI (gh)가 설치되어 있을 때
```powershell
cd "<이 폴더 경로>"
gh auth login
gh repo create Neosiki/creatorlink-site-collector --private --source . --push
```

## 방법 B. 웹에서 빈 저장소를 만든 뒤 푸시
1. https://github.com/new 에서 소유자 `Neosiki`, 이름 `creatorlink-site-collector`, 공개 범위 Private으로 만듭니다. README, .gitignore, 라이선스는 추가하지 않습니다(빈 저장소).
2. 이 폴더에서 실행합니다.
```powershell
git remote add origin https://github.com/Neosiki/creatorlink-site-collector.git
git branch -M main
git push -u origin main
```

## 압축본(zip)만 받은 경우
`.git` 폴더가 없으면 먼저 아래를 실행합니다.
```powershell
git init -b main
git add .
git commit -m "Initial commit: creatorlink-site-collector"
```
이후 방법 B의 2번부터 진행합니다.

## git bundle로 받은 경우
```powershell
git clone creatorlink-site-collector.bundle creatorlink-site-collector
cd creatorlink-site-collector
git remote set-url origin https://github.com/Neosiki/creatorlink-site-collector.git
git push -u origin main
```

## 확인 사항
- 라이선스 파일은 넣지 않았습니다. 공개하실 경우 종류를 정해 `LICENSE`를 추가하십시오.
- `history/`의 스크립트는 카페보리 수집 때 쓴 PC 버전 원본이며 소유자 id가 하드코딩되어 있습니다. 새 작업에는 `scripts/collect.py`를 쓰십시오.
- 수집된 이미지는 작가의 저작물이라 저장소에 넣지 않았습니다(`.gitignore`에 `output/` 포함).
