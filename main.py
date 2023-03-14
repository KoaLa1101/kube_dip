import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QPlainTextEdit, QLabel, QLineEdit, QComboBox, QMenu, QAction
import kubernetes.client as k8s_client
from kubernetes.config import kube_config

kube_config.load_kube_config(config_file='admin.conf')
api_instance = k8s_client.CoreV1Api()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kubernetes Cluster GUI")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # кнопка для вывода списка подов
        self.list_pods_btn = QPushButton("List pods")
        self.list_pods_btn.clicked.connect(self.list_pods)
        layout.addWidget(self.list_pods_btn)

        # поле для вывода результатов
        self.results_text = QPlainTextEdit()
        layout.addWidget(self.results_text)

        # метка и поле для ввода имени пода
        self.pod_name_label = QLabel("Pod name:")
        self.pod_name_field = QLineEdit()
        layout.addWidget(self.pod_name_label)
        layout.addWidget(self.pod_name_field)

        # метка и поле для ввода namespace
        self.namespace_label = QLabel("Namespace:")
        self.namespace_field = QLineEdit()
        layout.addWidget(self.namespace_label)
        layout.addWidget(self.namespace_field)

        # кнопка для выполнения действия с подом
        self.pod_action_btn = QPushButton("Perform action")
        self.pod_action_btn.clicked.connect(self.show_actions_menu)
        layout.addWidget(self.pod_action_btn)

    def list_pods(self):
        pods = api_instance.list_pod_for_all_namespaces().items
        pod_names = [pod.metadata.name for pod in pods]
        self.results_text.setPlainText("\n".join(pod_names))

    def show_actions_menu(self):
        pod_name = self.pod_name_field.text()
        namespace = self.namespace_field.text()
        menu = QMenu(self.pod_action_btn)
        delete_action = QAction("Delete", menu)
        scale_up_action = QAction("Scale Up", menu)
        scale_down_action = QAction("Scale Down", menu)
        menu.addAction(delete_action)
        menu.addAction(scale_up_action)
        menu.addAction(scale_down_action)
        action = menu.exec_(self.pod_action_btn.mapToGlobal(self.pod_action_btn.rect().bottomLeft()))
        if action == delete_action:
            api_instance.delete_namespaced_pod(name=pod_name, namespace=namespace, body=k8s_client.V1DeleteOptions())
            self.results_text.setPlainText(f"Pod {pod_name} deleted.")
        elif action == scale_up_action:
            api_instance.patch_namespaced_replication_controller_scale(name=pod_name, namespace=namespace, body={"spec": {"replicas": 2}})
            self.results_text.setPlainText(f"Pod {pod_name} scaled up.")
        elif action == scale_down_action:
            api_instance.patch_namespaced_replication_controller_scale(name=pod_name, namespace=namespace, body={"spec": {"replicas": 1}})
            self.results_text.setPlainText(f"Pod {pod_name} scaled down.")

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()
