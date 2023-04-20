from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox


class AddNodeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Добавить новую ноду")

        layout = QVBoxLayout()

        self.ip_address_label = QLabel("IP-адрес:")
        self.ip_address_edit = QLineEdit()
        layout.addWidget(self.ip_address_label)
        layout.addWidget(self.ip_address_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_ip_address(self):
        return self.ip_address_edit.text()
