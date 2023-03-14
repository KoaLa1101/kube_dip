import subprocess
import sys
import threading

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QSpinBox, \
    QComboBox, QFormLayout, QGridLayout, QMessageBox, QProgressBar


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
        self.label_os = QLabel("Операционная система")
        self.combo_box_os = QComboBox()
        self.combo_box_os.addItem("CentOS")
        self.combo_box_os.addItem("Debian")
        self.combo_box_os.addItem("Ubuntu")
        self.button_confirm_count = QPushButton("Подтвердить количество")
        self.button_start = QPushButton("Начать")

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
        vbox_right.addLayout(grid_layout)
        vbox_right.addWidget(self.button_confirm_count)
        vbox_right.addWidget(self.button_start)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox_left)
        hbox.addLayout(vbox_right)

        self.setLayout(hbox)

        # Обработчики событий
        self.spin_box_cp.valueChanged.connect(self.show_confirm_button)
        self.spin_box_worker.valueChanged.connect(self.show_confirm_button)
        self.button_confirm_count.clicked.connect(self.add_fields)
        self.button_start.clicked.connect(self.start_script)

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
            label = QLabel(f"Control-plane адрес {i+1}")
            line_edit = QLineEdit()
            self.cp_fields.append((label, line_edit))

        # Создание полей для worker адресов
        for i in range(len(self.worker_fields), worker_count):
            label = QLabel(f"Worker адрес {i+1}")
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
        version = self.combo_box_version.currentText()
        os = self.combo_box_os.currentText()

        # Вывод в консоль IP-адресов, операционной системы и версии Kubernetes
        print("Control-plane адреса:")
        for address in cp_addresses:
            print(address)
        print("Worker адреса:")
        for address in worker_addresses:
            print(address)
        print(f"Операционная система: {os}")
        print(f"Версия Kubernetes: {version}")

        # Вывод всплывающего окна перед запуском скрипта
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Загрузка пакетов")
        msg_box.setText("Началась загрузка пакетов. Ожидайте сообщения о завершении")
        msg_box.exec_()

        # Запуск скрипта установки пакетов в отдельном потоке
        def run_script():
            command = f"bash install_kubernetes.sh {','.join(cp_addresses)} {','.join(worker_addresses)} {version} '{os}'"
            subprocess.run(command, shell=True)

            # Вывод всплывающего окна после завершения работы скрипта
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Установка завершена")
            msg_box.setText("Пакеты установлены")
            msg_box.exec_()

        thread = threading.Thread(target=run_script)
        thread.start()
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
