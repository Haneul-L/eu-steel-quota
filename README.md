# EU Steel Quota Monitor — 웹사이트 배포 안내 (Azure Static Web Apps)

이 `web` 폴더 전체가 웹사이트 하나입니다. 친구분 사이트와 같은 구조입니다.

```
web/
├─ src/                      ← 화면 (Azure가 그대로 웹에 올림)
│  ├─ index.html             ← eng/index.html + 카탈로그 + 마지막 스냅샷이 합쳐진 파일
│  └─ staticwebapp.config.json
└─ api/                      ← 서버 코드 (Azure Functions, Python)
   ├─ ping/                  ← /api/ping  : 현재 분기 확인
   ├─ live/                  ← /api/live  : TARIC 실시간 조회 (한 번에 최대 40건)
   └─ shared_code/taric.py   ← TARIC 조회·해석 (eng/server.py와 같은 로직, 10분 캐시)
```

비용: Static Web Apps **Free 요금제** (API 포함, 0원).

---

## 1. GitHub에 올리기 (최초 1회)

1. https://github.com 가입 → 오른쪽 위 **+ → New repository**
2. 이름 예: `eu-steel-quota` · **Public** 선택 · README 추가 체크하지 않음 → **Create repository**
3. 만든 저장소 주소(예: `https://github.com/계정/eu-steel-quota.git`)를 Claude에게 알려주면 올려드립니다.
   직접 올릴 때는 이 `web` 폴더에서:

```bash
git init -b main
```

```bash
git add . && git commit -m "EU steel quota monitor"
```

```bash
git remote add origin https://github.com/계정/eu-steel-quota.git
```

```bash
git push -u origin main
```

   (처음 push할 때 GitHub 로그인 창이 뜹니다.)

## 2. Azure에 사이트 만들기 (최초 1회)

1. https://portal.azure.com 가입·로그인 (무료 계정, 카드 본인확인이 있을 수 있음)
2. 위 검색창에 **Static Web Apps** → **만들기(Create)**
3. 입력값

| 항목 | 값 |
|---|---|
| 구독 | 본인 구독 |
| 리소스 그룹 | 새로 만들기 → `eu-quota` |
| 이름 | `eu-steel-quota` |
| 요금제 유형 | **Free** |
| 배포 원본 | **GitHub** → 로그인 → 조직/리포지토리 `eu-steel-quota` / 분기 `main` |
| 빌드 사전 설정 | **Custom** |
| 앱 위치 | `/src` |
| API 위치 | `api` |
| 출력 위치 | (비워둠) |

4. **검토 + 만들기 → 만들기**
5. Azure가 GitHub 저장소에 배포 설정 파일(`.github/workflows/...`)을 자동으로 추가하고 3~5분 뒤 배포가 끝납니다.
6. 리소스 **개요** 화면의 **URL**(예: `https://xxxx-xxxx.azurestaticapps.net`)이 직원들에게 보낼 주소입니다.

## 3. 이후 관리

- **데이터**: 할 일 없음. 직원이 페이지를 열면 그 화면의 Order를 TARIC에서 바로 조회합니다.
  같은 Order는 10분 동안 다시 조회하지 않아 TARIC 트래픽이 적습니다.
- **화면이나 쿼터 목록 수정** (예: 2027년 규정 변경):
  1. `eng/index.html` 또는 `eng/catalog.js` 수정
  2. `eng/Make_Shareable_File.bat` 실행 → `web/src/index.html`도 같이 새로 만들어짐
  3. `web` 폴더에서 `git add . && git commit -m "update" && git push` → 몇 분 뒤 사이트 자동 반영
- 배포 상태는 GitHub 저장소의 **Actions** 탭에서 확인할 수 있습니다.
