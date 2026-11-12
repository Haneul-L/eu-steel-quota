# EU Steel Quota Monitor (English)

EU steel safeguard quota dashboard for the Istanbul office, built on public EU TARIC data.

- Site: https://haneul-l.github.io/eu-steel-quota/
- Data: `data/latest.json`, refreshed by GitHub Actions every 2 hours, 06:00–18:00 Istanbul time, Monday–Friday
  (`.github/workflows/update-data.yml` → `scripts/fetch_taric.py`)
- Manual update: **Actions → Update TARIC data → Run workflow**

## 관리 메모 (한국어)

- 화면·쿼터 목록 수정: `eng/index.html` 또는 `eng/catalog.js` 수정 → `eng/Make_Shareable_File.bat` 실행
  (이 폴더의 `index.html`, `catalog.js`도 같이 갱신됨) → 이 폴더에서 아래 실행

```bash
git pull
```

```bash
git add . && git commit -m "update" && git push
```

- 2027년 규정이 바뀌면 `eng/catalog.js`의 Order 목록을 새 규정에 맞게 바꿔야 합니다.
- 자동 갱신 상태: 저장소 **Actions** 탭 (초록 체크 = 정상)
