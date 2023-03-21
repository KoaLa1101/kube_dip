import notebook as notebook
import yaml
import sys
from tkinter import *
from tkinter import ttk, filedialog, messagebox, simpledialog
from kubernetes import client, config, stream
from ttkthemes import ThemedTk
import threading



def read_yaml_file():
    file_path = filedialog.askopenfilename(title="Select YAML file")
    if not file_path:
        return None

    with open(file_path, "r") as file:
        yaml_content = yaml.safe_load(file)

    return yaml_content

def load_kube_config(path):
    config.load_kube_config(config_file=path)

# Получение списка PersistentVolumes
def get_pvs():
    api_instance = client.CoreV1Api()
    try:
        pvs = api_instance.list_persistent_volume()
        return pvs
    except client.exceptions.ApiException as e:
        print(f"Failed to get PersistentVolumes: {e}")
        raise

# Получение списка PersistentVolumeClaims
def get_pvcs(namespace):
    api_instance = client.CoreV1Api()
    try:
        pvcs = api_instance.list_namespaced_persistent_volume_claim(namespace)
        return pvcs
    except client.exceptions.ApiException as e:
        print(f"Failed to get PersistentVolumeClaims: {e}")
        raise

# Получение списка CronJobs
def get_cronjobs(namespace):
    api_instance = client.BatchV1beta1Api()
    try:
        cronjobs = api_instance.list_namespaced_cron_job(namespace)
        return cronjobs
    except client.exceptions.ApiException as e:
        print(f"Failed to get CronJobs: {e}")
        raise

# Получение списка HorizontalPodAutoscalers
def get_hpas(namespace):
    api_instance = client.AutoscalingV2beta2Api()
    try:
        hpas = api_instance.list_namespaced_horizontal_pod_autoscaler(namespace)
        return hpas
    except client.exceptions.ApiException as e:
        print(f"Failed to get HorizontalPodAutoscalers: {e}")
        raise


# Get pod logs
def get_pod_logs(pod_name, namespace):
    api_instance = client.CoreV1Api()
    return api_instance.read_namespaced_pod_log(pod_name, namespace)

# Get pod information
def get_pod_info(pod_name, namespace):
    api_instance = client.CoreV1Api()
    return api_instance.read_namespaced_pod(pod_name, namespace)

# Execute command in a pod
def execute_command_in_pod(pod_name, namespace):
    api_instance = client.CoreV1Api()
    exec_command = ['/bin/sh']
    ws = stream.stream(api_instance.connect_get_namespaced_pod_exec,
                       pod_name,
                       namespace,
                       command=exec_command,
                       stderr=True,
                       stdin=True,
                       stdout=True,
                       tty=False,
                       _preload_content=False)

    # Поток вывода и ввода
    while ws.is_open():
        command = input("Enter command: ")
        if command.strip() == "exit":
            break

        ws.write_stdin(command + "\n")
        try:
            while True:
                stdout = ws.read_stdout(timeout=3)
                stderr = ws.read_stderr(timeout=3)
                if stdout:
                    print(stdout)
                if stderr:
                    print(stderr, file=sys.stderr)
                if not stdout and not stderr:
                    break
        except (stream.exceptions.WebSocketTimeout, TimeoutError):
            pass
    ws.close()


def select_config_file():
    file_path = filedialog.askopenfilename()
    kube_config_var.set(file_path)

def delete_pod(pod_name, namespace):
    api_instance = client.CoreV1Api()
    try:
        api_instance.delete_namespaced_pod(pod_name, namespace, body=client.V1DeleteOptions())
    except client.exceptions.ApiException as e:
        print(f"Failed to delete pod '{pod_name}': {e}")
        raise

# Получение списка StatefulSet
def get_statefulsets(namespace):
    api_instance = client.AppsV1Api()
    statefulsets = api_instance.list_namespaced_stateful_set(namespace)
    return statefulsets.items

# Получение списка DaemonSet
def get_daemonsets(namespace):
    api_instance = client.AppsV1Api()
    daemonsets = api_instance.list_namespaced_daemon_set(namespace)
    return daemonsets.items

