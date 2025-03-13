import pytesseract
import cv2
import numpy as np
from capture import capture_game_screen as capture_game_image

def extract_all_text(window_title):
    """
    선택된 창을 캡처한 후, 해당 이미지의 모든 텍스트를 추출합니다.
    이 경우, 위치 정보는 생략합니다.
    """
    img = capture_game_image(window_title)
    # 이미지가 None이거나 NumPy 배열이 아닌 경우 빈 문자열 반환
    if img is None or not isinstance(img, np.ndarray):
        return ""
    
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    except Exception as e:
        print("cv2.cvtColor 오류:", e)
        return ""
    
    text = pytesseract.image_to_string(gray, lang="jpn+eng")
    return text.strip()

if __name__ == "__main__":
    text = extract_all_text("Your Game Window Title")
    print("✅ 전체 OCR 결과:", text)


