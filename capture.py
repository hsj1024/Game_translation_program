import pygetwindow as gw
import pyautogui
import cv2
import numpy as np
import pytesseract

# Tesseract 경로 설정 (Windows 사용자)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def get_game_window(selected_title):
    """선택한 제목을 포함하는 창 목록 중 첫 번째 창 반환"""
    windows = [win for win in gw.getWindowsWithTitle(selected_title)]
    if windows:
        return windows[0]
    return None

def capture_game_screen(window_title):
    """특정 창 제목을 가진 게임 창만 캡처하여 OCR 실행"""
    game_window = get_game_window(window_title)
    if game_window:
        x, y, w, h = game_window.left, game_window.top, game_window.width, game_window.height
        screenshot = pyautogui.screenshot(region=(x, y, w, h))
        img = np.array(screenshot)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray, lang="jpn+eng")
        return text.strip()
    return ""

def capture_game_image(window_title):
    """특정 창 제목을 가진 게임 창만 캡처하여 이미지(NumPy 배열) 반환"""
    game_window = get_game_window(window_title)
    if game_window:
        x, y, w, h = game_window.left, game_window.top, game_window.width, game_window.height
        screenshot = pyautogui.screenshot(region=(x, y, w, h))
        img = np.array(screenshot)
        return img
    return None



if __name__ == "__main__":
    # 테스트용: 원하는 게임 창 제목 입력
    text = capture_game_screen("Your Game Window Title")
    print("🎮 게임 화면 OCR 감지 결과:", text)
