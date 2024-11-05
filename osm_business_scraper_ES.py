import sys
import subprocess

# Verificar los módulos requeridos e instalar si faltan
modulos_requeridos = ['requests', 'tkinter', 'openpyxl', 'tkintermapview']
for modulo in modulos_requeridos:
    try:
        __import__(modulo)
    except ImportError:
        print(f"El módulo '{modulo}' no está instalado. Instalando ahora...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", modulo])

import requests
import tkinter as tk
from tkinter import messagebox, ttk
from openpyxl import Workbook
from openpyxl.styles import Font
from collections import defaultdict
import tkintermapview
import webbrowser

def buscar_empresas():
    try:
        latitud = float(entrada_latitud.get())
        longitud = float(entrada_longitud.get())
        radio = float(entrada_radio.get())  # Radio en kilómetros
    except ValueError:
        messagebox.showerror("Error de entrada", "Por favor, ingrese valores numéricos válidos.")
        return

    # Recopilar las categorías seleccionadas
    categorias_seleccionadas = []
    for (tag, value), var in variables_categorias.items():
        if var.get():
            categorias_seleccionadas.append((tag, value))

    if not categorias_seleccionadas:
        messagebox.showerror("Error de selección", "Por favor, seleccione al menos una categoría.")
        return

    # Construir la consulta Overpass API basada en las categorías seleccionadas
    url_overpass = "http://overpass-api.de/api/interpreter"

    # Agrupar las categorías seleccionadas por etiqueta
    valores_tags = defaultdict(list)
    for tag, values in categorias_seleccionadas:
        valores_tags[tag].append(values)

    # Construir las partes de la consulta
    partes_consulta = []
    for tag, values in valores_tags.items():
        if None in values:
            # Para etiquetas sin valores específicos (por ejemplo, 'shop', 'office')
            partes_consulta.append(f'  node(around:{radio * 1000},{latitud},{longitud})["name"]["{tag}"];')
            partes_consulta.append(f'  way(around:{radio * 1000},{latitud},{longitud})["name"]["{tag}"];')
        else:
            # Para etiquetas con valores específicos
            regex = '|'.join(values)
            partes_consulta.append(f'  node(around:{radio * 1000},{latitud},{longitud})["name"]["{tag}"~"{regex}"];')
            partes_consulta.append(f'  way(around:{radio * 1000},{latitud},{longitud})["name"]["{tag}"~"{regex}"];')

    consulta_overpass = f"""
    [out:json];
    (
    {'\n'.join(partes_consulta)}
    );
    out center;
    """

    response = requests.get(url_overpass, params={'data': consulta_overpass})
    data = response.json()

    global todos_los_resultados  # Hacer todos_los_resultados global para acceder en otras funciones
    todos_los_resultados = []
    contador_procesado = 0

    for element in data.get('elements', []):
        tags = element.get('tags', {})
        nombre = tags.get('name')
        direccion = construir_direccion(tags)
        telefono = tags.get('phone', None)  # Obtener el número de teléfono, None si no está presente

        # Verificar si la casilla "Excluir entradas sin número de teléfono" está seleccionada
        excluir_sin_telefono = var_excluir_sin_telefono.get()

        # Determinar si incluir esta entrada
        incluir_entrada = True
        if excluir_sin_telefono and not telefono:
            incluir_entrada = False

        if nombre and incluir_entrada:
            todos_los_resultados.append({
                'Nombre': nombre,
                'Dirección': direccion,
                'Teléfono': telefono if telefono else 'N/A'
            })
            contador_procesado += 1
            etiqueta_contador.config(text=f"Número de empresas: {contador_procesado}")
            root.update_idletasks()

    if todos_los_resultados:
        messagebox.showinfo("Datos obtenidos", f"Datos obtenidos con éxito. Total de empresas: {contador_procesado}")
    else:
        messagebox.showinfo("Sin datos", "No se encontraron empresas con los criterios especificados.")

