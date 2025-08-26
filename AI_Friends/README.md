## AI Friends

따뜻한 공감과 실용적인 제안을 해주는 멀티모달(텍스트/음성/이미지) AI 친구 웹앱입니다. 일상 대화, 위로와 격려, 음식/취미/나들이 추천 등 실제 친구처럼 상호작용하는 경험을 목표로 합니다.

### 문제 의식과 동기 (직접 작성)
- 최근 기사에서 우리나라가 2003년 이후 20년 넘게 OECD 국가 자살률 1위라는 것을 봤습니다.
- 엄청나게 빠른 성장과 선진국이 된 이면에는 과도한 경쟁, 극심한 압박과 스트레스 등 정작 우리들의 마음 건강은 돌보지 못했다는 문제가 있습니다.
- 매년 우리나라 국민의 약 11,000명이 스스로 생을 마감한다고 합니다. 지난 2024년에는 통계상으로 약 36분마다 1명씩 자살했다고 합니다.
- 2025년 기준 우리나라 국민 1인당 자살 예방 사업 예산은 1,514원이며, 정부의 자살 예방 회의는 0회로 진행 중입니다. 이 밖에도 부정적인 관련 통계가 너무 많습니다.
- 자살 신고는 한 해 평균 10만 5천 건으로 하루 평균 287건, 약 5분 마다 신고가 접수되는 상황입니다.
- 자살 예방의 최전선에서 활동하는 자살 예방 센터는 부족한 예산과 인력으로, 서울시 자살 예방 인력 1명당 담당 인구가 3만명을 초과합니다. (287명이 932만명을 담당)
- 과도한 업무와 부족한 처우, 그리고 삼당사 분들 역시 사람이기 때문에 업무를 하면서 힘든 마음이 들 수도 있습니다.  

- 이 프로젝트는 이러한 사회적 현실 속에서, **누군가에게 작은 대화의 창구가 되어줄 수 있는 AI 친구**를 만들어보고자 시작되었습니다.  
- 비록 기술로 모든 문제를 해결할 수는 없지만, **혼자 있는 사람에게 가장 먼저 말을 걸어줄 수 있는 존재**가 될 수 있기를 바랍니다.

### 목적
- **공감과 위로**: 감정 이름붙이기 → 공감 → 확인 질문 → 부드러운 제안 → 선택지 제시의 흐름으로 대화합니다.
- **생활 밀착 추천**: 음식, 취미, 나들이 장소 등 상황 맞춤형 아이디어 제안.
- **멀티모달 상호작용**: 텍스트 대화, 음성 합성(TTS), 음성 입력(STT), 이미지와 함께 대화.

### 주요 기능
- **텍스트 채팅**: 공감형 시스템 프롬프트 기반의 대화. 추천 프롬프트(취미/나들이/음식/루틴) 버튼 제공.
- **음성 합성(TTS)**: 텍스트 → MP3 오디오 생성 및 재생.
- **음성 입력(STT)**: 마이크로 직접 녹음 → 서버 전송 → 텍스트 전사.
- **이미지 업로드**: 이미지를 업로드하고 함께 메시지 전송(시각 정보의 맥락 반영).
- **안전/톤 관리**: 기본적인 입력 정화와 공감형 말투, 민감 주제에 대한 가이드라인 반영.

### 사용된 기술 스택
- **Backend**: FastAPI, Starlette, Uvicorn, python-multipart, python-dotenv
- **LLM/Audio**: OpenAI Python SDK (Chat, TTS, STT)
- **Frontend**: HTML, Tailwind CSS(CDN), Vanilla JS, Jinja2 Templates

### 프로젝트 구조
```
AI_Friends/
├─ app.py                  # FastAPI 진입점 (라우트: /, /api/chat, /api/voice, /api/transcribe, /api/upload-image)
├─ requirements.txt        # Python 의존성
├─ templates/
│  └─ index.html           # 메인 UI 템플릿 (채팅/음성/이미지)
├─ static/
│  ├─ css/styles.css       # 커스텀 스타일
│  └─ js/app.js            # 프론트 인터랙션 로직
└─ agent/
   ├─ config.py            # 모델/보이스/환경설정 로딩
   ├─ openai_client.py     # Chat/TTS/STT 래퍼
   ├─ safety.py            # 공감형 시스템 프롬프트/간단한 정화
   └─ __init__.py
```

### 빠른 시작
1) 의존성 설치
```bash
pip install -r requirements.txt
```

2) 환경변수 설정 (권장: 프로젝트 루트 `.env` 파일)
```bash
# AI_Friends/.env
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
```

3) 개발 서버 실행
```bash
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

4) 접속
```
http://127.0.0.1:8000
```

### 실행 방법 (Windows PowerShell 예시)
```powershell
cd C:\Users\<USER>\Desktop\PythonWorkspace\AI_Friends
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
echo OPENAI_API_KEY=YOUR_OPENAI_API_KEY > .env
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

### API 엔드포인트 요약
- `POST /api/chat`
  - Form: `text`(str), `image_url`(str, optional)
  - Response: `{ reply: string }`

- `POST /api/voice`
  - Form: `text`(str)
  - Response: mp3 스트리밍(Audio/MPEG)

- `POST /api/transcribe`
  - Form: `file`(audio/webm 등)
  - Response: `{ text: string }`

- `POST /api/upload-image`
  - Form: `file`(image/*)
  - Response: `{ image_url: data_url }`

### 커스터마이즈 포인트
- `agent/config.py`
  - `chat_model`, `tts_model`, `tts_voice` 등 모델/보이스 설정
  - `max_history_messages` 등 대화 히스토리 제한값 (현재 기본 단문/단발 구조)

- `agent/safety.py`
  - 공감형 시스템 프롬프트/톤 수정
  - 입력 정화 로직 보강 가능

### 트러블슈팅
- "Could not import module 'app'": `AI_Friends` 디렉터리에서 실행했는지 확인하세요.
- 401/403/429 에러: `OPENAI_API_KEY` 유효성·쿼터·속도 제한 확인.
- 마이크 접근 불가: 브라우저 권한 허용 필요.
- 이미지가 반영되지 않음: 파일 업로드 성공 여부 및 `image_url` 전송 여부 확인.

### 주의사항
- 본 프로젝트는 데모/연구 목적 예제로 제공됩니다. 민감 주제 응대는 실제 서비스 수준의 안전 정책/감수 절차를 별도 설계하여 강화하세요.






