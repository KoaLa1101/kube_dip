import subprocess
import sys

import paramiko
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor, QAction, QGuiApplication
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, \
    QListWidget, QPlainTextEdit, QSplitter, QStyleFactory, QDialog, QMenu
from PyQt6.QtWidgets import QMessageBox
from kubernetes import client, config

from helpers.AddNodeDialog import AddNodeDialog
from helpers.DeploymentEditDialog import DeploymentEditDialog
from helpers.HPAEditDialog import HPAEditDialog
from helpers.ReplicaSetEditDialog import ReplicaSetEditDialog
from helpers.ScriptThread import ScriptThread
from helpers.StatefulSetEditDialog import StatefulSetEditDialog


def get_master_ip():
    api = client.CoreV1Api()
    nodes = api.list_node()
    control_plane_ips = []

    for node in nodes.items:
        if "node-role.kubernetes.io/control-plane" in node.metadata.labels:
            for address in node.status.addresses:
                if address.type == "InternalIP":
                    control_plane_ips.append(address.address)

    return control_plane_ips


def get_kubeadm_join_command():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(get_master_ip()[0])
        stdin, stdout, stderr = ssh.exec_command('sudo kubeadm token create --print-join-command')
        join_command = stdout.read().decode().strip()

        f = open("add_node_command.sh", "w")
        f.write(join_command)
        f.close()
        return join_command
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        ssh.close()


