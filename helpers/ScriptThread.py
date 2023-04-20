from PyQt6.QtCore import QThread
import subprocess


class ScriptThread(QThread):
    def __init__(self, command, parent=None):
        super().__init__(parent)
        self.command = command

    def run(self):
        try:
            process = subprocess.Popen(self.command, shell=True)
            process.communicate()
        except Exception as e:
            # Вывод всплывающего окна с сообщением об ошибке
            self.error_message = f"Ошибка: {str(e)}"
            self.finished.emit()
        else:
            self.error_message = None
            self.finished.emit()
