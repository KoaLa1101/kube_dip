import sys
import os
import subprocess
from kubernetes import client, config
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QComboBox, QPushButton, \
    QListWidget, QPlainTextEdit, QLabel, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QStyleFactory
from PyQt5.QtGui import QPalette, QColor


class KubernetesAdminGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        # Установка темной темы для приложения
        self.set_dark_theme()

        # Создаем основной лэйаут
        main_layout = QHBoxLayout()

        # Создаем виджеты для левой, центральной и правой частей
        left_widget = QWidget()
        center_widget = QWidget()
        right_widget = QWidget()

        # Создаем лэйауты для левой и правой частей
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Верхняя левая часть: выпадающий список namespace и кнопка добавления ноды
        top_left_widget = QWidget()
        top_left_layout = QHBoxLayout()

        self.namespace_combo = QComboBox()
        self.add_node_button = QPushButton("Добавить новую ноду")

        top_left_layout.addWidget(self.namespace_combo)
        top_left_layout.addWidget(self.add_node_button)
        top_left_widget.setLayout(top_left_layout)

        # Нижняя левая часть: список типов ресурсов
        self.resource_list = QListWidget()

        # Установка лэйаута для левой части
        left_layout.addWidget(top_left_widget, 1)
        left_layout.addWidget(self.resource_list, 9)
        left_widget.setLayout(left_layout)

        # Центральная часть: список ресурсов
        center_layout = QVBoxLayout()
        self.resource_items_list = QListWidget()
        center_layout.addWidget(self.resource_items_list)
        center_widget.setLayout(center_layout)

        # Верхняя правая часть: кнопки действий
        top_right_widget = QWidget()
        top_right_layout = QHBoxLayout()
        self.edit_button = QPushButton("Изменить")
        self.delete_button = QPushButton("Удалить")
        top_right_layout.addWidget(self.edit_button)
        top_right_layout.addWidget(self.delete_button)
        top_right_widget.setLayout(top_right_layout)

        # Нижняя правая часть: информация о выбранном объекте
        self.info_text = QPlainTextEdit()
        self.info_text.setReadOnly(True)

        # Установка лэйаута для правой части
        right_layout.addWidget(top_right_widget, 1)
        right_layout.addWidget(self.info_text, 9)
        right_widget.setLayout(right_layout)

        # Разделение окна на три части с использованием QSplitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(center_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([self.width() // 5, 2 * self.width() // 5, 2 * self.width() // 5])

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

        # Настраиваем сигналы и слоты
        self.setup_connections()

    def setup_connections(self):
        # Загрузка списка namespace и ресурсов при запуске приложения
        self.namespace_combo.currentIndexChanged.connect(self.load_resource_types)
        self.namespace_combo.currentIndexChanged.connect(self.load_resource_items_for_current_resource_type)
        self.add_node_button.clicked.connect(self.add_node)

        # Выбор ресурса в левой части
        self.resource_list.itemClicked.connect(self.load_resource_items_for_current_resource_type)

        # Выбор объекта ресурса в центральной части
        self.resource_items_list.itemClicked.connect(self.display_resource_info)

        # Действия над выбранным объектом
        self.edit_button.clicked.connect(self.edit_resource)
        self.delete_button.clicked.connect(self.delete_resource)

        # Загрузка конфигурации Kubernetes
        config.load_kube_config('admin.conf')

        # Загрузка namespace и ресурсов при запуске приложения
        self.load_namespaces()
        self.load_resource_types()

    def load_namespaces(self):
        api = client.CoreV1Api()
        namespaces = api.list_namespace()
        for namespace in namespaces.items:
            self.namespace_combo.addItem(namespace.metadata.name)

    def load_resource_types(self):
        self.resource_list.clear()
        resource_types = [
            "Pods",
            "Deployments",
            "StatefulSets",
            "DaemonSets",
            "CronJobs",
            "Jobs",
            "PersistentVolumes",
            "PersistentVolumeClaims",
            "StorageClasses",
            "ConfigMaps",
            "Secrets",
            "ReplicaSets",
            "HorizontalPodAutoscalers",
            "Services",
            "Ingresses",
        ]
        for resource_type in resource_types:
            self.resource_list.addItem(resource_type)

    def load_resource_items_for_current_resource_type(self):
        if self.resource_list.currentItem():
            self.load_resource_items(self.resource_list.currentItem())

    def set_dark_theme(self):
        dark_palette = QPalette()

        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)

        QApplication.setStyle(QStyleFactory.create("Fusion"))
        QApplication.setPalette(dark_palette)

    def add_node(self):
        # Замените "your_script.sh" на путь к вашему bash скрипту для добавления ноды
        bash_script_path = "your_script.sh"
        subprocess.run(["bash", bash_script_path])

    def load_resource_items(self, item):
        resource_type = item.text()
        api = client.CoreV1Api()

        self.resource_items_list.clear()
        if resource_type == "Pods":
            resources = api.list_namespaced_pod(namespace=self.namespace_combo.currentText())
        elif resource_type == "Deployments":
            api = client.AppsV1Api()
            resources = api.list_namespaced_deployment(namespace=self.namespace_combo.currentText())
        elif resource_type == "PersistentVolumes":
            resources = api.list_persistent_volume()

        for resource in resources.items:
            self.resource_items_list.addItem(resource.metadata.name)

    def display_resource_info(self, item):
        resource_name = item.text()
        resource_type = self.resource_list.currentItem().text()
        namespace = self.namespace_combo.currentText()

        if resource_type == "Pods":
            resource_info = self.get_pod_info(namespace, resource_name)
        elif resource_type == "Deployments":
            resource_info = self.get_deployment_info(namespace, resource_name)
        elif resource_type == "StatefulSets":
            resource_info = self.get_stateful_set_info(namespace, resource_name)
        elif resource_type == "DaemonSets":
            resource_info = self.get_daemon_set_info(namespace, resource_name)
        elif resource_type == "PersistentVolumes":
            resource_info = self.get_pv_info(resource_name)
        elif resource_type == "PersistentVolumeClaims":
            resource_info = self.get_pvc_info(namespace, resource_name)
        elif resource_type == "ConfigMaps":
            resource_info = self.get_config_map_info(namespace, resource_name)
        elif resource_type == "Secrets":
            resource_info = self.get_secret_info(namespace, resource_name)
        elif resource_type == "CronJobs":
            resource_info = self.get_cron_job_info(namespace, resource_name)
        elif resource_type == "Jobs":
            resource_info = self.get_job_info(namespace, resource_name)
        elif resource_type == "ReplicaSets":
            resource_info = self.get_replica_set_info(namespace, resource_name)
        elif resource_type == "HorizontalPodAutoscalers":
            resource_info = self.get_hpa_info(namespace, resource_name)
        elif resource_type == "Services":
            resource_info = self.get_service_info(namespace, resource_name)
        elif resource_type == "Ingresses":
            resource_info = self.get_ingress_info(namespace, resource_name)
        elif resource_type == "StorageClasses":
            resource_info = self.get_sc_info(namespace, resource_name)
        else:
            resource_info = "Неизвестный тип ресурса"

        self.info_text.setPlainText(resource_info)

    def get_pod_info(self, namespace, pod_name):
        api = client.CoreV1Api()
        pod = api.read_namespaced_pod(namespace=namespace, name=pod_name)
        return f"Pod info:\n\nName: {pod.metadata.name}\nNamespace: {pod.metadata.namespace}\n\n{pod}"

    def get_deployment_info(self, namespace, deployment_name):
        api = client.AppsV1Api()
        deployment = api.read_namespaced_deployment(namespace=namespace, name=deployment_name)
        return f"Deployment info:\n\nName: {deployment.metadata.name}\nNamespace: {deployment.metadata.namespace}\n\n{deployment}"

    def get_pv_info(self, pv_name):
        api = client.CoreV1Api()
        pv = api.read_persistent_volume(name=pv_name)
        return f"PersistentVolume info:\n\nName: {pv.metadata.name}\n\n{pv}"

    def get_stateful_set_info(self, namespace, stateful_set_name):
        api = client.AppsV1Api()
        stateful_set = api.read_namespaced_stateful_set(namespace=namespace, name=stateful_set_name)
        return f"StatefulSet info:\n\nName: {stateful_set.metadata.name}\nNamespace: {stateful_set.metadata.namespace}\n\n{stateful_set}"

    def get_daemon_set_info(self, namespace, daemon_set_name):
        api = client.AppsV1Api()
        daemon_set = api.read_namespaced_daemon_set(namespace=namespace, name=daemon_set_name)
        return f"DaemonSet info:\n\nName: {daemon_set.metadata.name}\nNamespace: {daemon_set.metadata.namespace}\n\n{daemon_set}"

    def get_replica_set_info(self, namespace, replica_set_name):
        api = client.AppsV1Api()
        replica_set = api.read_namespaced_replica_set(namespace=namespace, name=replica_set_name)
        return f"ReplicaSet info:\n\nName: {replica_set.metadata.name}\nNamespace: {replica_set.metadata.namespace}\n\n{replica_set}"

    def get_pvc_info(self, namespace, pvc_name):
        api = client.CoreV1Api()
        pvc = api.read_namespaced_persistent_volume_claim(namespace=namespace, name=pvc_name)
        return f"PersistentVolumeClaims info:\n\nName: {pvc.metadata.name}\nNamespace: {pvc.metadata.namespace}\n\n{pvc}"

    def get_config_map_info(self, namespace, config_map_name):
        api = client.CoreV1Api()
        config_map = api.read_namespaced_config_map(namespace=namespace, name=config_map_name)
        return f"ConfigMaps info:\n\nName: {config_map.metadata.name}\nNamespace: {config_map.metadata.namespace}\n\n{config_map}"

    def get_secret_info(self, namespace, secret_name):
        api = client.CoreV1Api()
        secret = api.read_namespaced_secret(namespace=namespace, name=secret_name)
        return f"Secrets info:\n\nName: {secret.metadata.name}\nNamespace: {secret.metadata.namespace}\n\n{secret}"

    def get_cron_job_info(self, namespace, cron_job_name):
        api = client.BatchV1Api()
        cron_job = api.read_namespaced_cron_job(namespace=namespace, name=cron_job_name)
        return f"CronJobs info:\n\nName: {cron_job.metadata.name}\nNamespace: {cron_job.metadata.namespace}\n\n{cron_job}"


    def get_job_info(self, namespace, job_name):
        api = client.BatchV1Api()
        job = api.read_namespaced_job(namespace=namespace, name=job_name)
        return f"Jobs info:\n\nName: {job.metadata.name}\nNamespace: {job.metadata.namespace}\n\n{job}"

    def get_hpa_info(self, namespace, hpa_name):
        api = client.AutoscalingV2Api
        hpa = api.read_namespaced_horizontal_pod_autoscaler(namespace=namespace, name=hpa_name)
        return f"HPA info:\n\nName: {hpa.metadata.name}\nNamespace: {hpa.metadata.namespace}\n\n{hpa}"

    def get_service_info(self, namespace, service_name):
        api = client.CoreV1Api
        service = api.read_namespaced_service(namespace=namespace, name=service_name)
        return f"Service info:\n\nName: {service.metadata.name}\nNamespace: {service.metadata.namespace}\n\n{service}"

    def get_sc_info(self, namespace, sc_name):
        api = client.StorageV1Api
        sc = api.read_namespaced_csi_storage_capacity(namespace=namespace, name=sc_name)
        return f"StorageClasses info:\n\nName: {sc.metadata.name}\nNamespace: {sc.metadata.namespace}\n\n{sc}"


    def edit_resource(self):
        resource_name = self.resource_items_list.currentItem().text()
        resource_type = self.resource_list.currentItem().text()
        namespace = self.namespace_combo.currentText()

        # TODO: Замените на свою логику изменения объектов ресурса
        print(f"Edit resource {resource_type}: {resource_name} in namespace {namespace}")

    def delete_resource(self):
        resource_name = self.resource_items_list.currentItem().text()
        resource_type = self.resource_list.currentItem().text()
        namespace = self.namespace_combo.currentText()

        if resource_type == "Pods":
            self.delete_pod(namespace, resource_name)
        elif resource_type == "Deployments":
            self.delete_deployment(namespace, resource_name)
        elif resource_type == "PersistentVolumes":
            self.delete_pv(resource_name)
        else:
            print("Неизвестный тип ресурса")

        self.load_resource_items(self.resource_list.currentItem())

    def delete_pod(self, namespace, pod_name):
        api = client.CoreV1Api()
        api.delete_namespaced_pod(namespace=namespace, name=pod_name)

    def delete_deployment(self, namespace, deployment_name):
        api = client.AppsV1Api()
        api.delete_namespaced_deployment(namespace=namespace, name=deployment_name)

    def delete_pv(self, pv_name):
        api = client.CoreV1Api()
        api.delete_persistent_volume(name=pv_name)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = KubernetesAdminGUI()
    gui.show()
    sys.exit(app.exec_())
