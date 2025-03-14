# Game_translation_program

# 게임 실시간 번역 프로그램

이 프로젝트는 **Google Cloud Vision API**와 **Google Translate API**를 활용하여 게임 화면에서 텍스트를 추출하고 자동 번역하는 프로그램입니다. 사용자는 특정 게임 창을 선택하여 실시간으로 번역된 텍스트를 오버레이 창을 통해 확인할 수 있습니다.

## 🔹 주요 기능
- **OCR (광학 문자 인식)**: 게임 화면에서 텍스트를 감지하고 추출
- **자동 번역**: Google Translate API를 사용하여 영어에서 한국어로 번역
- **게임 창 캡처**: 사용자가 선택한 특정 창을 캡처하여 번역 수행
- **변경 감지 최적화**: 이전 화면과 비교하여 변동이 없으면 OCR 및 번역 생략
- **BERT 기반 유사 문장 필터링**: 중복 문장을 제거하여 번역 품질 향상
- **오버레이 UI**: 번역된 텍스트를 화면에 표시하며 이동 및 크기 조절 가능

## 📌 설치 및 실행 방법
### 1️⃣ 필수 패키지 설치
```bash
pip install opencv-python numpy pyautogui pygetwindow google-cloud-vision google-cloud-translate PyQt5 sentence-transformers
```

### 2️⃣ Google Cloud API 설정
1. [Google Cloud Console](https://console.cloud.google.com/)에서 **Vision API** 및 **Translate API** 활성화
2. 서비스 계정 키(JSON)를 다운로드 후, 환경 변수에 설정
   ```python
   os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "<YOUR_CREDENTIALS_FILE>.json"
   ```

### 3️⃣ 실행
```bash
python main.py
```

## 🖥️ 사용 방법
1. 프로그램 실행 후 번역할 게임 창을 선택
2. **'번역 시작'** 버튼을 눌러 실시간 번역 시작
3. 번역된 텍스트는 오버레이 창에 표시됨
4. **'번역 중지'** 버튼으로 번역 종료

## ⚠️ 주의 사항
- Google Cloud API 사용 시 **요금**이 발생할 수 있으므로 무료 할당량을 초과하지 않도록 주의하세요.
- 일부 게임에서는 캡처 기능이 제한될 수 있습니다.
- 번역 품질은 Google Translate API의 성능에 따라 달라질 수 있습니다.

## 📌 라이센스
이 프로젝트는 MIT 라이센스를 따릅니다.
