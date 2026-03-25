## 실행 방법

이 프로젝트는 `uv` 패키지 매니저를 기반으로 동작합니다. 프로젝트를 실행하려면 터미널에서 다음 명령어를 입력하세요:

```bash
uv run main.py
```

## 에디터 가상환경 버전 선택 (VS Code 기준)

에디터에서 코드를 작성할 때, `uv`가 관리하는 가상 환경을 사용하도록 설정해야 패키지 자동 완성 및 타입 힌트가 정상적으로 동작합니다.

1. **명령 팔레트 활성화**: `Ctrl + Shift + P` (Mac: `Cmd + Shift + P`)를 누릅니다.
2. **인터프리터 선택**: `Python: Select Interpreter`를 검색하여 클릭합니다.
3. **가상 환경 경로 지정**: 목록에서 현재 프로젝트 폴더 내 `.venv` 경로의 Python을 선택합니다.
   - 주로 `.\.venv\Scripts\python.exe` (Windows) 또는 `./.venv/bin/python` (Mac/Linux) 입니다.
   - 만약 목록에 보이지 않는다면, `Enter interpreter path...`를 클릭해 직접 `.venv` 내의 실행 파일 경로를 찾아 선택해 주세요.