def update_statefulset_list():
    statefulset_list.delete(0, END)
    statefulsets = get_statefulsets(namespace_var.get())
    for statefulset in statefulsets:
        statefulset_list.insert(END, f"{statefulset.metadata.name}")

def update_daemonset_list():
    daemonset_list.delete(0, END)
    daemonsets = get_daemonsets(namespace_var.get())
    for daemonset in daemonsets:
        daemonset_list.insert(END, f"{daemonset.metadata.name}")



# Удаление выбранного StatefulSet
def delete_selected_statefulset():
    selected_statefulset = statefulset_list.get(ACTIVE)
    if not selected_statefulset:
        messagebox.showerror("Error", "No StatefulSet is selected")
        return

    statefulset_name = selected_statefulset.split()[0]
    namespace = namespace_var.get()
    try:
        delete_statefulset(statefulset_name, namespace)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete StatefulSet '{statefulset_name}': {e}")

# Удаление выбранного DaemonSet
def delete_selected_daemonset():
    selected_daemonset = daemonset_list.get(ACTIVE)
    if not selected_daemonset:
        messagebox.showerror("Error", "No DaemonSet is selected")
        return

    daemonset_name = selected_daemonset.split()[0]
    namespace = namespace_var.get()
    try:
        delete_daemonset(daemonset_name, namespace)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete DaemonSet '{daemonset_name}': {e}")


def delete_statefulset(name, namespace):
    api_instance = client.AppsV1Api()
    api_instance.delete_namespaced_stateful_set(name, namespace)

def delete_daemonset(name, namespace):
    api_instance = client.AppsV1Api()
    api_instance.delete_namespaced_daemon_set(name, namespace)


def update_namespace_list():
    load_kube_config(kube_config_var.get())
    v1 = client.CoreV1Api()
    ret = v1.list_namespace()
    namespace_menu["menu"].delete(0, END)
    for i in ret.items:
        namespace_menu["menu"].add_command(label=i.metadata.name, command=lambda value=i.metadata.name: namespace_var.set(value))

def update_pod_list():
    selected_namespace = namespace_var.get()
    load_kube_config(kube_config_var.get())
    v1 = client.CoreV1Api()
    ret = v1.list_namespaced_pod(selected_namespace)
    pod_list.delete(0, END)
    for i in ret.items:
        pod_list.insert(END, i.metadata.name)


def delete_selected_pod():
    selected_pod = pod_list.get(ACTIVE)
    if selected_pod:
        try:
            delete_pod(selected_pod, namespace_var.get())
            messagebox.showinfo("Success", f"Pod {selected_pod} deleted.")
            update_pod_list()
        except Exception as e:
            messagebox.showerror("Error", str(e))

def get_selected_pod_logs():
    selected_pod = pod_list.get(ACTIVE)
    if selected_pod:
        try:
            logs = get_pod_logs(selected_pod, namespace_var.get())
            show_logs_window(selected_pod, logs)
        except Exception as e:
            messagebox.showerror("Error", str(e))

def show_logs_window(pod_name, logs):
    logs_window = Toplevel(root)
    logs_window.title(f"Logs for {pod_name}")

    logs_text = Text(logs_window, wrap=WORD)
    logs_text.insert(INSERT, logs)
    logs_text.pack(expand=YES, fill=BOTH)

    logs_window.mainloop()

def get_selected_pod_info():
    selected_pod = pod_list.get(ACTIVE)
    if selected_pod:
        try:
            pod_info = get_pod_info(selected_pod, namespace_var.get())
            show_pod_info_window(selected_pod, pod_info)
        except Exception as e:
            messagebox.showerror("Error", str(e))

def show_pod_info_window(pod_name, pod_info):
    info_window = Toplevel(root)
    info_window.title(f"Info for {pod_name}")

    info_text = Text(info_window, wrap=WORD)
    info_text.insert(INSERT, str(pod_info))
    info_text.pack(expand=YES, fill=BOTH)

    info_window.mainloop()

def execute_command_in_selected_pod():
    selected_pod = pod_list.get(ACTIVE)
    if not selected_pod:
        messagebox.showerror("Error", "No pod is selected")
        return

    # Получаем имя пода и namespace
    pod_name = selected_pod.split()[0]
    namespace = namespace_var.get()

    try:
        execute_command_in_pod(pod_name, namespace)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to execute command in pod '{pod_name}': {e}")