def eliminar_duplicados():
    global todos_los_resultados
    if not todos_los_resultados:
        messagebox.showinfo("Sin datos", "No hay datos para procesar. Por favor, busque empresas primero.")
        return

    resultados_unicos = []
    nombres_vistos = set()

    for entrada in todos_los_resultados:
        nombre = entrada['Nombre']
        if nombre not in nombres_vistos:
            nombres_vistos.add(nombre)
            resultados_unicos.append(entrada)

    duplicados_eliminados = len(todos_los_resultados) - len(resultados_unicos)
    todos_los_resultados = resultados_unicos  # Actualizar todos_los_resultados con entradas únicas

    etiqueta_contador.config(text=f"Número de empresas: {len(todos_los_resultados)}")
    root.update_idletasks()
    messagebox.showinfo("Duplicados eliminados", f"{duplicados_eliminados} entradas duplicadas eliminadas.")

def guardar_datos():
    if not todos_los_resultados:
        messagebox.showinfo("Sin datos", "No hay datos para guardar. Por favor, busque empresas primero.")
        return

    guardar_en_excel(todos_los_resultados)
    messagebox.showinfo("Éxito", f"Datos guardados en 'empresas.xlsx'. Total de empresas: {len(todos_los_resultados)}")

def construir_direccion(tags):
    # Construir la dirección a partir de las etiquetas disponibles
    partes_direccion = []
    for key in ['addr:housenumber', 'addr:street', 'addr:city', 'addr:postcode', 'addr:country']:
        if tags.get(key):
            partes_direccion.append(tags[key])
    return ', '.join(partes_direccion) if partes_direccion else 'N/A'

def guardar_en_excel(data):
    wb = Workbook()
    ws = wb.active
    ws.title = "Empresas"

    # Definir los encabezados
    encabezados = ['Nombre', 'Dirección', 'Teléfono']
    ws.append(encabezados)

    # Aplicar negrita a los encabezados
    for cell in ws[1]:
        cell.font = Font(bold=True)

    # Agregar datos a la hoja
    for entrada in data:
        ws.append([entrada['Nombre'], entrada['Dirección'], entrada['Teléfono']])

    # Ajustar el ancho de las columnas
    for column_cells in ws.columns:
        length = max(len(str(cell.value)) for cell in column_cells if cell.value)
        ws.column_dimensions[column_cells[0].column_letter].width = length + 2

    # Guardar el libro
    wb.save('empresas.xlsx')

# Nuevas funciones para "Seleccionar todo" y "Deseleccionar todo"
def seleccionar_todo():
    for var in variables_categorias.values():
        var.set(True)

def deseleccionar_todo():
    for var in variables_categorias.values():
        var.set(False)

# Función para abrir el mapa y seleccionar ubicación
def abrir_mapa():
    ventana_mapa = tk.Toplevel(root)
    ventana_mapa.title("Seleccionar ubicación")
    ventana_mapa.geometry("600x400")

    # Crear el widget de mapa
    widget_mapa = tkintermapview.TkinterMapView(ventana_mapa, width=600, height=400, corner_radius=0)
    widget_mapa.pack(fill="both", expand=True)

    # Centrar el mapa en la ubicación actual si está disponible
    try:
        lat_actual = float(entrada_latitud.get())
        lon_actual = float(entrada_longitud.get())
        widget_mapa.set_position(lat_actual, lon_actual)
        widget_mapa.set_zoom(15)
    except ValueError:
        # Ubicación por defecto (0,0) si las entradas son inválidas
        widget_mapa.set_position(0, 0)
        widget_mapa.set_zoom(2)

    # Función para manejar clics en el mapa
    def on_left_click_event(coordinates_tuple):
        lat, lon = coordinates_tuple
        # Actualizar las entradas
        entrada_latitud.delete(0, tk.END)
        entrada_latitud.insert(0, str(lat))
        entrada_longitud.delete(0, tk.END)
        entrada_longitud.insert(0, str(lon))
        # Colocar un marcador
        widget_mapa.set_marker(lat, lon, text="Ubicación seleccionada")
        # Cerrar la ventana del mapa
        ventana_mapa.destroy()

    widget_mapa.add_left_click_map_command(on_left_click_event)

# Función para abrir el sitio web
def abrir_sitio_web(event):
    webbrowser.open_new("https://clement.business/")

# Función para abrir el repositorio de GitHub
def abrir_github():
    webbrowser.open_new("https://github.com/Eykthirnyr/OSM-Business-Scraper")

