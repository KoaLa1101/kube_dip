from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, \
    QDialogButtonBox


class HPAEditDialog(QDialog):
    def __init__(self, parent, current_min_replicas, current_max_replicas, current_cpu, current_memory):
        super().__init__(parent)

        self.setWindowTitle("Edit HPA")

        layout = QVBoxLayout(self)

        # Создание полей ввода для редактирования атрибутов HPA
        self.min_replicas_spinbox = QSpinBox()
        self.min_replicas_spinbox.setRange(0, 1000)
        self.min_replicas_spinbox.setValue(current_min_replicas)
        self.max_replicas_spinbox = QSpinBox()
        self.max_replicas_spinbox.setRange(0, 1000)
        self.max_replicas_spinbox.setValue(current_max_replicas)
        self.cpu_percent_spinbox = QDoubleSpinBox()
        self.cpu_percent_spinbox.setRange(0, 100)
        self.cpu_percent_spinbox.setValue(current_cpu)
        self.memory_percent_spinbox = QDoubleSpinBox()
        self.memory_percent_spinbox.setRange(0, 100)
        self.memory_percent_spinbox.setValue(current_memory)

        # Функция для добавления метки и поля ввода на диалог
        def add_row(label_text, widget):
            row_layout = QHBoxLayout()
            row_layout.addWidget(QLabel(label_text))
            row_layout.addWidget(widget)
            layout.addLayout(row_layout)

        add_row("Min Replicas:", self.min_replicas_spinbox)
        add_row("Max Replicas:", self.max_replicas_spinbox)
        add_row("CPU %:", self.cpu_percent_spinbox)
        add_row("Memory %:", self.memory_percent_spinbox)

        # Создание кнопок "OK" и "Cancel"
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_updated_values(self):
        # Возвращает обновленные значения из полей ввода
        return (
            self.min_replicas_spinbox.value(),
            self.max_replicas_spinbox.value(),
            self.cpu_percent_spinbox.value(),
            self.memory_percent_spinbox.value()
        )
