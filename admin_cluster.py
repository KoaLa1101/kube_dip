import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from kubernetes import config, client


class KubernetesGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Kubernetes Admin")
        self.geometry("800x600")

        self.create_widgets()

    def create_widgets(self):
        self.file_label = tk.Label(self, text="Admin Config File:")
        self.file_label.grid(row=0, column=0, sticky="w")

        self.file_entry = tk.Entry(self, width=50)
        self.file_entry.grid(row=0, column=1)

        self.browse_button = tk.Button(self, text="Browse", command=self.load_config_file)
        self.browse_button.grid(row=0, column=2)

        # Namespace label and combobox
        self.namespace_label = tk.Label(self, text="Namespace:")
        self.namespace_label.grid(row=0, column=0, sticky="w")

        self.namespace_combobox = ttk.Combobox(self, values=self.get_namespaces(), state="readonly")
        self.namespace_combobox.grid(row=0, column=1, sticky="w")
        self.namespace_combobox.bind("<<ComboboxSelected>>", self.on_namespace_selected)

        # Resources listbox
        self.resources_listbox = tk.Listbox(self, width=50, height=20)
        self.resources_listbox.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

        # Scrollbar for resources listbox
        self.resources_listbox_scrollbar = tk.Scrollbar(self, orient="vertical", command=self.resources_listbox.yview)
        self.resources_listbox_scrollbar.grid(row=1, column=2, sticky="ns")
        self.resources_listbox.config(yscrollcommand=self.resources_listbox_scrollbar.set)

        # Buttons
        self.info_button = tk.Button(self, text="Info", command=self.show_resource_info)
        self.info_button.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        self.delete_button = tk.Button(self, text="Delete", command=self.delete_resource)
        self.delete_button.grid(row=2, column=1, padx=5, pady=5)

        self.logs_button = tk.Button(self, text="Logs", command=self.show_resource_logs)
        self.logs_button.grid(row=2, column=1, padx=5, pady=5, sticky="e")

    def load_config_file(self):
        file_path = filedialog.askopenfilename()
        self.file_entry.delete(0, tk.END)
        self.file_entry.insert(0, file_path)

        config.load_kube_config(config_file=file_path)
        self.load_namespaces()

    def on_namespace_selected(self, _):
        self.load_resources()

    def load_namespaces(self):
        v1 = client.CoreV1Api()
        namespaces = v1.list_namespace().items
        self.namespace_combobox["values"] = [ns.metadata.name for ns in namespaces]
        self.namespace_combobox.bind("<<ComboboxSelected>>", lambda _: self.load_resources())
        self.namespace_combobox.bind("<<ComboboxSelected>>", self.on_namespace_selected)

    def load_resources(self):
        selected_namespace = self.namespace_combobox.get()
        if not selected_namespace:
            return

        v1 = client.CoreV1Api()
        pods = v1.list_namespaced_pod(selected_namespace).items

        # Сортировка подов в обратном порядке по времени создания
        sorted_pods = sorted(pods, key=lambda pod: pod.metadata.creation_timestamp, reverse=True)

        self.resources_listbox.delete(0, tk.END)
        for pod in sorted_pods:
            self.resources_listbox.insert(tk.END, pod.metadata.name)

    def get_selected_pod(self):
        try:
            selected_pod_name = self.resources_listbox.get(self.resources_listbox.curselection())
        except tk.TclError:
            tk.messagebox.showerror("Error", "Please select a pod.")
            return None, None

        selected_namespace = self.namespace_combobox.get()
        return selected_pod_name, selected_namespace

    def show_resource_info(self):
        pod = self.get_selected_pod()
        if pod:
            info = f"Name: {pod.metadata.name}\n" \
                   f"Namespace: {pod.metadata.namespace}\n" \
                   f"Status: {pod.status.phase}\n" \
                   f"Start Time: {pod.status.start_time}"
            tk.messagebox.showinfo("Pod Information", info)

    def delete_resource(self):
        pod = self.get_selected_pod()
        if pod:
            v1 = client.CoreV1Api()
            v1.delete_namespaced_pod(pod.metadata.name, pod.metadata.namespace)
            self.load_resources()

    def show_resource_logs(self):
        pod_name, namespace = self.get_selected_pod()
        if pod_name and namespace:
            v1 = client.CoreV1Api()
            pod = v1.read_namespaced_pod(pod_name, namespace)
            container_name = None

            if len(pod.spec.containers) > 1:
                container_names = [container.name for container in pod.spec.containers]
                container_name = tk.simpledialog.askstring("Logs", f"Select container: {', '.join(container_names)}")
                if container_name not in container_names:
                    tk.messagebox.showerror("Error", "Invalid container name.")
                    return
            elif len(pod.spec.containers) == 1:
                container_name = pod.spec.containers[0].name

            logs = v1.read_namespaced_pod_log(pod_name, namespace, container=container_name)
            tk.messagebox.showinfo("Pod Logs", logs)

    def show_resource_info(self):
        pass

    def delete_resource(self):
        pass

    def show_resource_logs(self):
        pass


if __name__ == "__main__":
    app = KubernetesGUI()
    app.mainloop()
