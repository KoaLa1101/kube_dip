from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, \
    QDialogButtonBox


class StatefulSetEditDialog(QDialog):
    def __init__(self, parent, current_image, current_replicas, current_limits, current_requests):
        super().__init__(parent)

        self.setWindowTitle("Edit StatefulSet")

        layout = QVBoxLayout(self)

        # Создание полей ввода для редактирования атрибутов StatefulSet
        self.image_edit = QLineEdit(current_image)
        self.replicas_spinbox = QSpinBox()
        self.replicas_spinbox.setRange(0, 1000)
        self.replicas_spinbox.setValue(current_replicas)
        self.limits_cpu_edit = QLineEdit(str(current_limits["cpu"])if current_limits else "")
        self.limits_memory_edit = QLineEdit(str(current_limits["memory"])if current_limits else "")
        self.requests_cpu_edit = QLineEdit(str(current_requests["cpu"])if current_requests else "")
        self.requests_memory_edit = QLineEdit(str(current_requests["memory"])if current_requests else "")

        # Функция для добавления метки и поля ввода на диалог
        def add_row(label_text, widget):
            row_layout = QHBoxLayout()
            row_layout.addWidget(QLabel(label_text))
            row_layout.addWidget(widget)
            layout.addLayout(row_layout)

        add_row("Image:", self.image_edit)
        add_row("Replicas:", self.replicas_spinbox)
        add_row("Limits CPU:", self.limits_cpu_edit)
        add_row("Limits Memory:", self.limits_memory_edit)
        add_row("Requests CPU:", self.requests_cpu_edit)
        add_row("Requests Memory:", self.requests_memory_edit)

        # Создание кнопок "OK" и "Cancel"
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_updated_values(self):
        # Возвращает обновленные значения из полей ввода
        return (
            self.image_edit.text(),
            self.replicas_spinbox.value(),
            {"cpu": self.limits_cpu_edit.text(), "memory": self.limits_memory_edit.text()},
            {"cpu": self.requests_cpu_edit.text(), "memory": self.requests_memory_edit.text()}
        )
