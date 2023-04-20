import os
import subprocess
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QWidget, QMessageBox


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Кластерное приложение")
        self.setGeometry(100, 100, 400, 200)

        # Создание темной темы
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        self.setPalette(palette)

        layout = QVBoxLayout()

        label = QLabel("Выберите операцию:")
        layout.addWidget(label)

        self.start_dip_btn = QPushButton("Сервис инициализации кластера", self)
        self.start_dip_btn.clicked.connect(self.start_dip)
        layout.addWidget(self.start_dip_btn)

        self.admin_btn = QPushButton("Администрирование кластера", self)
        self.admin_btn.clicked.connect(self.admin_cluster)
        layout.addWidget(self.admin_btn)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def start_dip(self):
        subprocess.Popen(["python", "start_dip.py"])

    def admin_cluster(self):
        if os.path.isfile("admin.conf"):
            QMessageBox.information(self, "Проверка файла конфигурации", "Файл 'admin.conf' найден. Запуск администрирования кластера.")
            subprocess.Popen(["python", "Gui.py"])
        else:
            QMessageBox.warning(self, "Проверка файла конфигурации", "Файл 'admin.conf' не найден. Пожалуйста, добавьте его в текущую директорию.")


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
