import sys
import difflib
import threading
import time
import io
import os
import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
from google.cloud import vision, translate_v2 as translate
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QComboBox, QSizeGrip
from PyQt5.QtCore import Qt, QPoint, QMetaObject, Q_ARG, QTimer
import html
import re
from sentence_transformers import SentenceTransformer, util

# 🔹 Google API 인증 정보 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\Users\\SeoJeong\\Downloads\\gametranskey1.json"

# 🔹 Google Cloud Vision API & Translate API 클라이언트
vision_client = vision.ImageAnnotatorClient()
translate_client = translate.Client()

previous_ocr_text = ""  # OCR 결과 저장 (영어)
previous_translation = ""  # 번역 결과 저장
previous_screenshot = None  # 이전 캡처된 이미지 저장
selected_window_title = None  # 사용자가 선택한 창
running = False  # 번역 실행 여부

# 🔹 현재 실행 중인 창 목록 가져오기
def get_window_titles():
    return [win.title for win in gw.getWindowsWithTitle("") if win.title.strip()]

# 🔹 선택한 게임 창 찾기
def get_game_window():
    global selected_window_title
    if not selected_window_title:
        return None
    windows = [win for win in gw.getWindowsWithTitle(selected_window_title)]
    return windows[0] if windows else None

# 🔹 게임 창 활성화 함수
def activate_game_window():
    game_window = get_game_window()
    if game_window:
        try:
            if not game_window.isActive:
                game_window.activate()
                print(f"🎮 게임 창 활성화됨: {game_window.title}")
        except Exception as e:
            print(f"⚠️ 창 활성화 오류: {e}")

# 🔹 게임 창 또는 풀스크린 캡처 함수
# 🔹 전체 화면에서 OCR 영역 최적화
def capture_game_image():
    global previous_screenshot

    game_window = get_game_window()
    
    if game_window:
        # 🔹 선택한 창이 있을 경우, 해당 창을 캡처
        activate_game_window()
        x, y, w, h = game_window.left, game_window.top, game_window.width, game_window.height

        # 🛠 대화창 부분만 OCR하도록 조정
        titlebar_height = int(h * 0.75)  # 🔹 화면 하단 25% 부분을 OCR 수행
        bottom_ui_height = int(h * 0.05) # 🔹 UI 버튼 제외 (5%)
        margin = int(w * 0.02)           # 🔹 좌우 여백 설정 (2%)

        try:
            screenshot = pyautogui.screenshot(region=(
                x + margin, y + titlebar_height, w - margin * 2, h - titlebar_height - bottom_ui_height
            ))
        except Exception as e:
            print(f"⚠️ 창 캡처 오류: {e}")
            return None
    else:
        # 🔹 선택한 창이 없으면 전체 화면을 캡처 (풀스크린 지원)
        print("🖥️ 창이 선택되지 않음, 전체 화면 캡처 진행")
        screenshot = pyautogui.screenshot()

    screenshot_np = np.array(screenshot.convert("L"))  # 🔹 흑백 변환

    # 🔹 이전 스크린샷과 비교하여 변화가 없으면 OCR 건너뜀
    if previous_screenshot is not None:
        diff = cv2.absdiff(previous_screenshot, screenshot_np)
        if np.sum(diff) < 5000:
            print("📸 화면 변화 없음, OCR 생략")
            return None

    previous_screenshot = screenshot_np  # 🔹 새로운 스크린샷 저장

    image_path = "game_screenshot.png"
    screenshot.save(image_path)
    print(f"📸 화면 캡처 완료: {image_path}")
    return image_path


# 🔹 OCR에서 UI 요소 및 게임 제목 제거 & 줄바꿈 처리
def preprocess_text(text):
    unwanted_words = ["Doki Doki Literature Club!", "게임 번역 프로그램", "번역 준비 중", "번역 시작", "번역 중지", "☐", "□", "x"]
    lines = text.split("\n")
    cleaned_lines = [line.strip() for line in lines if not any(word in line for word in unwanted_words)]

    # 🔹 따옴표 안의 텍스트만 추출
    merged_text = ""
    inside_quotes = False

    for line in cleaned_lines:
        if '"' in line:
            # 🔹 따옴표가 처음 등장하면 시작
            if not inside_quotes:
                merged_text += line.split('"', 1)[1] + " "
                inside_quotes = True
            else:
                merged_text += line.rsplit('"', 1)[0]  # 🔹 마지막 따옴표 이전까지 추가
                inside_quotes = False
        elif inside_quotes:
            merged_text += line + " "  # 🔹 따옴표 안에 있으면 문장 이어 붙이기

    # 🔹 문장 끝이 온점(.)이 아니라면 한 문장으로 붙이기
    merged_text = merged_text.strip()
    if merged_text and not merged_text.endswith("."):
        merged_text += "."

    return html.unescape(merged_text)


# 🔹 BERT 기반 문장 임베딩 모델 로드
model = SentenceTransformer('all-MiniLM-L6-v2')

previous_ocr_text = ""  # 이전 OCR 결과 저장

def is_similar(text1, text2, threshold=0.9):
    """
    두 개의 텍스트가 유사한지 판단하는 함수 (BERT 기반 코사인 유사도 계산)
    """
    embeddings = model.encode([text1, text2], convert_to_tensor=True)
    similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
    return similarity >= threshold

def normalize_text(text):
    """
    OCR 결과를 정규화하여 불필요한 공백, 특수문자를 제거하고 비교가 쉽도록 변환하는 함수.
    """
    text = text.lower().strip()  # 소문자로 변환
    text = re.sub(r'[^a-z0-9.,!?\'"()\s]', '', text)  # 불필요한 특수문자 제거
    text = re.sub(r'\s+', ' ', text)  # 다중 공백 제거
    return text