# Inicializar variable global
todos_los_resultados = []

# Configuración de la interfaz gráfica
root = tk.Tk()
root.title("Scraper de Empresas de OpenStreetMap")
root.geometry("850x900")
root.resizable(False, False)

# Configuración del estilo
style = ttk.Style(root)
style.configure('TLabel', font=('Arial', 10))
style.configure('TButton', font=('Arial', 10))
style.configure('TCheckbutton', font=('Arial', 10))

# Título y descripción
etiqueta_titulo = ttk.Label(root, text="Scraper de Empresas de OpenStreetMap", font=("Arial", 16, "bold"))
etiqueta_titulo.pack(pady=(10, 5))

etiqueta_descripcion = ttk.Label(root, text="Busque empresas desde OpenStreetMap según ubicación y categorías.")
etiqueta_descripcion.pack(pady=(0, 10))

# Marco para las entradas de latitud, longitud y radio
marco_entradas = ttk.Frame(root)
marco_entradas.pack(pady=5)

# Entradas para la latitud y la longitud
ttk.Label(marco_entradas, text="Latitud:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
entrada_latitud = ttk.Entry(marco_entradas)
entrada_latitud.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(marco_entradas, text="Longitud:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
entrada_longitud = ttk.Entry(marco_entradas)
entrada_longitud.grid(row=1, column=1, padx=5, pady=5)

# Entrada para el radio
ttk.Label(marco_entradas, text="Radio (km):").grid(row=2, column=0, sticky='e', padx=5, pady=5)
entrada_radio = ttk.Entry(marco_entradas)
entrada_radio.grid(row=2, column=1, padx=5, pady=5)

# Botón para abrir el mapa
boton_seleccionar_ubicacion = ttk.Button(marco_entradas, text="Seleccionar ubicación en el mapa", command=abrir_mapa)
boton_seleccionar_ubicacion.grid(row=0, column=2, rowspan=3, padx=5, pady=5)

# Categorías para la selección
categorias = [
    ('Tienda', 'shop', None),
    ('Oficina', 'office', None),
    ('Restaurante', 'amenity', 'restaurant'),
    ('Cafetería', 'amenity', 'cafe'),
    ('Bar', 'amenity', 'bar'),
    ('Pub', 'amenity', 'pub'),
    ('Comida rápida', 'amenity', 'fast_food'),
    ('Banco', 'amenity', 'bank'),
    ('Farmacia', 'amenity', 'pharmacy'),
    ('Hospital', 'amenity', 'hospital'),
    ('Clínica', 'amenity', 'clinic'),
    ('Dentista', 'amenity', 'dentist'),
    ('Médicos', 'amenity', 'doctors'),
    ('Teatro', 'amenity', 'theatre'),
    ('Cine', 'amenity', 'cinema'),
    ('Discoteca', 'amenity', 'nightclub'),
    ('Jardín de infancia', 'amenity', 'kindergarten'),
    ('Biblioteca', 'amenity', 'library'),
    ('Colegio', 'amenity', 'college'),
    ('Universidad', 'amenity', 'university'),
    # Etiquetas adicionales
    ('Estacionamiento', 'amenity', 'parking'),
    ('Gasolinera', 'amenity', 'fuel'),
    ('Hotel', 'tourism', 'hotel'),
    ('Motel', 'tourism', 'motel'),
    ('Casa de huéspedes', 'tourism', 'guest_house'),
    ('Supermercado', 'shop', 'supermarket'),
    ('Tienda de conveniencia', 'shop', 'convenience'),
    ('Panadería', 'shop', 'bakery'),
    ('Carnicería', 'shop', 'butcher'),
    ('Tienda de ropa', 'shop', 'clothes'),
    ('Tienda de electrónica', 'shop', 'electronics'),
    ('Tienda de muebles', 'shop', 'furniture'),
    ('Joyería', 'shop', 'jewelry'),
    ('Tienda de deportes', 'shop', 'sports'),
    ('Peluquería', 'shop', 'hairdresser'),
    ('Salón de belleza', 'shop', 'beauty'),
    ('Museo', 'tourism', 'museum'),
    ('Parque', 'leisure', 'park'),
    ('Cajero automático', 'amenity', 'atm'),
    ('Oficina de correos', 'amenity', 'post_office'),
    ('Comisaría', 'amenity', 'police'),
    ('Estación de bomberos', 'amenity', 'fire_station'),
    ('Embajada', 'amenity', 'embassy'),
    ('Tribunal', 'amenity', 'courthouse'),
    ('Lugar de culto', 'amenity', 'place_of_worship'),
    ('Clínica veterinaria', 'amenity', 'veterinary'),
    ('Piscina', 'leisure', 'swimming_pool'),
    ('Gimnasio', 'leisure', 'fitness_centre'),
    ('Parque infantil', 'leisure', 'playground'),
    ('Estación de autobuses', 'amenity', 'bus_station'),
    ('Estación de tren', 'railway', 'station'),
    ('Aeropuerto', 'aeroway', 'aerodrome'),
    ('Parada de taxis', 'amenity', 'taxi'),
    ('Alquiler de coches', 'amenity', 'car_rental'),
    ('Lavado de coches', 'amenity', 'car_wash'),
    ('Estación de carga', 'amenity', 'charging_station'),
    ('Escuela', 'amenity', 'school'),
    ('Casino', 'amenity', 'casino'),
    ('Obra de arte', 'tourism', 'artwork'),
    ('Información', 'tourism', 'information'),
    ('Mirador', 'tourism', 'viewpoint'),
    ('Zoo', 'tourism', 'zoo'),
    ('Parque de atracciones', 'tourism', 'theme_park'),
    ('Parque acuático', 'leisure', 'water_park'),
]

# Marco para las casillas de verificación
marco_casillas = ttk.LabelFrame(root, text="Categorías a incluir")
marco_casillas.pack(pady=10, padx=10, fill="both", expand=True)

variables_categorias = {}
columnas = 5
for idx, (nombre_mostrar, tag, value) in enumerate(categorias):
    var = tk.BooleanVar(value=True)  # seleccionado por defecto
    variables_categorias[(tag, value)] = var
    row = idx // columnas
    col = idx % columnas
    casilla = ttk.Checkbutton(marco_casillas, text=nombre_mostrar, variable=var)
    casilla.grid(row=row, column=col, sticky='w', padx=5, pady=2)

# Marco para los botones "Seleccionar todo" y "Deseleccionar todo"
marco_botones = ttk.Frame(root)
marco_botones.pack(pady=5)

boton_seleccionar_todo = ttk.Button(marco_botones, text="Seleccionar todo", command=seleccionar_todo)
boton_seleccionar_todo.pack(side='left', padx=20)

boton_deseleccionar_todo = ttk.Button(marco_botones, text="Deseleccionar todo", command=deseleccionar_todo)
boton_deseleccionar_todo.pack(side='left', padx=20)

# Casilla para excluir entradas sin número de teléfono
var_excluir_sin_telefono = tk.BooleanVar()
casilla_excluir_sin_telefono = ttk.Checkbutton(root, text="Excluir entradas sin número de teléfono", variable=var_excluir_sin_telefono)
casilla_excluir_sin_telefono.pack(pady=5)

# Botones de acción
boton_buscar = ttk.Button(root, text="Buscar empresas", command=buscar_empresas)
boton_buscar.pack(padx=5, pady=10)

boton_eliminar_duplicados = ttk.Button(root, text="Eliminar nombres duplicados", command=eliminar_duplicados)
boton_eliminar_duplicados.pack(padx=5, pady=10)

etiqueta_contador = ttk.Label(root, text="Número de empresas: 0")
etiqueta_contador.pack()

boton_guardar = ttk.Button(root, text="Guardar empresas", command=guardar_datos)
boton_guardar.pack(padx=5, pady=10)

# Botón de GitHub
boton_github = ttk.Button(root, text="Repositorio GitHub", command=abrir_github)
boton_github.pack(pady=5)

# Etiqueta "Hecho por" con hipervínculo
etiqueta_hecho_por = ttk.Label(root, text="Hecho por Clément GHANEME", foreground="blue", cursor="hand2")
etiqueta_hecho_por.pack(pady=(10, 5))
etiqueta_hecho_por.bind("<Button-1>", abrir_sitio_web)

root.mainloop()
