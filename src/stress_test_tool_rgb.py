# Importaciones necesarias
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

# Configuracion de CustomTkinter
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Variables globales
response_times = []
status_codes = {}
errors = []
test_running = False
log_queue = queue.Queue()
endpoints_to_test = []
available_endpoints = []
ip = "http://192.168.1.52:5000"
# ip = "http://192.168.1.71:5000"

# Definición de la clase principal
class APITestApp:
    # Función de inicialización
    def __init__(self, root):
        # Constructor de la clase. Se ejecuta al crear una instancia.
        self.root = root  # Guarda la ventana principal (root) para usarla en otros métodos.
        self.root.title("API Stress Test Tool by César Rodríguez")  # Establece el título de la ventana.
        self.root.geometry("1200x800")  # Define el tamaño inicial de la ventana.
        self.root.minsize(1000, 700)    # Define el tamaño mínimo de la ventana.
        
        # Configura el layout de la ventana principal usando grid.
        self.root.grid_columnconfigure(1, weight=1)  # La columna 1 puede expandirse.
        self.root.grid_columnconfigure((2, 3), weight=0)  # Las columnas 2 y 3 no se expanden.
        self.root.grid_rowconfigure((0, 1, 2), weight=1)  # Las filas 0, 1 y 2 pueden expandirse.
        
        # Llama al método que crea todos los widgets de la interfaz gráfica.
        self.create_widgets()
        
        # Inicia la actualización periódica de logs y gráficos.
        self.update_logs()
        self.update_graph_periodically()

    def create_widgets(self):
        """Crea todos los widgets de la interfaz gráfica"""

        # Configura el grid principal de la ventana raíz para distribuir los paneles principales.
        self.root.grid_columnconfigure(1, weight=2)  # Columna central (logs) con mayor expansión.
        self.root.grid_columnconfigure(2, weight=2)  # Columna derecha (gráficos) con igual expansión.
        self.root.grid_rowconfigure(0, weight=1)     # Fila superior (endpoints + gráficos).
        self.root.grid_rowconfigure(1, weight=1)     # Fila inferior (logs).

        # --- Sidebar (izquierda) ---
        # Crea un frame lateral izquierdo para los controles y parámetros.
        self.sidebar_frame = ctk.CTkFrame(self.root, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")  # Ocupa varias filas.
        self.sidebar_frame.grid_rowconfigure(5, weight=1)  # Permite expansión en la fila 5.

        # Logo en la parte superior de la barra lateral.
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="API Stress Test (RGB)", 
                                    font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Frame para los parámetros de configuración en la barra lateral.
        self.params_frame = ctk.CTkFrame(self.sidebar_frame)
        self.params_frame.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="nsew")

        # Campo para introducir la URL del servidor.
        self.server_url_label = ctk.CTkLabel(self.params_frame, text="Server URL:")
        self.server_url_label.grid(row=0, column=0, padx=5, pady=(5, 0), sticky="w")
        self.server_url_entry = ctk.CTkEntry(self.params_frame, 
                                            placeholder_text=ip,
                                            width=300)  # Entrada de texto más ancha.
        self.server_url_entry.insert(0, ip)  # Inserta el valor por defecto.
        self.server_url_entry.grid(row=1, column=0, padx=5, pady=(0, 5), sticky="ew")

        # Botón para descubrir endpoints automáticamente.
        self.discover_btn = ctk.CTkButton(self.params_frame, text="Discover Endpoints",
                                        command=self.discover_endpoints)
        self.discover_btn.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

        # Campo para el número de usuarios concurrentes en la prueba.
        self.num_users_label = ctk.CTkLabel(self.params_frame, text="Number of Users:")
        self.num_users_label.grid(row=3, column=0, padx=5, pady=(5, 0), sticky="w")
        self.num_users_entry = ctk.CTkEntry(self.params_frame)
        self.num_users_entry.insert(0, "1")
        self.num_users_entry.grid(row=4, column=0, padx=5, pady=(0, 5), sticky="ew")

        # Campos para el rango de delay entre peticiones.
        self.delay_label = ctk.CTkLabel(self.params_frame, text="Delay Range (s):")
        self.delay_label.grid(row=5, column=0, padx=5, pady=(5, 0), sticky="w")
        self.delay_frame = ctk.CTkFrame(self.params_frame, fg_color="transparent")
        self.delay_frame.grid(row=6, column=0, padx=0, pady=(0, 5), sticky="ew")
        self.delay_frame.grid_columnconfigure((0, 1), weight=1)
        self.delay_min_entry = ctk.CTkEntry(self.delay_frame, width=60)
        self.delay_min_entry.insert(0, "1")
        self.delay_min_entry.grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.delay_max_entry = ctk.CTkEntry(self.delay_frame, width=60)
        self.delay_max_entry.insert(0, "1")
        self.delay_max_entry.grid(row=0, column=1, padx=(5, 0), sticky="e")

        # Campo para el intervalo de logs.
        self.log_interval_label = ctk.CTkLabel(self.params_frame, text="Log Interval (s):")
        self.log_interval_label.grid(row=7, column=0, padx=5, pady=(5, 0), sticky="w")
        self.log_interval_entry = ctk.CTkEntry(self.params_frame)
        self.log_interval_entry.insert(0, "10")
        self.log_interval_entry.grid(row=8, column=0, padx=5, pady=(0, 10), sticky="ew")

        # Botón para iniciar el test de estrés.
        self.start_button = ctk.CTkButton(self.sidebar_frame, text="Start Test", 
                                        command=self.start_test)
        self.start_button.grid(row=2, column=0, padx=20, pady=5)

        # Botón para detener el test (inicialmente deshabilitado).
        self.stop_button = ctk.CTkButton(self.sidebar_frame, text="Stop Test", 
                                        command=self.stop_test, state="disabled")
        self.stop_button.grid(row=3, column=0, padx=20, pady=5)

        # --- Frame de endpoints (centro-izquierda) ---
        # Panel para mostrar y seleccionar los endpoints a testear.
        self.endpoints_frame = ctk.CTkFrame(self.root)
        self.endpoints_frame.grid(row=0, column=1, padx=(10, 5), pady=(10, 0), sticky="nsew")
        self.endpoints_frame.grid_columnconfigure(0, weight=1)
        self.endpoints_frame.grid_rowconfigure(1, weight=1)
        self.endpoints_label = ctk.CTkLabel(self.endpoints_frame, text="Select Endpoints to Test", 
                                            font=ctk.CTkFont(weight="bold"))
        self.endpoints_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        # Frame desplazable para los checkboxes de endpoints.
        self.checkbox_scrollframe = ctk.CTkScrollableFrame(self.endpoints_frame)
        self.checkbox_scrollframe.grid(row=1, column=0, padx=5, pady=(0, 10), sticky="nsew")
        self.endpoint_checkboxes = []  # Lista para almacenar los checkboxes de endpoints.

        # Botones para seleccionar o deseleccionar todos los endpoints.
        self.select_buttons_frame = ctk.CTkFrame(self.endpoints_frame, fg_color="transparent")
        self.select_buttons_frame.grid(row=2, column=0, padx=5, pady=(0, 10), sticky="ew")
        self.select_all_button = ctk.CTkButton(self.select_buttons_frame, text="Select All", 
                                            width=80, command=self.select_all_endpoints)
        self.select_all_button.grid(row=0, column=0, padx=(0, 5))
        self.deselect_all_button = ctk.CTkButton(self.select_buttons_frame, text="Deselect All", 
                                                width=80, command=self.deselect_all_endpoints)
        self.deselect_all_button.grid(row=0, column=1, padx=(5, 0))

        # --- Frame de logs (abajo-centro) ---
        # Panel para mostrar los logs generados por la prueba.
        self.log_frame = ctk.CTkFrame(self.root)
        self.log_frame.grid(row=1, column=1, padx=(10, 5), pady=(10, 0), sticky="nsew")
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_label = ctk.CTkLabel(self.log_frame, text="Test Log", 
                                    font=ctk.CTkFont(weight="bold"))
        self.log_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.log_text = ctk.CTkTextbox(self.log_frame, wrap="word")
        self.log_text.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.log_text.configure(state="disabled")  # Solo lectura para los logs.

        # --- Frame de gráficos (derecha) ---
        # Panel para mostrar los gráficos de resultados.
        self.graph_frame = ctk.CTkFrame(self.root)
        self.graph_frame.grid(row=0, column=2, rowspan=2, padx=(5, 10), pady=(10, 0), sticky="nsew")
        self.graph_frame.grid_columnconfigure(0, weight=1)
        self.graph_frame.grid_rowconfigure(1, weight=1)
        self.graph_label = ctk.CTkLabel(self.graph_frame, text="Response Times", 
                                        font=ctk.CTkFont(weight="bold"))
        self.graph_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        # Crea el gráfico usando matplotlib y lo integra en la interfaz.
        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().grid(row=1, column=0, padx=5, pady=(0, 10), sticky="nsew")

        # --- Barra de estado (abajo) ---
        # Barra de estado en la parte inferior para mostrar mensajes de estado.
        self.status_bar = ctk.CTkLabel(self.root, text="Ready", anchor="w", 
                                    font=ctk.CTkFont(size=10))
        self.status_bar.grid(row=3, column=1, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
    
    def discover_endpoints(self):
        """Descubre endpoints de la API detectando automáticamente los tipos FromForm y FromBody"""

        # Obtiene y limpia la URL base introducida por el usuario.
        base_url = self.server_url_entry.get().strip()
        if not base_url:
            # Muestra una advertencia si la URL está vacía o no es válida.
            messagebox.showwarning("Warning", "Please enter a valid Server URL")
            return

        # Muestra en el log que comienza el descubrimiento de endpoints.
        self.log_message("\n🚀 Starting comprehensive endpoint discovery...")

        # Genera datos aleatorios para simular peticiones.
        random_ip = f"192.168.1.{random.randint(1, 255)}"
        random_channel = random.randint(1, 5)
        random_r = random.randint(0, 255)
        random_g = random.randint(0, 255)
        random_b = random.randint(0, 255)
        random_blink = random.choice([True, False])
        random_timing = random.randint(0, 10)

        # Diccionario de configuración de endpoints a probar.
        endpoints_config = {
            # Endpoints que reciben datos en el body como JSON (FromBody).
            "FROM_BODY": {
                "/ConsoleDevice/ChangeLightRGB": {
                    "params": {  # Parámetros en la URL (query string)
                        "ip": "192.168.1.210"  
                    },
                    "data": {    # Datos enviados en el body (JSON)
                        "channel": 1,
                        "r": 255,
                        "g": 255,
                        "b": 255,
                        "blink": True,
                        "timing": 0
                    }
                }
            }
        }
        
        discovered_endpoints = []  # Lista para endpoints descubiertos exitosamente.
        session = requests.Session()  # Reutiliza la sesión HTTP para eficiencia.

        # Función interna para probar un endpoint concreto.
        def test_endpoint(endpoint_type, endpoint, config):
            nonlocal discovered_endpoints  # Permite modificar la lista externa.
            try:
                # Construye la URL completa, añadiendo parámetros si existen.
                url = urljoin(base_url, endpoint)
                if "params" in config:
                    url += "?" + "&".join([f"{k}={v}" for k, v in config["params"].items()])

                # Muestra información de la prueba en el log.
                self.log_message(f"\n🔍 Testing {endpoint_type} POST {endpoint}")
                self.log_message(f"URL: {url}")
                self.log_message(f"Data: {json.dumps(config['data'], indent=2)}")

                # Envía la petición POST según el tipo de endpoint.
                if endpoint_type == "FROM_FORM":
                    # Si es tipo formulario (x-www-form-urlencoded)
                    response = session.post(
                        url,
                        data=config["data"],
                        headers={'Content-Type': 'application/x-www-form-urlencoded'},
                        timeout=10
                    )
                else:  # FROM_BODY
                    # Si es tipo JSON (application/json)
                    response = session.post(
                        url,
                        json=config["data"],
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )

                # Muestra el estado y las cabeceras de la respuesta en el log.
                self.log_message(f"Status: {response.status_code}")
                self.log_message(f"Headers: {json.dumps(dict(response.headers), indent=2)}")
                
                # Intenta mostrar la respuesta en formato JSON, si es posible.
                try:
                    response_data = response.json()
                    self.log_message(f"Response: {json.dumps(response_data, indent=2)}")
                except:
                    self.log_message(f"Response: {response.text}")

                # Si la respuesta es exitosa (<400), añade el endpoint a la lista de válidos.
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
                # Si la petición tarda demasiado, lo indica en el log.
                self.log_message(f"⌛ Timeout testing {endpoint}")
                return False
            except Exception as e:
                # Cualquier otro error se muestra en el log.
                self.log_message(f"❌ Error testing {endpoint}: {str(e)}")
                return False

        # Recorre todos los endpoints configurados y los prueba.
        for endpoint_type, endpoints in endpoints_config.items():
            self.log_message(f"\n===== Testing {endpoint_type} Endpoints =====")
            for endpoint, config in endpoints.items():
                # Intenta probar el endpoint con el tipo principal.
                if not test_endpoint(endpoint_type, endpoint, config):
                    # Si falla, prueba el tipo alternativo (FromForm <-> FromBody).
                    alt_type = "FROM_BODY" if endpoint_type == "FROM_FORM" else "FROM_FORM"
                    self.log_message(f"🔄 Trying alternative {alt_type} approach...")
                    test_endpoint(alt_type, endpoint, config)

        # Guarda los endpoints válidos globalmente.
        global available_endpoints
        available_endpoints = discovered_endpoints

        # Si se han encontrado endpoints válidos, actualiza la interfaz y muestra éxito.
        if available_endpoints:
            self.update_endpoint_checkboxes()
            self.log_message(f"\n🎉 Discovery completed! Found {len(available_endpoints)} valid endpoints")
            messagebox.showinfo("Success", f"Discovered {len(available_endpoints)} endpoints!")
        else:
            # Si no se encontró ninguno, muestra advertencia.
            self.log_message("\n❌ No endpoints responded successfully")
            messagebox.showwarning("Warning", "No endpoints could be discovered")

    def generate_dynamic_data(self, template):
        data = {}  # Diccionario donde se almacenarán los datos generados dinámicamente

        # Recorre cada clave y especificación en la plantilla recibida
        for key, spec in template.items():
            if isinstance(spec, str) and spec.startswith("int"):
                # Si la especificación es una cadena que comienza con "int"
                # Extrae el rango de valores (por ejemplo, de "int(0-255)")
                parts = spec[4:-1].split('-')
                # Genera un número entero aleatorio dentro del rango especificado
                data[key] = random.randint(int(parts[0]), int(parts[1]))
            elif spec == "bool":
                # Si la especificación es "bool", genera un valor booleano aleatorio
                data[key] = random.choice([True, False])
            else:
                # Si es cualquier otro valor (valor fijo), lo copia tal cual
                data[key] = spec

        return data  # Devuelve el diccionario con los datos generados

    def update_endpoint_checkboxes(self):
        """Actualiza los checkboxes con los endpoints descubiertos"""

        # Elimina todos los checkboxes existentes en el frame desplazable
        for widget in self.checkbox_scrollframe.winfo_children():
            widget.destroy()
        
        # Reinicia la lista de checkboxes
        self.endpoint_checkboxes = []

        # Crea un nuevo checkbox por cada endpoint disponible
        for i, endpoint in enumerate(available_endpoints):
            # Crea el checkbox con el texto del endpoint
            checkbox = ctk.CTkCheckBox(self.checkbox_scrollframe, text=endpoint)
            # Lo coloca en la posición correspondiente dentro del frame
            checkbox.grid(row=i, column=0, padx=5, pady=2, sticky="w")
            # Añade el checkbox a la lista para poder acceder a ellos después
            self.endpoint_checkboxes.append(checkbox)
    
    def select_all_endpoints(self):
        # Recorre todos los checkboxes de endpoints disponibles
        for checkbox in self.endpoint_checkboxes:
            # Marca (selecciona) cada checkbox
            checkbox.select()
    
    def deselect_all_endpoints(self):
        # Recorre todos los checkboxes de endpoints disponibles
        for checkbox in self.endpoint_checkboxes:
            # Desmarca (deselecciona) cada checkbox
            checkbox.deselect()
    
    def get_selected_endpoints(self):
        selected = []  # Lista para almacenar los endpoints seleccionados

        # Recorre todos los checkboxes y su índice correspondiente
        for i, checkbox in enumerate(self.endpoint_checkboxes):
            # Si el checkbox está marcado (valor 1)
            if checkbox.get() == 1:
                # Añade el endpoint correspondiente a la lista de seleccionados
                selected.append(available_endpoints[i])
        return selected  # Devuelve la lista de endpoints seleccionados
    
    def log_message(self, message):
        # Envía el mensaje recibido a la cola de logs para que sea procesado y mostrado en la interfaz.
        log_queue.put(message)
        
    def update_logs(self):
        try:
            while True:
                # Intenta obtener un mensaje de la cola de logs sin esperar (no bloqueante)
                message = log_queue.get_nowait()
                # Permite editar el área de texto de logs
                self.log_text.configure(state="normal")
                # Inserta el mensaje al final del área de texto de logs
                self.log_text.insert("end", message + "\n")
                # Desplaza la vista al final para mostrar el último mensaje
                self.log_text.see("end")
                # Vuelve a poner el área de texto en solo lectura
                self.log_text.configure(state="disabled")
        except queue.Empty:
            # Si la cola está vacía, simplemente pasa (no hace nada)
            pass
        # Programa la siguiente actualización de logs dentro de 100 ms (actualización periódica)
        self.root.after(100, self.update_logs)

    def send_request(self, session, endpoint_info):
        """Envía una petición POST al endpoint de la luz RGB"""

        # Obtiene la URL base del servidor desde la interfaz o usa un valor por defecto (ip)
        base_url = self.server_url_entry.get().strip() or ip
        endpoint = endpoint_info['endpoint']
        url = urljoin(base_url, endpoint)  # Construye la URL completa del endpoint

        # Si hay parámetros en la configuración, los añade a la URL como query string
        if 'params' in endpoint_info['config']:
            url += "?" + "&".join(
                f"{k}={v}" for k, v in endpoint_info['config']['params'].items()
            )

        # Inicializa variables para métricas y estado de la petición
        start_time = time.time()  # Marca el inicio para calcular el tiempo de respuesta
        status = "Error"
        elapsed = None

        try:
            # Genera una IP aleatoria y datos dinámicos para la petición
            random_ip = f"192.168.1.{random.randint(1, 254)}"
            data_to_send = self.generate_dynamic_data(endpoint_info['config']['data'])
            
            # Reconstruye la URL añadiendo el parámetro IP dinámico
            url = urljoin(base_url, endpoint)
            url += f"?ip={random_ip}"

            headers = {'Content-Type': 'application/json'}  # Cabecera indicando tipo de contenido JSON

            # Envía la petición POST usando la sesión proporcionada
            response = session.post(
                url,
                json=data_to_send,
                headers=headers,
                timeout=10
            )

            # Calcula el tiempo que tardó la petición y obtiene el código de estado
            elapsed = time.time() - start_time
            status = response.status_code

            # Registra métricas globales de respuesta y errores
            global response_times, status_codes, errors
            response_times.append(elapsed)
            status_codes[status] = status_codes.get(status, 0) + 1

            # Prepara el mensaje de log con los detalles de la petición y la respuesta
            log_msg = [
                f"🔦 RGB Light Request to {endpoint}",
                f"URL: {url}",
                f"Color Data:",
                f"• Channel: {data_to_send.get('channel', 'N/A')}",
                f"• R: {data_to_send.get('r', 'N/A')}",
                f"• G: {data_to_send.get('g', 'N/A')}",
                f"• B: {data_to_send.get('b', 'N/A')}",
                f"• Blink: {data_to_send.get('blink', 'N/A')}",
                f"• Timing: {data_to_send.get('timing', 'N/A')}",
                # ... resto del log
            ]

            # Intenta obtener la respuesta en formato JSON, si es posible
            try:
                response_data = response.json()
                log_msg.append(f"Response: {json.dumps(response_data, indent=2)}")
            except:
                log_msg.append(f"Response: {response.text}")

            # Envía el mensaje de log a la cola de logs
            self.log_message("\n".join(log_msg))

            return status, elapsed  # Devuelve el estado y el tiempo de respuesta

        except requests.Timeout:
            # Si hay un timeout, lo registra como error y lo muestra en el log
            errors.append("Timeout")
            self.log_message(f"⌛ Timeout making request to {endpoint}")
            return "Timeout", None
        except Exception as e:
            # Cualquier otro error se registra y se muestra en el log
            errors.append(str(e))
            self.log_message(f"❌ Error making request to {endpoint}: {str(e)}")
            return "Error", None

    def user_simulation(self, user_id):
        """Simula el comportamiento de un usuario generando solicitudes a la API"""
        
        # Crea una sesión HTTP para reutilizar conexiones (mejora eficiencia)
        session = requests.Session()
        
        # Obtiene los endpoints seleccionados por el usuario en la interfaz
        endpoints = self.get_selected_endpoints()
        
        # Si no hay endpoints seleccionados, muestra advertencia y termina la simulación
        if not endpoints:
            self.log_message("No endpoints selected for testing!")
            return
                
        # Bucle principal de simulación: se ejecuta mientras el test esté activo
        while test_running:
            # Selecciona un endpoint aleatorio de la lista de seleccionados
            endpoint = random.choice(endpoints)
            
            # Envía la petición al endpoint seleccionado
            self.send_request(session, endpoint)
            
            # Espera un tiempo aleatorio entre el rango mínimo y máximo configurado
            delay_min = float(self.delay_min_entry.get())
            delay_max = float(self.delay_max_entry.get())
            time.sleep(random.uniform(delay_min, delay_max))
 
    def start_test(self):
        # Accede a las variables globales para control del test y métricas
        global test_running, response_times, status_codes, errors
        
        # Reinicia las métricas para cada nuevo test
        response_times = []       # Lista de tiempos de respuesta
        status_codes = {}         # Diccionario para códigos de estado HTTP
        errors = []               # Lista de errores durante el test
        
        # Verifica que haya endpoints seleccionados
        endpoints_to_test = self.get_selected_endpoints()
        if not endpoints_to_test:
            messagebox.showwarning("Warning", "Selecciona al menos un endpoint para probar")
            return
        
        # Valida los parámetros de entrada
        try:
            num_users = int(self.num_users_entry.get())          # Número de usuarios concurrentes
            delay_min = float(self.delay_min_entry.get())        # Delay mínimo entre peticiones
            delay_max = float(self.delay_max_entry.get())        # Delay máximo entre peticiones
            log_interval = int(self.log_interval_entry.get())    # Intervalo de actualización de logs
            
            # Validaciones adicionales
            if delay_min < 0 or delay_max < 0:
                raise ValueError("Los delays deben ser valores positivos")
            if delay_min > delay_max:
                raise ValueError("El delay mínimo debe ser menor al máximo")
        except ValueError as e:
            messagebox.showerror("Error", f"Parámetro inválido: {str(e)}")
            return

        # --- Actualización de la interfaz durante el test ---
        test_running = True  # Activa el flag de test en curso
        # Deshabilita botones/entradas para prevenir cambios durante el test
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")  # Habilita el botón de parar
        self.num_users_entry.configure(state="disabled")
        self.delay_min_entry.configure(state="disabled")
        self.delay_max_entry.configure(state="disabled")
        self.log_interval_entry.configure(state="disabled")
        self.server_url_entry.configure(state="disabled")
        self.discover_btn.configure(state="disabled")
        
        # Deshabilita la selección de endpoints durante el test
        for checkbox in self.endpoint_checkboxes:
            checkbox.configure(state="disabled")
        self.select_all_button.configure(state="disabled")
        self.deselect_all_button.configure(state="disabled")
        
        # Registra el inicio del test en los logs
        self.log_message("\n=== Iniciando prueba de estrés ===")
        self.log_message(f"Usuarios: {num_users} | Endpoints: {len(endpoints_to_test)}")
        self.log_message(f"Rango de delay: {delay_min}-{delay_max}s | Intervalo de logs: {log_interval}s")
        
        # --- Inicio de hilos para simulación ---
        threads = []
        # Crea un hilo por usuario para simular concurrencia
        for user_id in range(num_users):
            thread = threading.Thread(target=self.user_simulation, args=(user_id,))
            threads.append(thread)
            thread.daemon = True  # Hilos en segundo plano (se cierran al terminar el programa)
            thread.start()
        
        # Hilo separado para actualizar logs/estadísticas periódicamente
        log_thread = threading.Thread(target=self.log_status, args=(log_interval,))
        log_thread.daemon = True
        log_thread.start()
        
        # Actualiza la barra de estado
        self.status_bar.configure(text="Test en curso...")
    
    def stop_test(self):
        global test_running  # Accede a la variable global que controla el estado del test

        # Detiene el test cambiando el flag global
        test_running = False

        # --- Restaura el estado de los controles de la interfaz ---
        # Habilita el botón de inicio y deshabilita el de detener
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        
        # Reactiva los campos de entrada de parámetros
        self.num_users_entry.configure(state="normal")       # Número de usuarios
        self.delay_min_entry.configure(state="normal")       # Delay mínimo
        self.delay_max_entry.configure(state="normal")       # Delay máximo
        self.log_interval_entry.configure(state="normal")    # Intervalo de logs
        self.server_url_entry.configure(state="normal")      # URL del servidor
        self.discover_btn.configure(state="normal")          # Botón de descubrir endpoints

        # --- Reactiva la selección de endpoints ---
        # Habilita todos los checkboxes de endpoints
        for checkbox in self.endpoint_checkboxes:
            checkbox.configure(state="normal")
        
        # Reactiva los botones de selección masiva
        self.select_all_button.configure(state="normal")     # Seleccionar todos
        self.deselect_all_button.configure(state="normal")   # Deseleccionar todos

        # --- Registro y feedback visual ---
        self.log_message("\n=== Test detenido ===")          # Mensaje en el log
        self.status_bar.configure(text="Test detenido")      # Actualiza barra de estado
    
    def log_status(self, interval):
        """Registra periódicamente el estado del test de estrés"""
        while test_running:  # Se ejecuta mientras el test esté activo
            time.sleep(interval)  # Espera el intervalo especificado (en segundos)
            
            # Solo genera el reporte si hay respuestas registradas
            if response_times:
                # Cálculo de métricas estadísticas
                avg_time = statistics.mean(response_times)  # Tiempo promedio de respuesta
                min_time = min(response_times)  # Tiempo más rápido registrado
                max_time = max(response_times)  # Tiempo más lento registrado
                # Desviación estándar (solo si hay más de 1 dato)
                std_dev = statistics.stdev(response_times) if len(response_times) > 1 else 0
                
                # Construye el mensaje de estado con formato
                status_message = (
                    f"\n=== Actualización de Estado ===\n"
                    f"Peticiones: {len(response_times)}\n"
                    f"Tiempo promedio: {avg_time:.4f} s\n"
                    f"Tiempo mínimo: {min_time:.4f} s\n"
                    f"Tiempo máximo: {max_time:.4f} s\n"
                    f"Desviación estándar: {std_dev:.4f} s\n"
                    f"Códigos de estado: {status_codes}\n"  # Distribución de códigos HTTP
                    f"Errores: {len(errors)}"  # Cantidad total de errores
                )
                self.log_message(status_message)  # Envía el reporte al área de logs
    
    def update_graph(self):
        # Si hay tiempos de respuesta registrados, actualiza el gráfico
        if response_times:
            self.ax.clear()  # Limpia el gráfico anterior
            
            # Dibuja la nueva gráfica de tiempos de respuesta
            self.ax.plot(
                range(len(response_times)),     # Eje X: número de petición
                response_times,                 # Eje Y: tiempo de respuesta de cada petición
                label="Response Times",         # Etiqueta de la línea
                color='#3a7ebf'                 # Color de la línea
            )
            
            # Configura el título y las etiquetas de los ejes
            self.ax.set_title("Response Times Over Time", pad=10)  # Título del gráfico
            self.ax.set_xlabel("Request Count")                     # Etiqueta eje X
            self.ax.set_ylabel("Response Time (s)")                 # Etiqueta eje Y
            
            # Añade una cuadrícula para facilitar la lectura
            self.ax.grid(True, linestyle='--', alpha=0.7)
            
            # Muestra la leyenda en la esquina superior derecha
            self.ax.legend(loc="upper right")
            
            # Redibuja el gráfico actualizado en la interfaz
            self.canvas.draw()
    
    def update_graph_periodically(self):
        # Actualiza el gráfico con los últimos datos disponibles
        self.update_graph()
        
        # Programa la próxima actualización del gráfico después de 1000 ms (1 segundo)
        self.root.after(1000, self.update_graph_periodically)
    
    def on_closing(self):
        global test_running  # Accede a la variable global de control del test
        
        # 1. Detener cualquier test en ejecución
        test_running = False
        
        # 2. Cancelar todas las actualizaciones programadas de la interfaz
        # (Evita que se ejecuten tareas pendientes tras cerrar)
        if hasattr(self, 'update_job'):
            self.root.after_cancel(self.update_job)  # Detiene actualización de gráficos
        if hasattr(self, 'log_job'):
            self.root.after_cancel(self.log_job)  # Detiene actualización de logs
        
        # 3. Liberar recursos de matplotlib
        plt.close('all')  # Cierra todas las figuras para evitar memory leaks
        if hasattr(self, 'canvas'):
            self.canvas.get_tk_widget().destroy()  # Destruye el widget del gráfico
        
        # 4. Cerrar la ventana principal de Tkinter
        self.root.destroy()  # Elimina todos los widgets y cierra la aplicación
        
        # 5. Terminación forzosa para asegurar cierre completo (especialmente en hilos)
        import os
        os._exit(0)  # Finaliza el proceso inmediatamente

    def update_graph_periodically(self):
        # Programa la próxima ejecución de esta función después de 1000 ms (1 segundo)
        # y guarda la referencia del trabajo programado para poder cancelarlo luego
        self.update_job = self.root.after(1000, self.update_graph_periodically)
        
        # Actualiza el gráfico con los datos más recientes
        self.update_graph()

    def update_logs(self):
        try:
            while True:
                # Intenta obtener un mensaje de la cola de logs sin bloquear el hilo
                message = log_queue.get_nowait()
                # Permite editar el área de texto de logs
                self.log_text.configure(state="normal")
                # Inserta el mensaje al final del área de texto
                self.log_text.insert("end", message + "\n")
                # Desplaza la vista al final para mostrar el último mensaje
                self.log_text.see("end")
                # Vuelve a poner el área de texto en modo solo lectura
                self.log_text.configure(state="disabled")
        except queue.Empty:
            # Si la cola está vacía, no hace nada y continúa
            pass

        # Programa la próxima actualización de logs dentro de 100 ms (0.1 segundos)
        # Guarda el identificador de la tarea programada para poder cancelarla si es necesario
        self.log_job = self.root.after(100, self.update_logs)

if __name__ == "__main__":
    # Crea la ventana principal de la aplicación usando CustomTkinter
    root = ctk.CTk()
    
    # Instancia la clase principal de la aplicación, pasando la ventana raíz
    app = APITestApp(root)
    
    # Asocia el evento de cierre de la ventana a la función personalizada 'on_closing'
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Inicia el bucle principal de la interfaz gráfica (la aplicación queda a la espera de eventos)
    root.mainloop()