def get_k8s_version():
    api = client.CoreV1Api()
    nodes = api.list_node()
    k8s_version = None

    for node in nodes.items:
        if "node-role.kubernetes.io/control-plane" in node.metadata.labels:
            k8s_version = node.status.node_info.kubelet_version

    return k8s_version


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
        #        self.edit_button = QPushButton("Изменить")
        self.delete_button = QPushButton("Удалить")
        # Подключаем контекстное меню
        self.resource_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.resource_list.customContextMenuRequested.connect(self.show_context_menu)
        #        top_right_layout.addWidget(self.edit_button)
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
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(center_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([self.width() // 5, 2 * self.width() // 5, 2 * self.width() // 5])

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

        # Устанавливаем размер окна 3/4 экрана
        screen_geometry = QGuiApplication.screens()[0].availableGeometry()
        width, height = screen_geometry.width() * 3 // 4, screen_geometry.height() * 3 // 4
        self.resize(width, height)

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
        #        self.edit_button.clicked.connect(self.show_context_menu)
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
            "Nodes",
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
            "HPA",
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

        QApplication.setStyle(QStyleFactory.create("Fusion"))
        QApplication.setPalette(dark_palette)

    def add_node(self):
        get_kubeadm_join_command()
        dialog = AddNodeDialog(self)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            ip_address = dialog.get_ip_address()
            self.run_add_node_script(ip_address)

    def run_add_node_script(self, ip_address):
        command = f"bash add_node.sh {ip_address} {get_k8s_version()}"
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
            msg_box.setWindowTitle("Добавление ноды ")
            msg_box.setText("Нода добавлена в кластер")
            msg_box.exec()


    def load_resource_items(self, item):
        global resources
        resource_type = item.text()
        api = client.CoreV1Api()

        self.resource_items_list.clear()
        if resource_type == "Pods":
            resources = api.list_namespaced_pod(namespace=self.namespace_combo.currentText())
        elif resource_type == "Nodes":
            resources = api.list_node()
        elif resource_type == "Deployments":
            api = client.AppsV1Api()
            resources = api.list_namespaced_deployment(namespace=self.namespace_combo.currentText())
        elif resource_type == "StatefulSets":
            api = client.AppsV1Api()
            resources = api.list_namespaced_stateful_set(namespace=self.namespace_combo.currentText())
        elif resource_type == "DaemonSets":
            api = client.AppsV1Api()
            resources = api.list_namespaced_daemon_set(namespace=self.namespace_combo.currentText())
        elif resource_type == "ReplicaSets":
            api = client.AppsV1Api()
            resources = api.list_namespaced_replica_set(namespace=self.namespace_combo.currentText())
        elif resource_type == "CronJobs":
            api = client.BatchV1Api()
            resources = api.list_namespaced_cron_job(namespace=self.namespace_combo.currentText())
        elif resource_type == "Jobs":
            api = client.BatchV1Api()
            resources = api.list_namespaced_job(namespace=self.namespace_combo.currentText())
        elif resource_type == "HPA":
            api = client.AutoscalingV2Api()
            resources = api.list_namespaced_horizontal_pod_autoscaler(namespace=self.namespace_combo.currentText())
        elif resource_type == "Ingresses":
            api = client.NetworkingV1Api()
            resources = api.list_namespaced_ingress(namespace=self.namespace_combo.currentText())
        elif resource_type == "Services":
            resources = api.list_namespaced_service(namespace=self.namespace_combo.currentText())
        elif resource_type == "PersistentVolumes":
            resources = api.list_persistent_volume()
        elif resource_type == "PersistentVolumeClaims":
            resources = api.list_namespaced_persistent_volume_claim(namespace=self.namespace_combo.currentText())
        elif resource_type == "ConfigMaps":
            resources = api.list_namespaced_config_map(namespace=self.namespace_combo.currentText())
        elif resource_type == "Secrets":
            resources = api.list_namespaced_secret(namespace=self.namespace_combo.currentText())
        elif resource_type == "StorageClasses":
            api = client.StorageV1Api()
            resources = api.list_namespaced_csi_storage_capacity(namespace=self.namespace_combo.currentText())

        for resource in resources.items:
            self.resource_items_list.addItem(resource.metadata.name)

    def display_resource_info(self):
        selected_item = self.resource_items_list.currentItem()
        if not selected_item:
            return

        resource_name = selected_item.text()
        namespace = self.namespace_combo.currentText()
        resource_type = self.resource_list.currentItem().text()

        config.load_kube_config('admin.conf')
        api_instance = client.CoreV1Api()

        resource_info = ""

        if resource_type in ["Deployments", "StatefulSets", "DaemonSets", "ReplicaSets", "CronJobs"]:
            api_instance = client.AppsV1Api()
        elif resource_type in ["HPA"]:
            api_instance = client.AutoscalingV1Api()
        elif resource_type in ["Ingresses"]:
            api_instance = client.NetworkingV1Api()
        elif resource_type in ["StorageClasses"]:
            api_instance = client.StorageV1Api()

        if resource_type == "Pods":
            pod = api_instance.read_namespaced_pod(resource_name, namespace)

            creation_timestamp = pod.metadata.creation_timestamp
            status = pod.status.phase
            containers = pod.spec.containers

            resource_info += f"Pod info:\n\nName: {resource_name}\nNamespace: {namespace}\n\nCreation time: {creation_timestamp}\nStatus: {status}\n\nContainers:\n"

            for container in containers:
                name = container.name
                image = container.image
                ports = container.ports if container.ports else []

                resource_info += f"\nName: {name}\nImage: {image}\nPorts: {', '.join([f'{p.container_port}/{p.protocol}' for p in ports])}\n"

        elif resource_type == "Deployments":
            deployment = api_instance.read_namespaced_deployment(resource_name, namespace)

            creation_timestamp = deployment.metadata.creation_timestamp
            replicas = deployment.spec.replicas
            available_replicas = deployment.status.available_replicas
            container = deployment.spec.template.spec.containers[0]
            image = container.image

            resource_info += f"Deployment info:\n\nName: {resource_name}\nNamespace: {namespace}\n\nCreation time: {creation_timestamp}\nReplicas: {replicas}\nAvailable Replicas: {available_replicas}\nImage: {image}\n"

        elif resource_type == "Services":
            service = api_instance.read_namespaced_service(resource_name, namespace)

            creation_timestamp = service.metadata.creation_timestamp
            cluster_ip = service.spec.cluster_ip
            ports = service.spec.ports

            resource_info += f"Service info:\n\nName: {resource_name}\nNamespace: {namespace}\n\nCreation time: {creation_timestamp}\nCluster IP: {cluster_ip}\n\nPorts:\n"

            for port in ports:
                resource_info += f"\nPort: {port.port}, Target Port: {port.target_port}\n"

        elif resource_type == "StatefulSets":
            statefulset = api_instance.read_namespaced_stateful_set(resource_name, namespace)

            creation_timestamp = statefulset.metadata.creation_timestamp
            replicas = statefulset.spec.replicas
            container = statefulset.spec.template.spec.containers[0]
            image = container.image

            resource_info += f"StatefulSet info:\n\nName: {resource_name}\nNamespace: {namespace}\n\nCreation time: {creation_timestamp}\nReplicas: {replicas}\nImage: {image}\n"

        elif resource_type == "DaemonSets":
            daemonset = api_instance.read_namespaced_daemon_set(resource_name, namespace)

            creation_timestamp = daemonset.metadata.creation_timestamp
            desired_number_scheduled = daemonset.status.desired_number_scheduled
            container = daemonset.spec.template.spec.containers[0]
            image = container.image

            resource_info += f"DaemonSet info:\n\nName: {resource_name}\nNamespace: {namespace}\n\nCreation time: {creation_timestamp}\nDesired Number Scheduled: {desired_number_scheduled}\nImage: {image}\n"

        elif resource_type == "PersistentVolumeClaims":
            pvc = api_instance.read_namespaced_persistent_volume_claim(resource_name, namespace)

            creation_timestamp = pvc.metadata.creation_timestamp
            status = pvc.status.phase
            access_modes = pvc.spec.access_modes
            storage_class_name = pvc.spec.storage_class_name

            resource_info += f"PVC info:\n\nName: {resource_name}\nNamespace: {namespace}\n\nCreation time: {creation_timestamp}\nStatus: {status}\nAccess Modes: {access_modes}\nStorage Class: {storage_class_name}\n"

        elif resource_type == "ConfigMaps":
            config_map = api_instance.read_namespaced_config_map(resource_name, namespace)

            creation_timestamp = config_map.metadata.creation_timestamp
            data = config_map.data

            resource_info += f"ConfigMap info:\n\nName: {resource_name}\nNamespace: {namespace}\n\nCreation time: {creation_timestamp}\nData:\n\n{data}\n"

        elif resource_type == "Secrets":
            secret = api_instance.read_namespaced_secret(resource_name, namespace)

            creation_timestamp = secret.metadata.creation_timestamp
            secret_type = secret.type

            resource_info += f"Secret info:\n\nName: {resource_name}\nNamespace: {namespace}\n\nCreation time: {creation_timestamp}\nType: {secret_type}\n"

        elif resource_type == "CronJobs":
            api_instance = client.BatchV1beta1Api()
            cron_job = api_instance.read_namespaced_cron_job(resource_name, namespace)

            creation_timestamp = cron_job.metadata.creation_timestamp
            schedule = cron_job.spec.schedule
            job_template = cron_job.spec.job_template

            resource_info += f"CronJob info:\n\nName: {resource_name}\nNamespace: {namespace}\n\nCreation time: {creation_timestamp}\nSchedule: {schedule}\nJob Template:\n\n{job_template}\n"

        elif resource_type == "ReplicaSets":
            replica_set = api_instance.read_namespaced_replica_set(resource_name, namespace)

            creation_timestamp = replica_set.metadata.creation_timestamp
            replicas = replica_set.spec.replicas
            container = replica_set.spec.template.spec.containers[0]
            image = container.image

            resource_info += f"ReplicaSet info:\n\nName: {resource_name}\nNamespace: {namespace}\n\nCreation time: {creation_timestamp}\nReplicas: {replicas}\nImage: {image}\n"

        elif resource_type == "HPA":
            hpa = api_instance.read_namespaced_horizontal_pod_autoscaler(resource_name, namespace)

            creation_timestamp = hpa.metadata.creation_timestamp
            min_replicas = hpa.spec.min_replicas
            max_replicas = hpa.spec.max_replicas

            resource_info += f"HPA info:\n\nName: {resource_name}\nNamespace: {namespace}\n\nCreation time: {creation_timestamp}\nMin Replicas: {min_replicas}\nMax Replicas: {max_replicas}\n"

        elif resource_type == "Ingresses":
            ingress = api_instance.read_namespaced_ingress(resource_name, namespace)

            creation_timestamp = ingress.metadata.creation_timestamp
            rules = ingress.spec.rules

            resource_info += f"Ingress info:\n\nName: {resource_name}\nNamespace: {namespace}\n\nCreation time: {creation_timestamp}\nRules:\n"

            for rule in rules:
                resource_info += f"\nHost: {rule.host}\n"
                for path in rule.http.paths:
                    resource_info += f"Path: {path.path}, Backend: {path.backend.service.name}:{path.backend.service.port.name}\n"
        elif resource_type == "Nodes":
            status = 'Not Ready'
            node = api_instance.read_node(resource_name)
            creation_timestamp = node.metadata.creation_timestamp
            for condition in node.status.conditions:
                if condition.type == 'Ready':
                    status = 'Ready'

            resource_info += f"Ingress info:\n\nName: {resource_name}\nNamespace: {namespace}\n\nCreation time: {creation_timestamp}\n\nStatus :  {status}"

        elif resource_type == "StorageClasses":
            api_instance = client.StorageV1Api()
            storage_class = api_instance.read_storage_class(resource_name)

            creation_timestamp = storage_class.metadata.creation_timestamp
            provisioner = storage_class.provisioner
            parameters = storage_class.parameters

            resource_info += f"StorageClass info:\n\nName: {resource_name}\n\nCreation time: {creation_timestamp}\nProvisioner: {provisioner}\nParameters: {parameters}\n"

        self.info_text.setPlainText(resource_info)

    def show_context_menu(self, position):
        resource_type = self.resource_list.currentItem().text()
        if resource_type in ["Deployments", "StatefulSets", "ReplicaSets", "HPA"]:
            context_menu = QMenu(self.resource_list)
            edit_action = QAction("Изменить")
            edit_action.triggered.connect(self.edit_resource)
            context_menu.addAction(edit_action)
            context_menu.exec(self.resource_list.viewport().mapToGlobal(position))

    def edit_resource(self):
        resource_type = self.resource_list.currentItem().text()

        if resource_type == "Deployments":
            self.edit_deployment()
        elif resource_type == "StatefulSets":
            self.edit_statefulset()
        elif resource_type == "ReplicaSets":
            self.edit_replicaset()
        elif resource_type == "HPA":
            self.edit_hpa()

    def edit_deployment(self):
        selected_item = self.resource_items_list.currentItem()
        api_instance = client.AppsV1Api()
        if not selected_item:
            return

        resource_name = selected_item.text()
        namespace = self.namespace_combo.currentText()

        # Получение текущих значений Deployment из кластера
        deployment = api_instance.read_namespaced_deployment(resource_name, namespace)
        current_image = deployment.spec.template.spec.containers[0].image
        current_replicas = deployment.spec.replicas
        current_limits = deployment.spec.template.spec.containers[0].resources.limits
        current_requests = deployment.spec.template.spec.containers[0].resources.requests

        # Создание и отображение диалога редактирования Deployment
        dialog = DeploymentEditDialog(self, current_image, current_replicas, current_limits, current_requests)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            # Получение обновленных значений из диалога
            new_image, new_replicas, new_limits, new_requests = dialog.get_updated_values()

            # Обновление Deployment в кластере
            deployment.spec.template.spec.containers[0].image = new_image
            deployment.spec.replicas = new_replicas
            deployment.spec.template.spec.containers[0].resources.limits = new_limits
            deployment.spec.template.spec.containers[0].resources.requests = new_requests

            api_instance.patch_namespaced_deployment(resource_name, namespace, deployment)

    def edit_statefulset(self):
        selected_item = self.resource_items_list.currentItem()
        api_instance = client.AppsV1Api()
        if not selected_item:
            return

        resource_name = selected_item.text()
        namespace = self.namespace_combo.currentText()

        # Получение текущих значений Deployment из кластера
        statefulset = api_instance.read_namespaced_stateful_set(resource_name, namespace)
        current_image = statefulset.spec.template.spec.containers[0].image
        current_replicas = statefulset.spec.replicas
        current_limits = statefulset.spec.template.spec.containers[0].resources.limits
        current_requests = statefulset.spec.template.spec.containers[0].resources.requests

        # Создание и отображение диалога редактирования Deployment
        dialog = StatefulSetEditDialog(self, current_image, current_replicas, current_limits, current_requests)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            # Получение обновленных значений из диалога
            new_image, new_replicas, new_limits, new_requests = dialog.get_updated_values()

            # Обновление Deployment в кластере
            statefulset.spec.template.spec.containers[0].image = new_image
            statefulset.spec.replicas = new_replicas
            statefulset.spec.template.spec.containers[0].resources.limits = new_limits
            statefulset.spec.template.spec.containers[0].resources.requests = new_requests

            api_instance.patch_namespaced_stateful_set(resource_name, namespace, statefulset)

    def edit_replicaset(self):
        selected_item = self.resource_items_list.currentItem()
        api_instance = client.AppsV1Api()
        if not selected_item:
            return

        resource_name = selected_item.text()
        namespace = self.namespace_combo.currentText()

        # Получение текущих значений Deployment из кластера
        replicatset = api_instance.read_namespaced_replica_set(resource_name, namespace)
        current_image = replicatset.spec.template.spec.containers[0].image
        current_replicas = replicatset.spec.replicas
        current_limits = replicatset.spec.template.spec.containers[0].resources.limits
        current_requests = replicatset.spec.template.spec.containers[0].resources.requests

        # Создание и отображение диалога редактирования Deployment
        dialog = ReplicaSetEditDialog(self, current_image, current_replicas, current_limits, current_requests)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            # Получение обновленных значений из диалога
            new_image, new_replicas, new_limits, new_requests = dialog.get_updated_values()

            # Обновление Deployment в кластере
            replicatset.spec.template.spec.containers[0].image = new_image
            replicatset.spec.replicas = new_replicas
            replicatset.spec.template.spec.containers[0].resources.limits = new_limits
            replicatset.spec.template.spec.containers[0].resources.requests = new_requests

            api_instance.patch_namespaced_replica_set(resource_name, namespace, replicatset)

    def edit_hpa(self):
        selected_item = self.resource_items_list.currentItem()
        api_instance = client.AutoscalingV2Api()
        if not selected_item:
            return

        hpa_name = selected_item.text()
        namespace = self.namespace_combo.currentText()

        # Получить текущий объект HPA
        hpa = api_instance.read_namespaced_horizontal_pod_autoscaler(hpa_name, namespace)

        # Извлечь текущие значения
        current_min_replicas = hpa.spec.min_replicas
        current_max_replicas = hpa.spec.max_replicas
        current_cpu = hpa.spec.target_cpu_utilization_percentage
        current_memory = hpa.spec.target_memory_utilization_percentage

        # Создать и показать диалог редактирования HPA
        dialog = HPAEditDialog(self, current_min_replicas, current_max_replicas, current_cpu, current_memory)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            # Получить обновленные значения из диалога
            new_min_replicas, new_max_replicas, new_cpu, new_memory = dialog.get_updated_values()

            # Обновить объект HPA с новыми значениями
            hpa.spec.min_replicas = new_min_replicas
            hpa.spec.max_replicas = new_max_replicas
            hpa.spec.target_cpu_utilization_percentage = new_cpu
            hpa.spec.target_memory_utilization_percentage = new_memory

            # Сохранить изменения
            api_instance.patch_namespaced_horizontal_pod_autoscaler(hpa_name, namespace, hpa)

            # Обновить информацию на экране
            self.load_resource_items(self.resource_list.currentItem())

    def delete_resource(self):
        resource_name = self.resource_items_list.currentItem().text()
        resource_type = self.resource_list.currentItem().text()
        namespace = self.namespace_combo.currentText()

        if resource_type == "Pods":
            self.delete_pod(namespace, resource_name)
        elif resource_type == "Deployments":
            self.delete_deployment(namespace, resource_name)
        elif resource_type == "StatefulSets":
            self.delete_statefulset(namespace, resource_name)
        elif resource_type == "DaemonSets":
            self.delete_daemonset(namespace, resource_name)
        elif resource_type == "CronJobs":
            self.delete_cronjob(namespace, resource_name)
        elif resource_type == "Jobs":
            self.delete_job(namespace, resource_name)
        elif resource_type == "ConfigMaps":
            self.delete_configmap(namespace, resource_name)
        elif resource_type == "Secrets":
            self.delete_secret(namespace, resource_name)
        elif resource_type == "ReplicaSets":
            self.delete_replicaset(namespace, resource_name)
        elif resource_type == "HPA":
            self.delete_hpa(namespace, resource_name)
        elif resource_type == "Services":
            self.delete_service(namespace, resource_name)
        elif resource_type == "Ingresses":
            self.delete_ingress(namespace, resource_name)
        elif resource_type == "StorageClasses":
            self.delete_sc(namespace, resource_name)
        elif resource_type == "PersistentVolumeClaims":
            self.delete_pvc(namespace, resource_name)
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

    def delete_statefulset(self, namespace, statefulset_name):
        api = client.AppsV1Api()
        api.delete_namespaced_stateful_set(namespace=namespace, name=statefulset_name)

    def delete_replicaset(self, namespace, replicaset_name):
        api = client.AppsV1Api()
        api.delete_namespaced_replica_set(namespace=namespace, name=replicaset_name)

    def delete_daemonset(self, namespace, daemonset_name):
        api = client.AppsV1Api()
        api.delete_namespaced_daemon_set(namespace=namespace, name=daemonset_name)

    def delete_cronjob(self, namespace, cronjob_name):
        api = client.BatchV1Api()
        api.delete_namespaced_cron_job(namespace=namespace, name=cronjob_name)

    def delete_job(self, namespace, job_name):
        api = client.BatchV1Api()
        api.delete_namespaced_job(namespace=namespace, name=job_name)

    def delete_ingress(self, namespace, ingress_name):
        api = client.NetworkingV1Api()
        api.delete_namespaced_ingress(namespace=namespace, name=ingress_name)

    def delete_service(self, namespace, service_name):
        api = client.CoreV1Api()
        api.delete_namespaced_service(namespace=namespace, name=service_name)

    def delete_configmap(self, namespace, configmap_name):
        api = client.CoreV1Api()
        api.delete_namespaced_config_map(namespace=namespace, name=configmap_name)

    def delete_secret(self, namespace, secret_name):
        api = client.CoreV1Api()
        api.delete_namespaced_secret(namespace=namespace, name=secret_name)

    def delete_sc(self, namespace, sc_name):
        api = client.StorageV1Api()
        api.delete_namespaced_csi_storage_capacity(namespace=namespace, name=sc_name)

    def delete_hpa(self, namespace, pvc_name):
        api = client.AutoscalingV2Api()
        api.delete_namespaced_horizontal_pod_autoscaler(namespace=namespace, name=pvc_name)

    def delete_pvc(self, namespace, pvc_name):
        api = client.CoreV1Api()
        api.delete_namespaced_persistent_volume_claim(namespace=namespace, name=pvc_name)

    def delete_pv(self, pv_name):
        api = client.CoreV1Api()
        api.delete_persistent_volume(name=pv_name)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = KubernetesAdminGUI()
    gui.show()
    sys.exit(app.exec())