def show_output_window(title, output):
    output_window = Toplevel(root)
    output_window.title(title)

    output_text = Text(output_window, wrap=WORD)
    output_text.insert(INSERT, output)
    output_text.pack(expand=YES, fill=BOTH)

    output_window.mainloop()


def update_node_list():
    load_kube_config(kube_config_var.get())
    v1 = client.CoreV1Api()
    ret = v1.list_node()
    node_list.delete(0, END)
    for i in ret.items:
        node_list.insert(END, i.metadata.name)

def update_deployment_list():
    selected_namespace = namespace_var.get()
    load_kube_config(kube_config_var.get())
    api_instance = client.AppsV1Api()
    ret = api_instance.list_namespaced_deployment(selected_namespace)
    deployment_list.delete(0, END)
    for i in ret.items:
        deployment_list.insert(END, i.metadata.name)

def create_deployment():
    deployment_name = deployment_name_entry.get()
    image_name = image_entry.get()
    replicas = int(replicas_entry.get())
    pull_secrets = image_pull_secrets_entry.get().split(',')

    selected_namespace = namespace_var.get()
    load_kube_config(kube_config_var.get())

    container = client.V1Container(
        name=deployment_name,
        image=image_name,
        ports=[client.V1ContainerPort(container_port=int(port)) for port in container_ports_entry.get().split(',')],
    )

    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": deployment_name}),
        spec=client.V1PodSpec(containers=[container], image_pull_secrets=[client.V1LocalObjectReference(name=secret.strip()) for secret in pull_secrets]),
    )

    spec = client.V1DeploymentSpec(
        replicas=replicas,
        template=template,
        selector=client.V1LabelSelector(match_labels={"app": deployment_name}),
    )

    deployment = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=deployment_name),
        spec=spec,
    )

    api_instance = client.AppsV1Api()
    api_instance.create_namespaced_deployment(
        body=deployment,
        namespace=selected_namespace,
    )

    update_deployment_list()

def delete_selected_deployment():
    selected_deployment = deployment_list.get(deployment_list.curselection()).split(" (Lifetime:")[0]
    if not selected_deployment:
        return

    selected_namespace = namespace_var.get()
    load_kube_config(kube_config_var.get())
    api_instance = client.AppsV1Api()
    api_instance.delete_namespaced_deployment(name=selected_deployment, namespace=selected_namespace)

    update_deployment_list()

def update_service_list():
    selected_namespace = namespace_var.get()
    load_kube_config(kube_config_var.get())
    v1 = client.CoreV1Api()
    ret = v1.list_namespaced_service(selected_namespace)
    service_list.delete(0, END)
    for i in ret.items:
        ports_str = ', '.join([f"{p.port}:{p.target_port}" for p in i.spec.ports])
        service_list.insert(END, f"{i.metadata.name} (Ports: {ports_str}")

def create_service():
    service_name = service_name_entry.get()
    selected_namespace = namespace_var.get()
    service_type = service_type_var.get()
    ports_str = service_ports_entry.get().split(',')
    ports = [client.V1ServicePort(name=f"{service_name}-{p.split(':')[0]}", port=int(p.split(':')[0]), target_port=int(p.split(':')[1])) for p in ports_str]

    load_kube_config(kube_config_var.get())

    service_spec = client.V1ServiceSpec(
        selector={"app": service_name},
        ports=ports,
        type=service_type
    )

    service = client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=client.V1ObjectMeta(name=service_name),
        spec=service_spec
    )

    v1 = client.CoreV1Api()
    v1.create_namespaced_service(
        body=service,
        namespace=selected_namespace
    )

    update_service_list()

def delete_selected_service():
    selected_service = service_list.get(service_list.curselection()).split(" (Ports:")[0]
    if not selected_service:
        return

    selected_namespace = namespace_var.get()
    load_kube_config(kube_config_var.get())
    v1 = client.CoreV1Api()
    v1.delete_namespaced_service(name=selected_service, namespace=selected_namespace)

    update_service_list()