def remove_duplicate_sentences(text):
    """
    문장 단위로 중복 제거 (BERT를 이용하여 의미적으로 중복된 문장 제거)
    """
    sentences = text.split(".")  # 문장 단위로 분할
    unique_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence and not any(is_similar(sentence, s, 0.9) for s in unique_sentences):
            unique_sentences.append(sentence)
    
    return ". ".join(unique_sentences) + "." if unique_sentences else ""

def extract_english_text(text):
    """
    OCR 결과에서 영어 문장만 추출하고 중복을 제거하는 함수.
    따옴표 안의 문장을 올바르게 인식하고 한 문장으로 정리.
    """
    # 🔹 따옴표 안의 문장만 추출
    quoted_texts = re.findall(r'"(.*?)"', text)
    
    # 🔹 OCR 결과에서 영어 문장 추출 (특수문자 포함)
    english_sentences = re.findall(r'[A-Za-z0-9.,!?\'"()\s]+', text)
    
    # 🔹 모든 문장을 소문자로 변환 후 strip()하여 중복 제거
    cleaned_sentences = list(dict.fromkeys([s.strip().lower().replace("  ", " ") for s in quoted_texts + english_sentences]))
    
    # 🔹 불필요한 공백 및 반복 제거
    final_text = " ".join(cleaned_sentences).strip()
    final_text = re.sub(r'\s+', ' ', final_text)  # 여러 개의 공백을 하나로
    final_text = remove_duplicate_sentences(final_text)  # 문장 단위 중복 제거 (BERT 활용)
    
    return final_text

def extract_text_from_image(image_path):
    global previous_ocr_text

    if not image_path:
        return ""

    print("📸 OCR 시작...")

    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = vision_client.text_detection(image=image)
    texts = response.text_annotations

    if texts:
        # 🔹 OCR 결과에서 영어 문장만 추출 (중복 제거 및 줄바꿈 처리)
        extracted_text = extract_english_text(" ".join([text.description for text in texts]))

        # 🔹 OCR 결과가 이전과 유사하면 OCR 건너뛰기
        if is_similar(extracted_text, previous_ocr_text):
            print("🔁 OCR 결과가 유사하여 생략")
            return ""

        print(f"📸 OCR 결과 (중복 제거 후): {extracted_text}")
        previous_ocr_text = extracted_text  # 🔹 OCR 결과 업데이트
        return extracted_text

    print("📸 OCR 결과 없음")
    return ""

# 🔹 번역 수행 (특수문자는 유지하고 영어만 번역)
def translate_text(text):
    global previous_translation

    if not text.strip():
        return ""

    print("🌍 번역 시작...")

    try:
        # 🔹 OCR에서 추출된 영어 문장만 번역
        result = translate_client.translate(text, source_language="en", target_language="ko")
        translated_text = html.unescape(result["translatedText"])  # 🔹 HTML 엔티티 변환 (&quot; → ")

        print(f"🌍 번역 결과 (HTML 엔티티 변환 완료): {translated_text}")
        previous_translation = translated_text
        return translated_text
    except Exception as e:
        print(f"⚠️ 번역 오류: {e}")
        return ""


# 🔹 번역 실행 루프
def translation_loop(overlay):
    global running

    while running:
        image_path = capture_game_image()
        if not image_path:
            continue

        ocr_text = extract_text_from_image(image_path)
        if not ocr_text:
            continue

        translated_text = translate_text(ocr_text)
        if translated_text:
            overlay.update_text(translated_text)

        time.sleep(1)

# 🔹 번역 오버레이 창 (크기 조절 및 이동 가능)
class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.dragging = False
        self.offset = QPoint()

    def initUI(self):
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 600, 300)

        layout = QVBoxLayout()
        self.label = QLabel("🔄 번역 준비 중...", self)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: white; font-size: 24px; background-color: rgba(0, 0, 0, 180); padding: 10px; border-radius: 10px; text-align: center;")
        layout.addWidget(self.label)

        size_grip = QSizeGrip(self)
        layout.addWidget(size_grip, alignment=Qt.AlignBottom | Qt.AlignRight)

        self.setLayout(layout)
        self.show()

    def update_text(self, text):
        QMetaObject.invokeMethod(self.label, "setText", Qt.QueuedConnection, Q_ARG(str, text))
        QTimer.singleShot(0, self.label.adjustSize)
        
# 🔹 번역 UI (창 선택 추가)
class TranslatorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.overlay = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("게임 번역 프로그램")
        self.setGeometry(100, 100, 400, 200)
        layout = QVBoxLayout()

        self.window_combo = QComboBox()
        self.populate_window_combo()
        layout.addWidget(self.window_combo)

        self.start_button = QPushButton("번역 시작")
        self.start_button.clicked.connect(self.start_translation)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("번역 중지")
        self.stop_button.clicked.connect(self.stop_translation)
        layout.addWidget(self.stop_button)

        self.setLayout(layout)

    def populate_window_combo(self):
        self.window_combo.clear()
        self.window_combo.addItems(get_window_titles())

    def start_translation(self):
        global selected_window_title, running
        selected_window_title = self.window_combo.currentText()
        running = True
        self.overlay = OverlayWindow()
        threading.Thread(target=translation_loop, args=(self.overlay,), daemon=True).start()

    def stop_translation(self):
        global running
        running = False
        print("🛑 번역 중지됨")
        
# 🔹 프로그램 실행
if __name__ == "__main__":
    app = QApplication(sys.argv)
    translator_ui = TranslatorApp()
    translator_ui.show()
    sys.exit(app.exec_())
