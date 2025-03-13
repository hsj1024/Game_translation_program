from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtCore import Qt
import sys

class OverlayText(QLabel):
    def __init__(self, text):
        super().__init__(None)
        self.setText(text)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 150); color: white; font-size: 20px; padding: 10px;")
        self.adjustSize()
        self.show()

def show_overlay(translated_text):
    app = QApplication([])
    overlay = OverlayText(translated_text)
    app.exec_()

if __name__ == "__main__":
    show_overlay("번역된 텍스트 예제")