def get_selected_service_info():
    selected_service = service_list.get(service_list.curselection()).split(" (Ports:")[0]
    if not selected_service:
        return None

    selected_namespace = namespace_var.get()
    load_kube_config(kube_config_var.get())
    v1 = client.CoreV1Api()
    return v1.read_namespaced_service(selected_service, selected_namespace)

def show_service_info():
    service_info = get_selected_service_info()
    if not service_info:
        return

    info_window = Toplevel(root)
    info_window.title("Service Info")
    info_window_width = info_window.winfo_screenwidth()
    info_window_height = info_window.winfo_screenheight()
    info_window.geometry(f"{info_window_width}x{info_window_height}")

    info_text = Text(info_window,wrap=WORD)
    info_text.insert(INSERT, str(service_info))
    info_text.pack(expand=YES, fill=BOTH)

    info_window.mainloop()

def update_resources():
    # Обновление ресурсов
    update_namespace_list()
    update_pod_list()
    update_deployment_list()
    update_service_list()
    update_statefulset_list()
    update_daemonset_list()

    # Запуск обновления каждые 15 секунд
    threading.Timer(15, update_resources).start()
def show_resource_action_popup(event):
    resource_type = resource_tree.item(resource_tree.selection()[0], "values")[0]
    resource_name = resource_tree.item(resource_tree.selection()[0], "values")[1]
    popup_menu.post(event.x_root, event.y_root)


root = ThemedTk(theme="radiance")
root.title("Kubernetes GUI")
# Get screen width and height
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Calculate the position of the window
x = (screen_width / 2) - (screen_width / 2)
y = (screen_height / 2) - (screen_height / 2)

# Set the dimensions of the screen and where it is placed
root.geometry(f'{screen_width}x{screen_height}+{int(x)}+{int(y)}')



main_frame = Frame(root)
main_frame.pack(expand=1, fill="both")


left_frame = Frame(main_frame)
left_frame.pack(side=LEFT, expand=0, fill=Y)

right_frame = Frame(main_frame)
right_frame.pack(side=RIGHT, expand=1, fill="both")

kube_config_label = Label(left_frame, text="Kubeconfig:")
kube_config_label.pack()

kube_config_var = StringVar()
kube_config_entry = Entry(left_frame, textvariable=kube_config_var)
kube_config_entry.pack()

select_config_button = Button(left_frame, text="Select Config File", command=select_config_file)
select_config_button.pack(pady=5)

namespace_label = Label(left_frame, text="Namespace:")
namespace_label.pack()

namespace_var = StringVar()
namespace_menu = OptionMenu(left_frame, namespace_var, "default")
namespace_menu.pack()

update_namespace_button = Button(left_frame, text="Update Namespace List", command=update_namespace_list)
update_namespace_button.pack(pady=10)

tab_control = ttk.Notebook(right_frame)

pod_frame = ttk.Frame(tab_control)
tab_control.add(pod_frame, text="Pods")

node_frame = ttk.Frame(tab_control)
tab_control.add(node_frame, text="Nodes")

deployment_frame = ttk.Frame(tab_control)
tab_control.add(deployment_frame, text="Deployments")

service_frame = ttk.Frame(tab_control)
tab_control.add(service_frame, text="Services")

statefulset_frame = ttk.Frame(tab_control)
tab_control.add(statefulset_frame, text="Statefulsets")

daemonset_frame = ttk.Frame(tab_control)
tab_control.add(statefulset_frame, text="Daemonsets")

pod_list = Listbox(pod_frame, height=30, width=100)
pod_list.pack()

update_pod_button = Button(pod_frame, text="Update Pod List", command=update_pod_list)
update_pod_button.pack(pady=5)

delete_pod_button = Button(pod_frame, text="Delete Pod", command=delete_selected_pod)
delete_pod_button.pack(pady=5)

view_logs_button = Button(pod_frame, text="View Logs", command=get_selected_pod_logs)
view_logs_button.pack(pady=5)

view_info_button = Button(pod_frame, text="View Info", command=get_selected_pod_info)
view_info_button.pack(pady=5)

execute_command_button = Button(pod_frame, text="Execute Command", command=execute_command_in_selected_pod)
execute_command_button.pack(pady=5)


