import customtkinter as ctk
from tkinter import messagebox
import threading
import time
import random
import requests
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import statistics
import queue
import json
from urllib.parse import urljoin
import random
import math

# Configuration
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Global variables
response_times = []
status_codes = {}
errors = []
test_running = False
log_queue = queue.Queue()
endpoints_to_test = []
available_endpoints = []  # Se llenará automáticamente
datos_usuarios = [
    {"username": "sergi", "password": "1234"},
    {"username": "lali", "password": "1234"},
    {"username": "adam", "password": "1234"},
    {"username": "david", "password": "1234"},
    {"username": "Lluis", "password": "1"},
    {"username": "user2", "password": "password2"},
    {"username": "user3", "password": "password3"},
    {"username": "user4", "password": "password4"},
    {"username": "user5", "password": "password5"},
    {"username": "user6", "password": "password6"},
    {"username": "user7", "password": "password7"},
    {"username": "user8", "password": "password8"},
    {"username": "user9", "password": "password9"},
    {"username": "user10", "password": "password10"},
    {"username": "user11", "password": "password11"},
    {"username": "user12", "password": "password12"},
    {"username": "user13", "password": "password13"},
    {"username": "user14", "password": "password14"},
    {"username": "user15", "password": "password15"},
    {"username": "user16", "password": "password16"},
    {"username": "user17", "password": "password17"},
    {"username": "user18", "password": "password18"},
    {"username": "user19", "password": "password19"},
    {"username": "user20", "password": "password20"},
    {"username": "user21", "password": "password21"},
    {"username": "user22", "password": "password22"},
    {"username": "user23", "password": "password23"},
    {"username": "user24", "password": "password24"},
    {"username": "user25", "password": "password25"},
    {"username": "user26", "password": "password26"},
    {"username": "user27", "password": "password27"},
    {"username": "user28", "password": "password28"},
    {"username": "user29", "password": "password29"},
    {"username": "user30", "password": "password30"},
    {"username": "user31", "password": "password31"},
    {"username": "user32", "password": "password32"},
    {"username": "user33", "password": "password33"},
    {"username": "user34", "password": "password34"},
    {"username": "user35", "password": "password35"},
    {"username": "user36", "password": "password36"},
    {"username": "user37", "password": "password37"},
    {"username": "user38", "password": "password38"},
    {"username": "user39", "password": "password39"},
    {"username": "user40", "password": "password40"},
    {"username": "user41", "password": "password41"},
    {"username": "user42", "password": "password42"},
    {"username": "user43", "password": "password43"},
    {"username": "user44", "password": "password44"},
    {"username": "user45", "password": "password45"},
    {"username": "user46", "password": "password46"},
    {"username": "user47", "password": "password47"},
    {"username": "user48", "password": "password48"},
    {"username": "user49", "password": "password49"},
    {"username": "aaaaa", "password": "aaaa"},
    {"username": "12", "password": "12"},
    {"username": "erf4rf", "password": None}
]


class APITestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("API Stress Test Tool by César Rodríguez")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Configure grid layout
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure((2, 3), weight=0)
        self.root.grid_rowconfigure((0, 1, 2), weight=1)
        
        # Create widgets
        self.create_widgets()
        
        # Start periodic updates
        self.update_logs()
        self.update_graph_periodically()
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Configuración del grid principal (ventana raíz)
        self.root.grid_columnconfigure(1, weight=2)  # Columna de logs (estrecha)
        self.root.grid_columnconfigure(2, weight=2)  # Columna de gráficos (3x más ancha)
        self.root.grid_rowconfigure(0, weight=1)     # Fila superior (endpoints + gráfico)
        self.root.grid_rowconfigure(1, weight=1)     # Fila inferior (logs)

        # --- Sidebar (izquierda) ---
        self.sidebar_frame = ctk.CTkFrame(self.root, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        # Logo
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="API Stress Test (Logins)", 
                                    font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Frame de parámetros
        self.params_frame = ctk.CTkFrame(self.sidebar_frame)
        self.params_frame.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="nsew")

        # Server URL (más ancho)
        self.server_url_label = ctk.CTkLabel(self.params_frame, text="Server URL:")
        self.server_url_label.grid(row=0, column=0, padx=5, pady=(5, 0), sticky="w")
        self.server_url_entry = ctk.CTkEntry(self.params_frame, 
                                        placeholder_text="http://192.168.1.52:5000",
                                        width=300)  # Ancho aumentado
        self.server_url_entry.insert(0, "http://192.168.1.52:5000")
        self.server_url_entry.grid(row=1, column=0, padx=5, pady=(0, 5), sticky="ew")

        # Botón "Discover Endpoints"
        self.discover_btn = ctk.CTkButton(self.params_frame, text="Discover Endpoints",
                                        command=self.discover_endpoints)
        self.discover_btn.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

        # Número de usuarios
        self.num_users_label = ctk.CTkLabel(self.params_frame, text="Number of Users:")
        self.num_users_label.grid(row=3, column=0, padx=5, pady=(5, 0), sticky="w")
        self.num_users_entry = ctk.CTkEntry(self.params_frame)
        self.num_users_entry.insert(0, "10")
        self.num_users_entry.grid(row=4, column=0, padx=5, pady=(0, 5), sticky="ew")

        # Rango de delay
        self.delay_label = ctk.CTkLabel(self.params_frame, text="Delay Range (s):")
        self.delay_label.grid(row=5, column=0, padx=5, pady=(5, 0), sticky="w")
        
        self.delay_frame = ctk.CTkFrame(self.params_frame, fg_color="transparent")
        self.delay_frame.grid(row=6, column=0, padx=0, pady=(0, 5), sticky="ew")
        self.delay_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.delay_min_entry = ctk.CTkEntry(self.delay_frame, width=60)
        self.delay_min_entry.insert(0, "0.1")
        self.delay_min_entry.grid(row=0, column=0, padx=(0, 5), sticky="w")
        
        self.delay_max_entry = ctk.CTkEntry(self.delay_frame, width=60)
        self.delay_max_entry.insert(0, "1.0")
        self.delay_max_entry.grid(row=0, column=1, padx=(5, 0), sticky="e")

        # Intervalo de logs
        self.log_interval_label = ctk.CTkLabel(self.params_frame, text="Log Interval (s):")
        self.log_interval_label.grid(row=7, column=0, padx=5, pady=(5, 0), sticky="w")
        self.log_interval_entry = ctk.CTkEntry(self.params_frame)
        self.log_interval_entry.insert(0, "10")
        self.log_interval_entry.grid(row=8, column=0, padx=5, pady=(0, 10), sticky="ew")

        # Botones de inicio/parada
        self.start_button = ctk.CTkButton(self.sidebar_frame, text="Start Test", 
                                        command=self.start_test)
        self.start_button.grid(row=2, column=0, padx=20, pady=5)
        
        self.stop_button = ctk.CTkButton(self.sidebar_frame, text="Stop Test", 
                                    command=self.stop_test, state="disabled")
        self.stop_button.grid(row=3, column=0, padx=20, pady=5)

        # --- Frame de endpoints (centro-izquierda) ---
        self.endpoints_frame = ctk.CTkFrame(self.root)
        self.endpoints_frame.grid(row=0, column=1, padx=(10, 5), pady=(10, 0), sticky="nsew")
        self.endpoints_frame.grid_columnconfigure(0, weight=1)
        self.endpoints_frame.grid_rowconfigure(1, weight=1)
        
        self.endpoints_label = ctk.CTkLabel(self.endpoints_frame, text="Select Endpoints to Test", 
                                        font=ctk.CTkFont(weight="bold"))
        self.endpoints_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Scrollable frame para checkboxes
        self.checkbox_scrollframe = ctk.CTkScrollableFrame(self.endpoints_frame)
        self.checkbox_scrollframe.grid(row=1, column=0, padx=5, pady=(0, 10), sticky="nsew")
        self.endpoint_checkboxes = []  # Lista para almacenar checkboxes

        # Botones "Select All/Deselect All"
        self.select_buttons_frame = ctk.CTkFrame(self.endpoints_frame, fg_color="transparent")
        self.select_buttons_frame.grid(row=2, column=0, padx=5, pady=(0, 10), sticky="ew")
        
        self.select_all_button = ctk.CTkButton(self.select_buttons_frame, text="Select All", 
                                            width=80, command=self.select_all_endpoints)
        self.select_all_button.grid(row=0, column=0, padx=(0, 5))
        
        self.deselect_all_button = ctk.CTkButton(self.select_buttons_frame, text="Deselect All", 
                                                width=80, command=self.deselect_all_endpoints)
        self.deselect_all_button.grid(row=0, column=1, padx=(5, 0))

        # --- Frame de logs (abajo-centro) ---
        self.log_frame = ctk.CTkFrame(self.root)
        self.log_frame.grid(row=1, column=1, padx=(10, 5), pady=(10, 0), sticky="nsew")
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(1, weight=1)
        
        self.log_label = ctk.CTkLabel(self.log_frame, text="Test Log", 
                                    font=ctk.CTkFont(weight="bold"))
        self.log_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.log_text = ctk.CTkTextbox(self.log_frame, wrap="word")
        self.log_text.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.log_text.configure(state="disabled")

        # --- Frame de gráficos (derecha) ---
        self.graph_frame = ctk.CTkFrame(self.root)
        self.graph_frame.grid(row=0, column=2, rowspan=2, padx=(5, 10), pady=(10, 0), sticky="nsew")
        self.graph_frame.grid_columnconfigure(0, weight=1)
        self.graph_frame.grid_rowconfigure(1, weight=1)
        
        self.graph_label = ctk.CTkLabel(self.graph_frame, text="Response Times", 
                                    font=ctk.CTkFont(weight="bold"))
        self.graph_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Gráfico matplotlib (más grande)
        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().grid(row=1, column=0, padx=5, pady=(0, 10), sticky="nsew")

        # --- Barra de estado (abajo) ---
        self.status_bar = ctk.CTkLabel(self.root, text="Ready", anchor="w", 
                                    font=ctk.CTkFont(size=10))
        self.status_bar.grid(row=3, column=1, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
    
    def discover_endpoints(self):
        """Discover API endpoints with automatic detection of FromForm and FromBody types"""
        base_url = self.server_url_entry.get().strip()
        if not base_url:
            messagebox.showwarning("Warning", "Please enter a valid Server URL")
            return

        self.log_message("\n🚀 Starting comprehensive endpoint discovery...")

        # Configuración completa de endpoints
        endpoints_config = {
            # FromForm endpoints (traditional form data)
            "FROM_FORM": {
                "/Auth/Login2": {
                    "data": {
                        "username": "adam",
                        "password": "1234"
                            },
                    },
                },
            }
        
        discovered_endpoints = []
        session = requests.Session()  # Reutilizamos la sesión HTTP

        # Función interna para probar endpoints
        def test_endpoint(endpoint_type, endpoint, config):
            nonlocal discovered_endpoints
            try:
                # Construcción de la URL
                url = urljoin(base_url, endpoint)
                
                # Manejo de parámetros query para endpoints FromForm
                if endpoint_type == "FROM_FORM" and "params" in config:
                    url += "?" + "&".join([f"{k}={v}" for k, v in config["params"].items()])

                self.log_message(f"\n🔍 Testing {endpoint_type} POST {endpoint}")
                self.log_message(f"URL: {url}")
                self.log_message(f"Data: {json.dumps(config['data'], indent=2)}")

                # Envío según el tipo
                if endpoint_type == "FROM_FORM":
                    response = session.post(
                        url,
                        data=config["data"],
                        headers={'Content-Type': 'application/x-www-form-urlencoded'},
                        timeout=10
                    )
                else:  # FROM_BODY
                    response = session.post(
                        url,
                        json=config["data"],
                        timeout=10
                    )

                # Registro detallado
                self.log_message(f"Status: {response.status_code}")
                self.log_message(f"Headers: {json.dumps(dict(response.headers), indent=2)}")
                
                try:
                    response_data = response.json()
                    self.log_message(f"Response: {json.dumps(response_data, indent=2)}")
                except:
                    self.log_message(f"Response: {response.text}")

                # Evaluación de respuesta
                if response.status_code < 400:
                    discovered_endpoints.append({
                        'endpoint': endpoint,
                        'type': 'form' if endpoint_type == "FROM_FORM" else 'json',
                        'config': config
                    })
                    self.log_message(f"✅ Success! Added {endpoint} as {endpoint_type}")
                    return True
                else:
                    self.log_message(f"⚠️ Failed with status {response.status_code}")
                    return False

            except requests.Timeout:
                self.log_message(f"⌛ Timeout testing {endpoint}")
                return False
            except Exception as e:
                self.log_message(f"❌ Error testing {endpoint}: {str(e)}")
                return False

        # Procesamiento de todos los endpoints
        for endpoint_type, endpoints in endpoints_config.items():
            self.log_message(f"\n===== Testing {endpoint_type} Endpoints =====")
            for endpoint, config in endpoints.items():
                # Intento principal
                if not test_endpoint(endpoint_type, endpoint, config):
                    # Intento alternativo si falla
                    alt_type = "FROM_BODY" if endpoint_type == "FROM_FORM" else "FROM_FORM"
                    self.log_message(f"🔄 Trying alternative {alt_type} approach...")
                    test_endpoint(alt_type, endpoint, config)

        # Resultados finales
        global available_endpoints
        available_endpoints = discovered_endpoints

        if available_endpoints:
            self.update_endpoint_checkboxes()
            self.log_message(f"\n🎉 {success_msg}")
            messagebox.showinfo("Success", success_msg)
        else:
            self.log_message("\n❌ No endpoints responded successfully")
            messagebox.showwarning("Warning", "No endpoints could be discovered")
    
    def update_endpoint_checkboxes(self):
        """Update the checkboxes with discovered endpoints"""
        # Clear existing checkboxes
        for widget in self.checkbox_scrollframe.winfo_children():
            widget.destroy()
        
        self.endpoint_checkboxes = []
        for i, endpoint in enumerate(available_endpoints):
            checkbox = ctk.CTkCheckBox(self.checkbox_scrollframe, text=endpoint)
            checkbox.grid(row=i, column=0, padx=5, pady=2, sticky="w")
            self.endpoint_checkboxes.append(checkbox)
    
    def select_all_endpoints(self):
        for checkbox in self.endpoint_checkboxes:
            checkbox.select()
    
    def deselect_all_endpoints(self):
        for checkbox in self.endpoint_checkboxes:
            checkbox.deselect()
    
    def get_selected_endpoints(self):
        selected = []
        for i, checkbox in enumerate(self.endpoint_checkboxes):
            if checkbox.get() == 1:
                selected.append(available_endpoints[i])
        return selected
    
    def log_message(self, message):
        log_queue.put(message)
    
    def update_logs(self):
        try:
            while True:
                message = log_queue.get_nowait()
                self.log_text.configure(state="normal")
                self.log_text.insert("end", message + "\n")
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except queue.Empty:
            pass
        self.root.after(100, self.update_logs)
    
    def send_request(self, session, endpoint_info):
        """Send a POST request with proper formatting based on endpoint type"""
        base_url = self.server_url_entry.get().strip() or "http://192.168.1.52:5000"
        endpoint = endpoint_info['endpoint']
        url = urljoin(base_url, endpoint)

        # Métricas
        start_time = time.time()
        status = "Error"
        elapsed = None

        global datos_usuarios

        try:
            # Preparar la petición según el tipo de endpoint
            if endpoint_info['type'] == 'form':
                if 'params' in endpoint_info['config']:
                    url += "?" + "&".join(
                        f"{k}={v}" for k, v in endpoint_info['config']['params'].items()
                    )
                data_to_send = endpoint_info['config']['data']
                headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            else:  # JSON endpoints
                # Modificación para endpoint de login con workplace random
                if endpoint == "/Auth/Login2":
                    # Añadir parámetro seed para que el backend elija un workplace aleatorio
                    seed = random.randint(1, 51)
                    url += f"?seed={seed}"

                    # Seleccionar usuario aleatorio con contraseña válida
                    valid_users = [u for u in datos_usuarios if u.get("password")]
                    if not valid_users:
                        self.log_message("❌ No hay credenciales válidas para probar")
                        return "Error", None

                    user = random.choice(valid_users)
                    data_to_send = {
                        "username": user["username"],
                        "password": user["password"]
                    }
                    headers = {'Content-Type': 'application/json'}
                else:
                    data_to_send = endpoint_info['config']['data']
                    headers = {'Content-Type': 'application/json'}

            # Envío de la petición
            if endpoint_info['type'] == 'form':
                response = session.post(
                    url,
                    data=data_to_send,
                    headers=headers,
                    timeout=10
                )
            else:
                response = session.post(
                    url,
                    json=data_to_send,
                    headers=headers,
                    timeout=10
                )

            elapsed = time.time() - start_time
            status = response.status_code

            # Registro de métricas
            global response_times, status_codes, errors
            response_times.append(elapsed)
            status_codes[status] = status_codes.get(status, 0) + 1

            # Log detallado
            log_msg = [
                f"Request to {endpoint}",
                f"Type: {endpoint_info['type'].upper()}",
                f"Status: {status}",
                f"Time: {elapsed:.3f}s"
            ]
            if endpoint == "/Auth/Login2":
                log_msg.append(f"Credentials used: {data_to_send['username']} | seed={seed}")

            try:
                response_data = response.json()
                log_msg.append(f"Response: {json.dumps(response_data, indent=2)}")
            except Exception:
                log_msg.append(f"Response: {response.text}")

            self.log_message("\n".join(log_msg))

            return status, elapsed

        except requests.Timeout:
            errors.append("Timeout")
            self.log_message(f"⌛ Timeout making request to {endpoint}")
            return "Timeout", None
        except Exception as e:
            errors.append(str(e))
            self.log_message(f"❌ Error making request to {endpoint}: {str(e)}")
            return "Error", None


    def user_simulation(self, user_id):
        """Simulate a user generating requests"""
        session = requests.Session()
        endpoints = self.get_selected_endpoints()
        if not endpoints:
            self.log_message("No endpoints selected for testing!")
            return
            
        while test_running:
            endpoint = random.choice(endpoints)
            self.send_request(session, endpoint)
            time.sleep(random.uniform(float(self.delay_min_entry.get()), float(self.delay_max_entry.get())))
 
    def start_test(self):
        global test_running, response_times, status_codes, errors
        
        # Reset metrics
        response_times = []
        status_codes = {}
        errors = []
        
        # Get selected endpoints
        endpoints_to_test = self.get_selected_endpoints()
        if not endpoints_to_test:
            messagebox.showwarning("Warning", "Please select at least one endpoint to test")
            return
        
        # Validate parameters
        try:
            num_users = int(self.num_users_entry.get())
            delay_min = float(self.delay_min_entry.get())
            delay_max = float(self.delay_max_entry.get())
            log_interval = int(self.log_interval_entry.get())
            
            if delay_min < 0 or delay_max < 0:
                raise ValueError("Delay values must be positive")
            if delay_min > delay_max:
                raise ValueError("Minimum delay must be less than maximum delay")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid parameter: {str(e)}")
            return
        
        # Update UI
        test_running = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.num_users_entry.configure(state="disabled")
        self.delay_min_entry.configure(state="disabled")
        self.delay_max_entry.configure(state="disabled")
        self.log_interval_entry.configure(state="disabled")
        self.server_url_entry.configure(state="disabled")
        self.discover_btn.configure(state="disabled")
        
        # Disable endpoint selection during test
        for checkbox in self.endpoint_checkboxes:
            checkbox.configure(state="disabled")
        
        self.select_all_button.configure(state="disabled")
        self.deselect_all_button.configure(state="disabled")
        
        self.log_message("\n=== Starting stress test ===")
        self.log_message(f"Users: {num_users} | Endpoints: {len(endpoints_to_test)}")
        self.log_message(f"Delay range: {delay_min}-{delay_max}s | Log interval: {log_interval}s")
        
        # Start user threads
        threads = []
        for user_id in range(num_users):
            thread = threading.Thread(target=self.user_simulation, args=(user_id,))
            threads.append(thread)
            thread.daemon = True
            thread.start()
        
        # Start log thread
        log_thread = threading.Thread(target=self.log_status, args=(log_interval,))
        log_thread.daemon = True
        log_thread.start()
        
        self.status_bar.configure(text="Test running...")
    
    def stop_test(self):
        global test_running
        
        test_running = False
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.num_users_entry.configure(state="normal")
        self.delay_min_entry.configure(state="normal")
        self.delay_max_entry.configure(state="normal")
        self.log_interval_entry.configure(state="normal")
        self.server_url_entry.configure(state="normal")
        self.discover_btn.configure(state="normal")
        
        # Re-enable endpoint selection
        for checkbox in self.endpoint_checkboxes:
            checkbox.configure(state="normal")
        
        self.select_all_button.configure(state="normal")
        self.deselect_all_button.configure(state="normal")
        
        self.log_message("\n=== Test stopped ===")
        self.status_bar.configure(text="Test stopped")
    
    def log_status(self, interval):
        while test_running:
            time.sleep(interval)
            
            if response_times:
                avg_time = statistics.mean(response_times)
                min_time = min(response_times)
                max_time = max(response_times)
                std_dev = statistics.stdev(response_times) if len(response_times) > 1 else 0
                
                status_message = (
                    f"\n=== Status Update ===\n"
                    f"Requests: {len(response_times)}\n"
                    f"Avg Time: {avg_time:.4f} s\n"
                    f"Min Time: {min_time:.4f} s\n"
                    f"Max Time: {max_time:.4f} s\n"
                    f"Std Dev: {std_dev:.4f} s\n"
                    f"Status Codes: {status_codes}\n"
                    f"Errors: {len(errors)}"
                )
                self.log_message(status_message)
    
    def update_graph(self):
        if response_times:
            self.ax.clear()
            self.ax.plot(range(len(response_times)), response_times, label="Response Times", color='#3a7ebf')
            self.ax.set_title("Response Times Over Time", pad=10)
            self.ax.set_xlabel("Request Count")
            self.ax.set_ylabel("Response Time (s)")
            self.ax.grid(True, linestyle='--', alpha=0.7)
            self.ax.legend(loc="upper right")
            self.canvas.draw()
    
    def update_graph_periodically(self):
        self.update_graph()
        self.root.after(1000, self.update_graph_periodically)
    
    def on_closing(self):
        global test_running
        test_running = False
        
        # 1. Detener todas las actualizaciones programadas
        self.root.after_cancel(self.update_job) if hasattr(self, 'update_job') else None
        self.root.after_cancel(self.log_job) if hasattr(self, 'log_job') else None
        
        # 2. Cerrar correctamente la figura de matplotlib
        plt.close('all')
        if hasattr(self, 'canvas'):
            self.canvas.get_tk_widget().destroy()
        
        # 3. Destruir la ventana principal
        self.root.destroy()
        
        # 4. Salir completamente (opcional pero recomendado)
        import os
        os._exit(0)

    def update_graph_periodically(self):
        self.update_job = self.root.after(1000, self.update_graph_periodically)
        self.update_graph()

    def update_logs(self):
        try:
            while True:
                message = log_queue.get_nowait()
                self.log_text.configure(state="normal")
                self.log_text.insert("end", message + "\n")
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except queue.Empty:
            pass
        self.log_job = self.root.after(100, self.update_logs)

if __name__ == "__main__":
    root = ctk.CTk()
    app = APITestApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()