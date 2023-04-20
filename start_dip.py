import subprocess
import sys
import threading

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QSpinBox, \
    QComboBox, QFormLayout, QGridLayout, QMessageBox

from helpers.ScriptThread import ScriptThread


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Конфигуратор Kubernetes")
        self.init_ui()

    def init_ui(self):
        # Создание виджетов
        self.label_cp = QLabel("Количество control-plane адресов")
        self.spin_box_cp = QSpinBox()
        self.label_worker = QLabel("Количество worker адресов")
        self.spin_box_worker = QSpinBox()
        self.label_version = QLabel("Версия Kubernetes")
        self.combo_box_version = QComboBox()
        self.combo_box_version.addItem("1.25.1")
        self.combo_box_version.addItem("1.25.2")
        self.combo_box_version.addItem("1.25.3")
        self.combo_box_version.addItem("1.25.4")
        self.combo_box_version.addItem("1.26.1")
        self.label_vip = QLabel("Виртуальный IP-адрес")
        self.line_edit_vip = QLineEdit()
        self.label_os = QLabel("Операционная система")
        self.combo_box_os = QComboBox()
        self.combo_box_os.addItem("CentOS")
        self.combo_box_os.addItem("Debian")
        self.combo_box_os.addItem("Ubuntu")
        self.combo_box_os.addItem("AlmaLinux")
        self.button_confirm_count = QPushButton("Подтвердить количество")
        self.button_start = QPushButton("Начать установку пакетов")
        self.button_init = QPushButton("Инициализация кластера")

        # Определение макета
        form_layout = QFormLayout()
        form_layout.addRow(self.label_cp, self.spin_box_cp)
        form_layout.addRow(self.label_worker, self.spin_box_worker)

        grid_layout = QGridLayout()
        grid_layout.addWidget(self.label_version, 0, 0)
        grid_layout.addWidget(self.combo_box_version, 0, 1)
        grid_layout.addWidget(self.label_os, 1, 0)
        grid_layout.addWidget(self.combo_box_os, 1, 1)

        vbox_left = QVBoxLayout()
        vbox_left.addLayout(form_layout)

        vbox_right = QVBoxLayout()
        vbox_right.addWidget(self.label_vip)
        vbox_right.addWidget(self.line_edit_vip)
        vbox_right.addLayout(grid_layout)
        vbox_right.addWidget(self.button_confirm_count)
        vbox_right.addWidget(self.button_start)
        vbox_right.addWidget(self.button_init)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox_left)
        hbox.addLayout(vbox_right)

        self.setLayout(hbox)

        # Обработчики событий
        self.spin_box_cp.valueChanged.connect(self.show_confirm_button)
        self.spin_box_worker.valueChanged.connect(self.show_confirm_button)
        self.button_confirm_count.clicked.connect(self.add_fields)
        self.button_start.clicked.connect(self.start_script)
        self.button_init.clicked.connect(self.init_k8s)

        # Поля для control-plane и worker адресов
        self.cp_fields = []
        self.worker_fields = []

    def show_confirm_button(self):
        self.button_confirm_count.show()

    def add_fields(self):
        cp_count = self.spin_box_cp.value()
        worker_count = self.spin_box_worker.value()

        # Удаление лишних полей для control-plane адресов
        if len(self.cp_fields) > cp_count:
            for i in range(cp_count, len(self.cp_fields)):
                field = self.cp_fields.pop()
                field[0].deleteLater()
                field[1].deleteLater()

        # Удаление лишних полей для worker адресов
        if len(self.worker_fields) > worker_count:
            for i in range(worker_count, len(self.worker_fields)):
                field = self.worker_fields.pop()
                field[0].deleteLater()
                field[1].deleteLater()

        # Создание полей для control-plane адресов
        for i in range(len(self.cp_fields), cp_count):
            label = QLabel(f"Control-plane адрес {i + 1}")
            line_edit = QLineEdit()
            self.cp_fields.append((label, line_edit))

        # Создание полей для worker адресов
        for i in range(len(self.worker_fields), worker_count):
            label = QLabel(f"Worker адрес {i + 1}")
            line_edit = QLineEdit()
            self.worker_fields.append((label, line_edit))

        # Обновление макета
        layout_left = self.layout().itemAt(0).layout()
        form_layout = layout_left.itemAt(0).layout()
        for field in self.cp_fields:
            form_layout.addRow(field[0], field[1])
        for field in self.worker_fields:
            form_layout.addRow(field[0], field[1])
        self.button_confirm_count.hide()

    def start_script(self):
        # Получение введенных IP-адресов, операционной системы и версии Kubernetes
        cp_addresses = [field[1].text() for field in self.cp_fields]
        worker_addresses = [field[1].text() for field in self.worker_fields]
        if len(worker_addresses) < 1:
            worker_addresses.append('0.0.0.0')
        version = self.combo_box_version.currentText()
        os = self.combo_box_os.currentText()
        vip = self.line_edit_vip.text()

        # Вывод в консоль IP-адресов, операционной системы, версии Kubernetes и виртуальный айпи адрес
        print("Control-plane адреса:")
        for address in cp_addresses:
            print(address)
        print("Worker адреса:")
        for address in worker_addresses:
            print(address)
        print(f"Операционная система: {os}")
        print(f"Версия Kubernetes: {version}")
        print(f"Virtual Ip Address : {vip}")

        # Вывод всплывающего окна перед запуском скрипта
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Загрузка пакетов")
        msg_box.setText("Началась загрузка пакетов. Ожидайте сообщения о завершении")
        msg_box.exec()

        command = f"bash install_kubernetes.sh {','.join(cp_addresses)} {','.join(worker_addresses)} {version} '{os}' '{vip}'"
        self.script_thread = ScriptThread(command)
        self.script_thread.finished.connect(self.on_script_finished)
        self.script_thread.start()

    def init_k8s(self):

        cp_addresses = [field[1].text() for field in self.cp_fields]
        worker_addresses = [field[1].text() for field in self.worker_fields]
        if len(cp_addresses) < 1:
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Ошибка")
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setText("Нужен хотя бы 1 control_plane")
            msg_box.exec()
            return 1
        if len(worker_addresses) < 1:
            worker_addresses.append('0.0.0.0')
        vip = self.line_edit_vip.text()

        # Вывод всплывающего окна перед запуском скрипта
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Инициализация кластера")
        msg_box.setText("Началась инициализация кластера. Ожидайте сообщения о завершении")
        msg_box.exec()

        command = f"bash init_k8s_cluster.sh {','.join(cp_addresses)} {','.join(worker_addresses)} '{vip}'"
        self.script_thread = ScriptThread(command)
        self.script_thread.finished.connect(self.on_script_finished)
        self.script_thread.start()

    def on_script_finished(self):
        if self.script_thread.error_message is not None:
            error_box = QMessageBox()
            error_box.setWindowTitle("Ошибка")
            error_box.setText(self.script_thread.error_message)
            error_box.setIcon(QMessageBox.Icon.Critical)
            error_box.exec()
        else:
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Инициализация кластера")
            msg_box.setText("Инициализация завершена. admin.conf находится в директории этого проекта")
            msg_box.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Настройка темной темы
    app.setStyle("Fusion")
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(dark_palette)
    app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")

    window = MainWindow()
    window.setGeometry(500, 300, 800, 200)
    window.show()
    sys.exit(app.exec())