node_list = Listbox(node_frame, height=20, width=100)
node_list.pack()

update_node_button = Button(node_frame, text="Update Node List", command=update_node_list)
update_node_button.pack(pady=5)

deployment_list = Listbox(deployment_frame, height=20, width=100)
deployment_list.pack()

deployment_name_label = Label(deployment_frame, text="Deployment Name:")
deployment_name_label.pack()
deployment_name_entry = Entry(deployment_frame)
deployment_name_entry.pack()

image_label = Label(deployment_frame, text="Image:")
image_label.pack()
image_entry = Entry(deployment_frame)
image_entry.pack()

replicas_label = Label(deployment_frame, text="Replicas:")
replicas_label.pack()
replicas_entry = Entry(deployment_frame)
replicas_entry.pack()

container_ports_label = Label(deployment_frame, text="Container Ports (comma-separated):")
container_ports_label.pack()
container_ports_entry = Entry(deployment_frame)
container_ports_entry.pack()

image_pull_secrets_label = Label(deployment_frame, text="Image Pull Secrets (comma-separated):")
image_pull_secrets_label.pack()
image_pull_secrets_entry = Entry(deployment_frame)
image_pull_secrets_entry.pack()

create_deployment_button = Button(deployment_frame, text="Create Deployment", command=create_deployment)
create_deployment_button.pack(pady=5)

delete_deployment_button = Button(deployment_frame, text="Delete Deployment", command=delete_selected_deployment)
delete_deployment_button.pack(pady=5)

update_deployment_button = Button(deployment_frame, text="Update Deployment List", command=update_deployment_list)
update_deployment_button.pack(pady=5)

service_list = Listbox(service_frame, height=20, width=100)
service_list.pack()

delete_service_button = Button(service_frame, text="Delete Service", command=delete_selected_service)
delete_service_button.pack(pady=5)

update_service_button = Button(service_frame, text="Update Service List", command=update_service_list)
update_service_button.pack(pady=5)

service_info_button = Button(service_frame, text="Service Info", command=show_service_info)
service_info_button.pack(pady=5)

service_name_label = Label(service_frame, text="Service Name:")
service_name_label.pack()
service_name_entry = Entry(service_frame)
service_name_entry.pack()

service_type_label = Label(service_frame, text="Service Type:")
service_type_label.pack()

service_type_var = StringVar()
service_type_menu = OptionMenu(service_frame, service_type_var, "ClusterIP", "NodePort", "LoadBalancer")
service_type_menu.pack()

service_ports_label = Label(service_frame, text="Service Ports (comma-separated, format: port:targetPort):")
service_ports_label.pack()
service_ports_entry = Entry(service_frame)
service_ports_entry.pack()


create_service_button = Button(service_frame, text="Create Service", command=create_service)
create_service_button.pack(pady=5)

# Создание вкладки StatefulSet


statefulset_list = Listbox(statefulset_frame, width=120, height=30)
statefulset_list.pack(side=LEFT, fill=Y)
statefulset_list_scrollbar = Scrollbar(statefulset_frame)
statefulset_list_scrollbar.pack(side=RIGHT, fill=Y)
statefulset_list.config(yscrollcommand=statefulset_list_scrollbar.set)
statefulset_list_scrollbar.config(command=statefulset_list.yview)

statefulset_delete_button = Button(statefulset_frame, text="Delete", command=delete_selected_statefulset)
statefulset_delete_button.pack(side=BOTTOM)

# Создание вкладки DaemonSet


daemonset_list = Listbox(daemonset_frame, width=120, height=30)
daemonset_list.pack(side=LEFT, fill=Y)
daemonset_list_scrollbar = Scrollbar(daemonset_frame)
daemonset_list_scrollbar.pack(side=RIGHT, fill=Y)
daemonset_list.config(yscrollcommand=daemonset_list_scrollbar.set)
daemonset_list_scrollbar.config(command=daemonset_list.yview)

daemonset_delete_button = Button(daemonset_frame, text="Delete", command=delete_selected_daemonset)
daemonset_delete_button.pack(side=BOTTOM)


tab_control.pack(expand=1, fill="both")
root.mainloop()


