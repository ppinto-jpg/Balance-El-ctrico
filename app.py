# --- Aplicación Completa de Balance Eléctrico (Versión .py) ---
import ipywidgets as widgets
from IPython.display import display, clear_output, HTML, SVG
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import json
from base64 import b64encode
import warnings

# Suprimir advertencias menores
warnings.filterwarnings('ignore', category=FutureWarning)


# --- 1. ESTADO GLOBAL DE LA APLICACIÓN ---

# Estilo para las descripciones de los widgets (label)
style_descripcion = {'description_width': '200px'}
layout_input = widgets.Layout(width='95%')

# Modos de operación (columnas del balance)
modos_operacion = ["Navegación", "Maniobra", "Puerto", "Carga/Descarga", "Emergencia"]

# Opciones de Barras para el Diagrama
barras_opciones = ["N/A", "MSB-A", "MSB-B", "EMSB", "220V (T1)"]

# --- BASE DE DATOS DE CABLES MEJORADA (CON AMPACIDAD) ---
CABLE_DATABASE = {
    # Sección (mm²): {'R_ohm_km': ..., 'X_ohm_km': ..., 'Ampacidad_A': ...}
    "16 mm²":  {'R_ohm_km': 1.21,  'X_ohm_km': 0.082, 'Ampacidad_A': 76},
    "25 mm²":  {'R_ohm_km': 0.78,  'X_ohm_km': 0.081, 'Ampacidad_A': 101},
    "35 mm²":  {'R_ohm_km': 0.554, 'X_ohm_km': 0.080, 'Ampacidad_A': 129},
    "50 mm²":  {'R_ohm_km': 0.386, 'X_ohm_km': 0.079, 'Ampacidad_A': 158},
    "70 mm²":  {'R_ohm_km': 0.272, 'X_ohm_km': 0.078, 'Ampacidad_A': 201},
    "95 mm²":  {'R_ohm_km': 0.196, 'X_ohm_km': 0.077, 'Ampacidad_A': 250},
    "120 mm²": {'R_ohm_km': 0.154, 'X_ohm_km': 0.076, 'Ampacidad_A': 292},
    "150 mm²": {'R_ohm_km': 0.124, 'X_ohm_km': 0.076, 'Ampacidad_A': 337},
}


# --- Base de Datos de Generadores ---
GEN_DATABASE = [
    # (Fabricante, Modelo, Potencia_kW_60Hz, Potencia_kW_50Hz)
    ("Caterpillar", "C7.1", 175, 150),
    ("Caterpillar", "C9.3", 300, 250),
    ("Caterpillar", "C18", 550, 450),
    ("Caterpillar", "C18 ACERT", 600, 500),
    ("Caterpillar", "C32", 940, 800),
    ("Caterpillar", "3508C", 800, 680),
    ("Caterpillar", "3512C", 1360, 1150),
    ("Caterpillar", "3516C", 2000, 1700),
    ("Caterpillar", "3516E", 2550, 2200),
    ("Cummins", "QSK19-DM", 560, 460),
    ("Cummins", "QSK38-DM", 1200, 1000),
    ("Cummins", "QSK50-DM", 1600, 1350),
    ("Cummins", "QSK60-DM", 2000, 1800),
    ("Cummins", "QSK95-DM", 3200, 2800),
    ("Volvo Penta", "D9 MG", 260, 215),
    ("Volvo Penta", "D13 MG", 400, 330),
    ("Volvo Penta", "D16 MG", 550, 460),
    ("MAN", "D2868 LE421", 500, 420),
    ("MAN", "D2862 LE431", 750, 630),
    ("MAN", "D2862 LE441", 880, 740),
]

# Base de Datos de Generadores de Emergencia
EMERGENCY_GEN_DATABASE = [
    ("Caterpillar", "C4.4", 80, 65),
    ("Caterpillar", "C4.4 ACERT", 118, 100),
    ("Caterpillar", "C7.1 ACERT", 160, 135),
    ("Cummins", "QSB7-DM", 120, 100),
    ("Cummins", "QSL9-DM", 200, 170),
    ("Volvo Penta", "D5A T", 85, 70),
    ("Volvo Penta", "D8 MG", 180, 150),
]


# --- FUNCIÓN HELPER PARA CREAR CONSUMIDORES DEFAULT ---
def get_consumidor_default(nombre, pn_kw, cos_phi, esencial, barra, modos_kn_ksr):
    """
    Crea una estructura de diccionario para un consumidor
    con valores de Ku y Ksr para cada modo.
    """
    consumidor = {
        'nombre': nombre,
        'pn_kw': pn_kw,
        'cos_phi': cos_phi,
        'esencial': esencial,
        'barra': barra,
        'modos': {}
    }
    for modo, (kn, ksr) in modos_kn_ksr.items():
        consumidor['modos'][modo] = {'kn': kn, 'ksr': ksr}
    return consumidor

# --- FUNCIÓN HELPER PARA OBTENER LISTA ESTÁNDAR ---
def get_lista_std():
    """
    Retorna una lista de diccionarios de consumidores estándar
    basada en la especificación del Combi Freighter 3850 y ejemplos.
    """
    lista = [
        # Generadores (se tratan distinto en el unifilar, pero se listan aquí)
        # Nota: Los G-E no son 'consumidores', se añaden a la lista para el balance de emergencia
        get_consumidor_default(
            "G-1 (Generador Principal)", 0, 0.8, False, "MSB-A",
            {"Navegación": (0, 0), "Maniobra": (0, 0), "Puerto": (0, 0), "Carga/Descarga": (0, 0), "Emergencia": (0, 0)}
        ),
        get_consumidor_default(
            "G-2 (Generador Principal)", 0, 0.8, False, "MSB-A",
            {"Navegación": (0, 0), "Maniobra": (0, 0), "Puerto": (0, 0), "Carga/Descarga": (0, 0), "Emergencia": (0, 0)}
        ),
        get_consumidor_default(
            "G-3 (Generador Principal)", 0, 0.8, False, "MSB-B",
            {"Navegación": (0, 0), "Maniobra": (0, 0), "Puerto": (0, 0), "Carga/Descarga": (0, 0), "Emergencia": (0, 0)}
        ),
        get_consumidor_default(
            "G-E (Generador Emergencia)", 0, 0.8, True, "EMSB",
            {"Navegación": (0, 0), "Maniobra": (0, 0), "Puerto": (0, 0), "Carga/Descarga": (0, 0), "Emergencia": (0, 0)}
        ),
        # Consumidores
        get_consumidor_default(
            "Bombas Serv. General (x2)", 30.0, 0.85, True, "MSB-A",
            {"Navegación": (0.5, 0.8), "Maniobra": (1.0, 0.5), "Puerto": (0.5, 0.2), "Carga/Descarga": (1.0, 0.5), "Emergencia": (0.5, 1.0)}
        ),
        get_consumidor_default(
            "Bombas Lastre (x2)", 55.0, 0.85, False, "MSB-B",
            {"Navegación": (0.0, 0.0), "Maniobra": (1.0, 0.5), "Puerto": (0.0, 0.0), "Carga/Descarga": (1.0, 0.8), "Emergencia": (0.0, 0.0)}
        ),
        get_consumidor_default(
            "Bow Thruster", 280.0, 0.88, False, "MSB-A",
            {"Navegación": (0.0, 0.0), "Maniobra": (1.0, 0.4), "Puerto": (0.0, 0.0), "Carga/Descarga": (0.0, 0.0), "Emergencia": (0.0, 0.0)}
        ),
        get_consumidor_default(
            "Compresores Aire Arranque (x2)", 25.0, 0.80, True, "MSB-A",
            {"Navegación": (0.5, 0.3), "Maniobra": (1.0, 0.5), "Puerto": (0.5, 0.1), "Carga/Descarga": (0.5, 0.1), "Emergencia": (0.5, 0.0)}
        ),
        get_consumidor_default(
            "Bomba Gobierno (x2)", 11.0, 0.85, True, "EMSB", # Típicamente alimentado desde EMSB con feed normal
            {"Navegación": (0.5, 1.0), "Maniobra": (1.0, 1.0), "Puerto": (0.0, 0.0), "Carga/Descarga": (0.0, 0.0), "Emergencia": (0.5, 1.0)}
        ),
        get_consumidor_default(
            "Ventiladores Sala Máquinas (x2)", 22.0, 0.85, True, "MSB-B",
            {"Navegación": (1.0, 1.0), "Maniobra": (1.0, 1.0), "Puerto": (0.5, 0.5), "Carga/Descarga": (1.0, 0.8), "Emergencia": (0.5, 1.0)}
        ),
        get_consumidor_default(
            "Ventiladores Bodega (x4)", 15.0, 0.85, False, "MSB-B",
            {"Navegación": (0.0, 0.0), "Maniobra": (0.0, 0.0), "Puerto": (0.0, 0.0), "Carga/Descarga": (1.0, 0.9), "Emergencia": (0.0, 0.0)}
        ),
        get_consumidor_default(
            "Transformador 440/220V (T1)", 75.0, 0.98, False, "MSB-B", # Representa la carga del trafo
            {"Navegación": (1.0, 0.6), "Maniobra": (1.0, 0.7), "Puerto": (1.0, 0.5), "Carga/Descarga": (1.0, 0.8), "Emergencia": (1.0, 0.3)}
        ),
        get_consumidor_default(
            "Iluminación (General)", 40.0, 0.95, True, "220V (T1)",
            {"Navegación": (1.0, 0.8), "Maniobra": (1.0, 0.9), "Puerto": (1.0, 0.6), "Carga/Descarga": (1.0, 1.0), "Emergencia": (1.0, 0.3)}
        ),
        get_consumidor_default(
            "Servicios Alojamiento (HVAC, Galley)", 60.0, 0.90, False, "220V (T1)",
            {"Navegación": (1.0, 0.7), "Maniobra": (1.0, 0.6), "Puerto": (1.0, 0.5), "Carga/Descarga": (1.0, 0.7), "Emergencia": (0.0, 0.0)}
        ),
        get_consumidor_default(
            "Equipos Navegación (Puente)", 5.0, 0.98, True, "EMSB",
            {"Navegación": (1.0, 1.0), "Maniobra": (1.0, 1.0), "Puerto": (1.0, 0.5), "Carga/Descarga": (1.0, 1.0), "Emergencia": (1.0, 1.0)}
        ),
         get_consumidor_default(
            "Bomba Incendio Emergencia", 30.0, 0.85, True, "EMSB",
            {"Navegación": (0.0, 0.0), "Maniobra": (0.0, 0.0), "Puerto": (0.0, 0.0), "Carga/Descarga": (0.0, 0.0), "Emergencia": (1.0, 1.0)}
        ),
    ]
    return [get_consumidor_dict(c) for c in lista]

def get_consumidor_dict(c_base):
    """
    Toma la estructura base y la convierte en el diccionario
    completo que usa la aplicación (incluyendo widgets).
    --- REFACTORIZADO PARA EL ACORDEÓN ---
    """
    consumidor = {
        'id': f"consumidor_{np.random.randint(1000, 9999)}",
        'nombre_widget': widgets.Text(value=c_base['nombre']),
        'pn_kw_widget': widgets.FloatText(value=c_base['pn_kw']),
        'cos_phi_widget': widgets.FloatText(value=c_base['cos_phi']),
        'esencial_widget': widgets.Checkbox(value=c_base['esencial'], description="Esencial", style={'description_width': 'initial'}),
        'barra_widget': widgets.Dropdown(options=barras_opciones, value=c_base['barra']),
        'modos_widgets': {}
    }
    
    # Crear widgets para cada modo
    for modo in modos_operacion:
        kn_val = c_base['modos'][modo]['kn']
        ksr_val = c_base['modos'][modo]['ksr']
        
        consumidor['modos_widgets'][modo] = {
            'kn': widgets.FloatText(value=kn_val, layout=widgets.Layout(width='60px'), description="Kn:"),
            'ksr': widgets.FloatText(value=ksr_val, layout=widgets.Layout(width='60px'), description="Ksr:")
        }
    return consumidor


# Almacenará la lista de todos los consumidores que agreguemos.
# Carga la lista estándar POR DEFECTO.
global_consumidores = get_lista_std()

# Almacenará los resultados clave para pasarlos a otras pestañas
global_app_state = {
    "max_kw": 0,
    "req_kw_n1_3gen": 0,
    "req_kw_n1_2gen": 0,
    "emerg_kw": 0,
    "emerg_kva": 0,
    "puerto_kw": 0,
    "puerto_kva": 0,
    "largest_motor_kw": 0,
    "largest_motor_cos_phi": 0,
    "selected_gen_kw": 0,
    "selected_gen_kva": 0,
    "selected_emerg_gen_kw": 0, # Para el diagrama unifilar
    "ultimo_diagrama_svg": "" # Para exportar el SVG
}


# --- 2. WIDGETS DE ENTRADA (PESTAÑA 1: Configuración) ---

# --- Sección para agregar un nuevo consumidor (vacío) ---
nuevo_consumidor_titulo = widgets.HTML("<h3>Agregar Nuevo Consumidor (en blanco)</h3>")
nuevo_nombre = widgets.Text(description="Nombre:", style=style_descripcion, layout=layout_input)
nuevo_pn_kw = widgets.FloatText(description="Pn (kW):", value=10.0, style=style_descripcion, layout=layout_input)
nuevo_cos_phi = widgets.FloatText(description="Cos φ:", value=0.85, style=style_descripcion, layout=layout_input)
nuevo_esencial = widgets.Checkbox(description="Esencial (SOLAS)", value=False, style=style_descripcion)
nuevo_barra = widgets.Dropdown(options=barras_opciones, value="N/A", description="Barra (SLD):", style=style_descripcion, layout=layout_input)

# Inputs para los modos del nuevo consumidor
modos_inputs = {}
items_modos = []
for modo in modos_operacion:
    kn = widgets.FloatText(value=0.5, description="Kn:", layout=widgets.Layout(width='120px'))
    ksr = widgets.FloatText(value=0.5, description="Ksr:", layout=widgets.Layout(width='120px'))
    modos_inputs[modo] = {'kn': kn, 'ksr': ksr}
    items_modos.append(widgets.VBox([widgets.HTML(f"<b>{modo}</b>"), widgets.HBox([kn, ksr])]))

# --- CORRECCIÓN: Layout de modos ahora en Acordeón para mejor visibilidad ---
layout_modos_accordion = widgets.Accordion(
    children=[widgets.HBox(items_modos, layout=widgets.Layout(width='100%', justify_content='space-around'))],
    selected_index=None # Colapsado por defecto
)
layout_modos_accordion.set_title(0, "Ver/Ocultar Coeficientes (Kn y Ksr)")

boton_agregar = widgets.Button(description="Agregar Consumidor", button_style='success', icon='plus', layout=widgets.Layout(margin='10px 0'))

# --- Sección para mostrar la lista de consumidores agregados ---
lista_consumidores_titulo = widgets.HTML("<h2>1. Lista de Consumidores</h2>")
# Botones para gestionar la lista estándar
boton_cargar_std = widgets.Button(description="Cargar Lista Estándar", button_style='info', icon='list', layout=widgets.Layout(margin='5px'))
boton_limpiar_lista = widgets.Button(description="Limpiar Toda la Lista", button_style='danger', icon='trash', layout=widgets.Layout(margin='5px'))

# --- NUEVO: Widgets para Guardar/Cargar Configuración ---
boton_guardar_json = widgets.Button(description="Guardar Config.", button_style='primary', icon='save', layout=widgets.Layout(margin='5px'))
upload_json = widgets.FileUpload(accept='.json', description="Cargar Config.", multiple=False, button_style='warning', layout=widgets.Layout(width='300px'))
json_output = widgets.Output() # Para mensajes de Guardar/Cargar/Actualizar

# --- NUEVO: Botón para Actualizar Cálculos Manualmente ---
boton_actualizar_calculos = widgets.Button(
    description="Actualizar Balance y Cálculos",
    button_style='success',
    icon='refresh',
    layout=widgets.Layout(margin='10px 0', width='95%')
)

# VBox que contendrá la lista dinámica de consumidores
lista_consumidores_output = widgets.VBox([])

# Layout completo de la Pestaña 1
layout_tab1 = widgets.VBox([
    lista_consumidores_titulo,
    widgets.HBox([boton_cargar_std, boton_limpiar_lista]),
    widgets.HBox([boton_guardar_json, upload_json]),
    json_output,
    widgets.HTML("<hr>"),
    boton_actualizar_calculos, # <-- BOTÓN DE ACTUALIZACIÓN AÑADIDO
    widgets.HTML("<p><i>Edite los valores (Kn/Ksr) en los acordeones y luego presione 'Actualizar'.</i></p>"),
    lista_consumidores_output, # <-- Aquí se generará la nueva lista con acordeones
    widgets.HTML("<hr>"),
    nuevo_consumidor_titulo,
    nuevo_nombre,
    nuevo_pn_kw,
    nuevo_cos_phi,
    nuevo_esencial,
    nuevo_barra,
    widgets.HTML("<b>Coeficientes (Kn y Ksr) para cada modo:</b>"),
    layout_modos_accordion, # <-- ACORDEÓN AÑADIDO
    boton_agregar
])


# --- 3. PESTAÑAS DE SALIDA ---

# --- Pestaña 2: Balance de Cargas (Output) ---
balance_output = widgets.Output()
balance_chart_output = widgets.Output()
boton_exportar_excel = widgets.Button(description="Exportar a Excel", button_style='primary', icon='download', layout=widgets.Layout(margin='10px 0'))
balance_export_output = widgets.Output()

layout_tab2 = widgets.VBox([
    widgets.HTML("<h2>2. Balance de Cargas Calculado</h2>"),
    widgets.HTML("<p>Esta tabla se actualiza cada vez que agregas/quitas un consumidor o presionas 'Actualizar'. Muestra la potencia activa (kW) y aparente (kVA) para cada modo de operación.</p>"),
    balance_output,
    widgets.HTML("<hr><h3>Gráfico de Cargas (kW)</h3>"),
    balance_chart_output,
    boton_exportar_excel,
    balance_export_output
])

# --- Pestaña 3: Dimensionamiento (Output y Widgets) ---
sizing_output = widgets.Output()
# Widgets para cálculo de Transformador
input_carga_trafo_kva = widgets.FloatText(description="Carga Trafo (kVA):", value=70.0, style=style_descripcion, layout=layout_input)
boton_calc_trafo = widgets.Button(description="Calcular Trafo (115%)", button_style='info')
trafo_output = widgets.Output()

# --- NUEVO: Widgets para Verificación de Arranque de Motores ---
motor_arranque_label = widgets.HTML(value="Motor más grande: <b>---</b>")
motor_lrc_factor = widgets.FloatText(description="Factor LRC (x In):", value=6.5, style=style_descripcion, layout=layout_input, tooltip="Típico: 6.0-8.0")
motor_cos_phi_arranque = widgets.FloatText(description="Cos φ Arranque:", value=0.3, style=style_descripcion, layout=layout_input, tooltip="Típico: 0.2-0.4")
gen_xd_transient = widgets.FloatText(description="Gen. Xd'' (p.u.):", value=0.15, style=style_descripcion, layout=layout_input, tooltip="Reactancia subtransitoria, 0.15-0.20")
boton_verificar_arranque = widgets.Button(description="Verificar Arranque de Motor", button_style='info')
arranque_output = widgets.Output()


layout_tab3 = widgets.VBox([
    widgets.HTML("<h2>3. Dimensionamiento Generadores (Planta Principal)</h2>"),
    widgets.HTML("<p>Cálculo de la potencia requerida según el peor caso (excluyendo Emergencia) y el criterio N-1 (SOLAS).</p>"),
    sizing_output,
    
    # --- NUEVA SECCIÓN: VERIFICACIÓN ARRANQUE DE MOTOR ---
    widgets.HTML("<hr><h2>4. Verificación de Arranque de Motores</h2>"),
    widgets.HTML("<p>Compara los kVA de arranque del motor más grande con la capacidad del generador seleccionado (en Pestaña 6) y estima la caída de tensión.</p>"),
    widgets.VBox([
        motor_arranque_label,
        motor_lrc_factor,
        motor_cos_phi_arranque,
        gen_xd_transient,
        boton_verificar_arranque,
        arranque_output
    ], layout=widgets.Layout(border='1px solid #ccc', padding='10px', margin='10px 0')),
    
    widgets.HTML("<hr><h2>5. Dimensionamiento Transformadores</h2>"),
    widgets.HTML("<p>Calcula la capacidad recomendada del transformador basada en la regla del 115% (del doc. 'Calculo transformadores.doc').</p>"),
    widgets.VBox([
        input_carga_trafo_kva,
        boton_calc_trafo,
        trafo_output
    ], layout=widgets.Layout(border='1px solid #ccc', padding='10px', margin='10px 0')),
    
    widgets.HTML("<hr><h2>6. Verificación Toma de Tierra (Shore Connection)</h2>"),
    widgets.HTML("<p>Compara la carga del modo 'Puerto' con la capacidad de la toma de tierra (ej. 85A @ 400V ≈ 59 kVA).</p>"),
    widgets.VBox([
        label_shore_carga := widgets.HTML(value="Carga en 'Puerto' (Calculada): <b>--- kVA</b>", layout=layout_input), 
        input_shore_kva := widgets.FloatText(description="Toma de Tierra (kVA):", value=59.0, style=style_descripcion, layout=layout_input),
        boton_check_shore := widgets.Button(description="Verificar Toma de Tierra", button_style='info'),
        shore_output := widgets.Output()
    ], layout=widgets.Layout(border='1px solid #ccc', padding='10px', margin='10px 0'))
])


# --- Pestaña 4: Cálculos Auxiliares ---
# Widgets para Caída de Tensión
volt_drop_titulo = widgets.HTML("<h3>Cálculo de Caída de Tensión (Trifásico AC)</h3>")
volt_drop_nota = widgets.HTML("""
<p><i>Nota: Se usa la fórmula precisa para AC trifásico (del doc. 'Calculo de pérdidas de carga'):
<b>ΔU = √3 * I * L * (R * cos φ + X * sin φ)</b></i></p>
<p>Este cálculo ahora también verifica la <b>Ampacidad</b> del cable (capacidad de corriente máxima segura).</p>
""")
volt_I = widgets.FloatText(description="Corriente (A):", value=50, style=style_descripcion)
volt_L = widgets.FloatText(description="Longitud Cable (m):", value=40, style=style_descripcion)
volt_seccion = widgets.Dropdown(options=list(CABLE_DATABASE.keys()), description="Sección Cable:", value="25 mm²", style=style_descripcion)
volt_cosphi = widgets.FloatText(description="Cos φ de la Carga:", value=0.85, min=0.1, max=1.0, step=0.05, style=style_descripcion)
volt_Vn = widgets.FloatText(description="Tensión Nominal (V):", value=440, style=style_descripcion)
volt_boton = widgets.Button(description="Calcular Caída y Ampacidad", button_style='info')
volt_output = widgets.Output()

# --- NUEVO: Calculadora de Cortocircuito (Icc) ---
short_circuit_titulo = widgets.HTML("<hr><h3>Calculadora de Corriente de Cortocircuito (Icc)</h3>")
short_circuit_nota = widgets.HTML("<p>Calcula la Icc simétrica en bornes del generador (usando datos de Pestaña 6) para seleccionar protecciones.</p>")
icc_gen_kva_label = widgets.HTML(value="Gen. kVA (de Pestaña 6): <b>--- kVA</b>", layout=layout_input)
icc_gen_xd = widgets.FloatText(description="Gen. Xd'' (p.u.):", value=0.15, style=style_descripcion, layout=layout_input, tooltip="Reactancia subtransitoria, 0.15-0.20")
icc_Vn = widgets.FloatText(description="Tensión (V):", value=440, style=style_descripcion, layout=layout_input)
boton_calc_icc = widgets.Button(description="Calcular Icc (kA)", button_style='info')
icc_output = widgets.Output()


layout_tab4 = widgets.VBox([
    volt_drop_titulo, volt_drop_nota,
    volt_I, volt_L, volt_seccion, volt_cosphi, volt_Vn,
    volt_boton, volt_output,
    short_circuit_titulo, short_circuit_nota,
    widgets.VBox([
        icc_gen_kva_label,
        icc_gen_xd,
        icc_Vn,
        boton_calc_icc,
        icc_output
    ], layout=widgets.Layout(border='1px solid #ccc', padding='10px', margin='10px 0'))
])

# --- Pestaña 5: Verificación de Requisitos ---
requisitos_output = widgets.Output(layout=widgets.Layout(border='1px solid #ccc', padding='10px'))
layout_tab5 = widgets.VBox([
    widgets.HTML("<h2>5. Verificación de Requisitos (SOLAS N-1)</h2>"),
    widgets.HTML("<p>Esta pestaña verifica si el dimensionamiento cumple con los requisitos N-1 y lista los consumidores esenciales.</p>"),
    requisitos_output
])

# --- Pestaña 6: Selección Generador Principal ---
gen_config_select = widgets.Dropdown(
    options=[('2 Generadores (N-1)', '2gen'), ('3 Generadores (N-1)', '3gen')],
    value='3gen',
    description='Configuración N-1:',
    style=style_descripcion
)
gen_freq_select = widgets.Dropdown(options=[60, 50], value=60, description="Frecuencia (Hz):", style=style_descripcion)
gen_margin_slider = widgets.IntSlider(value=15, min=0, max=50, step=5, description="Margen (%):", style=style_descripcion)
gen_req_label = widgets.HTML(value="Potencia Requerida por Generador: <b>--- kW</b>")
gen_buscar_boton = widgets.Button(description="Buscar Modelos", button_style='primary', icon='search')
gen_resultados_select = widgets.Select(options=[], description='Modelos Encontrados:', layout=widgets.Layout(width='95%', height='200px'), style=style_descripcion)
gen_detalle_output = widgets.Output(layout=widgets.Layout(border='1px solid #ccc', padding='10px', width='95%'))

layout_tab6 = widgets.VBox([
    widgets.HTML("<h2>6. Selección Comercial (Generadores Principales)</h2>"),
    widgets.HTML("<p>Busca en la base de datos interna los modelos de generadores que cumplen con la potencia N-1 requerida (calculada en 'Dimensionamiento').</p>"),
    widgets.VBox([
        gen_config_select,
        gen_freq_select,
        gen_margin_slider,
        gen_req_label,
        gen_buscar_boton,
        gen_resultados_select,
        gen_detalle_output
    ], layout=widgets.Layout(border='1px solid #ccc', padding='10px', margin='10px 0'))
])


# --- Pestaña 7: Planta de Emergencia ---
emerg_load_label = widgets.HTML(value="Carga de Emergencia Calculada: <b>--- kW / --- kVA</b>")
emerg_consumidores_output = widgets.Output(layout=widgets.Layout(border='1px solid #ccc', padding='10px', width='95%', height='150px', overflow_y='auto'))

# --- Selector de Fuente de Emergencia ---
emerg_source_select = widgets.RadioButtons(
    options=['Generador', 'Baterías'],
    value='Generador',
    description='Fuente Emergencia:',
    style=style_descripcion
)

# --- Widgets para Generador (se agrupan) ---
emerg_gen_freq_select = widgets.Dropdown(options=[60, 50], value=60, description="Frecuencia (Hz):", style=style_descripcion)
emerg_gen_margin_slider = widgets.IntSlider(value=20, min=0, max=50, step=5, description="Margen (%):", style=style_descripcion)
emerg_gen_buscar_boton = widgets.Button(description="Buscar Gen. Emergencia", button_style='primary', icon='search')
emerg_gen_resultados_select = widgets.Select(options=[], description='Modelos Encontrados:', layout=widgets.Layout(width='95%', height='150px'), style=style_descripcion)
emerg_gen_detalle_output = widgets.Output(layout=widgets.Layout(border='1px solid #ccc', padding='10px', width='95%'))

emerg_gen_box = widgets.VBox([
    emerg_gen_freq_select,
    emerg_gen_margin_slider,
    emerg_gen_buscar_boton,
    emerg_gen_resultados_select,
    emerg_gen_detalle_output
])

# --- Widgets para Baterías ---
emerg_bat_horas = widgets.FloatText(description="Autonomía (horas):", value=18.0, style=style_descripcion, layout=layout_input, tooltip="SOLAS requiere 18h (pasajeros) o 36h (carga)")
emerg_bat_voltaje = widgets.Dropdown(options=[24, 48, 110, 220], value=24, description="Tensión Banco (V):", style=style_descripcion, layout=layout_input)
emerg_bat_calc_boton = widgets.Button(description="Calcular Banco Baterías", button_style='info', icon='calculator')
emerg_bat_output = widgets.Output(layout=widgets.Layout(border='1px solid #ccc', padding='10px', width='95%'))

emerg_bat_box = widgets.VBox(
    [emerg_bat_horas, emerg_bat_voltaje, emerg_bat_calc_boton, emerg_bat_output],
    layout=widgets.Layout(display='none') # Oculto por defecto
)


layout_tab7 = widgets.VBox([
    widgets.HTML("<h2>7. Dimensionamiento de Planta de Emergencia</h2>"),
    widgets.HTML("<p>Calcula la carga del modo 'Emergencia' y permite dimensionar el generador o el banco de baterías (SOLAS).</p>"),
    widgets.VBox([
        emerg_load_label,
        widgets.HTML("<b>Consumidores alimentados en Emergencia:</b>"),
        emerg_consumidores_output
    ], layout=widgets.Layout(border='1px solid #ccc', padding='10px', margin='10px 0')),
    widgets.VBox([
        emerg_source_select, # Selector
        emerg_gen_box,       # Opciones de Generador
        emerg_bat_box        # Opciones de Baterías
    ], layout=widgets.Layout(border='1px solid #ccc', padding='10px', margin='10px 0'))
])


# --- Pestaña 8: Diagrama Unifilar ---
diagrama_output = widgets.Output(layout=widgets.Layout(border='1px solid #ccc', padding='10px', margin='10px 0', min_height='600px', overflow='auto'))
boton_generar_diagrama = widgets.Button(description="Generar/Actualizar Diagrama", button_style='primary', icon='project-diagram')
boton_exportar_diagrama = widgets.Button(description="Exportar Diagrama (SVG)", button_style='info', icon='download', layout=widgets.Layout(margin='5px'))
diagrama_export_output = widgets.Output()

layout_tab8 = widgets.VBox([
    widgets.HTML("<h2>8. Diagrama Unifilar (SLD)</h2>"),
    widgets.HTML("<p>Genera un diagrama unifilar (Single Line Diagram) basado en la configuración de la Pestaña 1 (columna 'Barra').</p>"),
    widgets.HBox([boton_generar_diagrama, boton_exportar_diagrama]),
    diagrama_export_output,
    diagrama_output
])


# --- 4. CREACIÓN DE LAS PESTAÑAS (TABS) ---
app_tabs = widgets.Tab()
app_tabs.children = [layout_tab1, layout_tab2, layout_tab3, layout_tab4, layout_tab5, layout_tab6, layout_tab7, layout_tab8]
app_tabs.set_title(0, "1. Configuración")
app_tabs.set_title(1, "2. Balance Cargas")
app_tabs.set_title(2, "3. Dimensionamiento")
app_tabs.set_title(3, "4. Cálculos Aux.")
app_tabs.set_title(4, "5. Requisitos")
app_tabs.set_title(5, "6. Selección Gen.")
app_tabs.set_title(6, "7. Emergencia")
app_tabs.set_title(7, "8. Diagrama SLD")


# --- 5. LÓGICA DE LA APLICACIÓN ---

# --- NUEVA FUNCIÓN WRAPPER ---
def on_actualizar_calculos_clicked(b):
    """
    Función wrapper para el botón de actualizar.
    Proporciona feedback al usuario.
    """
    with json_output: # Usamos el output de json para mensajes
        clear_output()
        display(widgets.HTML("<i><i class='fa fa-refresh fa-spin'></i> Actualizando todos los cálculos...</i>"))
        
        # Ejecutar la función principal de cálculo
        calcular_balance_y_dimensionamiento()
        
        clear_output()
        display(widgets.HTML("<p style='color:green;'><b>¡Cálculos actualizados!</b> Revise las otras pestañas.</p>"))


def on_agregar_consumidor_clicked(b):
    """
    Agrega un nuevo consumidor (desde los inputs "nuevo_") a la lista global
    y actualiza la interfaz.
    """
    global global_consumidores
    
    # 1. Crear la estructura base del consumidor desde los inputs
    c_base = {
        'nombre': nuevo_nombre.value,
        'pn_kw': nuevo_pn_kw.value,
        'cos_phi': nuevo_cos_phi.value,
        'esencial': nuevo_esencial.value,
        'barra': nuevo_barra.value,
        'modos': {}
    }
    for modo in modos_operacion:
        c_base['modos'][modo] = {
            'kn': modos_inputs[modo]['kn'].value,
            'ksr': modos_inputs[modo]['ksr'].value
        }
        
    # 2. Crear el diccionario completo (con widgets)
    nuevo_c_dict = get_consumidor_dict(c_base)
    
    # 3. Agregarlo a la lista global
    global_consumidores.append(nuevo_c_dict)
    
    # 4. Actualizar la UI
    actualizar_lista_consumidores()
    on_actualizar_calculos_clicked(None) # Usar la función wrapper
    
    # 5. Limpiar los campos de entrada
    nuevo_nombre.value = ""
    nuevo_pn_kw.value = 10.0
    nuevo_cos_phi.value = 0.85
    nuevo_esencial.value = False
    nuevo_barra.value = "N/A"
    for modo in modos_operacion:
        modos_inputs[modo]['kn'].value = 0.0
        modos_inputs[modo]['ksr'].value = 0.0

def on_quitar_consumidor_clicked(b):
    """
    Función que se asigna dinámicamente a cada botón "Quitar".
    El ID del consumidor a quitar se guarda en b.consumidor_id
    """
    global global_consumidores
    
    consumidor_id_a_quitar = b.consumidor_id
    
    # Filtrar la lista global para quitar el consumidor
    global_consumidores = [c for c in global_consumidores if c['id'] != consumidor_id_a_quitar]
    
    # Actualizar la UI
    actualizar_lista_consumidores()
    on_actualizar_calculos_clicked(None) # Usar la función wrapper

def actualizar_lista_consumidores():
    """
    Limpia y reconstruye la lista de widgets de consumidores (Pestaña 1)
    basándose en la lista global_consumidores.
    --- REFACTORIZADO PARA USAR ACORDEÓN ---
    """
    items_para_vbox = []
    
    # --- 1. Encabezados (con anchos flexibles en porcentaje) ---
    header_box = widgets.HBox([
        widgets.HTML("<b>Consumidor</b>", layout=widgets.Layout(width='35%')),
        widgets.HTML("<b>Pn (kW)</b>", layout=widgets.Layout(width='10%')),
        widgets.HTML("<b>Cos φ</b>", layout=widgets.Layout(width='10%')),
        widgets.HTML("<b>Esencial</b>", layout=widgets.Layout(width='15%')),
        widgets.HTML("<b>Barra (SLD)</b>", layout=widgets.Layout(width='15%')),
        widgets.HTML("<b>Acción</b>", layout=widgets.Layout(width='15%'))
    ], layout=widgets.Layout(width='100%', border='1px solid #aaa', padding='5px', background_color='#f0f0f0'))
    
    items_para_vbox.append(header_box)
    
    if not global_consumidores:
        items_para_vbox.append(widgets.HTML("<i>No hay consumidores. Agregue uno nuevo o cargue la lista estándar.</i>"))
    
    # --- 2. Crear VBox para cada consumidor (Fila + Acordeón) ---
    for c_dict in global_consumidores:
        
        # --- 2a. Crear el HBox de Modos (para el acordeón) ---
        modos_widgets_list = []
        for modo in modos_operacion:
            w_kn = c_dict['modos_widgets'][modo]['kn']
            w_ksr = c_dict['modos_widgets'][modo]['ksr']
            modos_widgets_list.append(widgets.VBox([
                widgets.HTML(f"<b>{modo}</b>"), w_kn, w_ksr
            ], layout=widgets.Layout(width='19%', border='1px solid #f0f0f0', padding='2px', align_items='center')))
        
        modos_hbox = widgets.HBox(modos_widgets_list, layout=widgets.Layout(width='100%', justify_content='space-around'))

        # --- 2b. Crear el Acordeón ---
        modos_accordion = widgets.Accordion(
            children=[modos_hbox],
            selected_index=None # Colapsado por defecto
        )
        modos_accordion.set_title(0, "Ver/Ocultar Modos (Kn/Ksr)")
        
        # --- 2c. Botón Quitar ---
        boton_quitar = widgets.Button(description="Quitar", icon='trash', button_style='danger', layout=widgets.Layout(width='95%'))
        boton_quitar.consumidor_id = c_dict['id'] # Guardamos el ID en el botón
        boton_quitar.on_click(on_quitar_consumidor_clicked)
        
        # --- 2d. Fila HBox principal (con anchos flexibles) ---
        fila_principal = widgets.HBox([
            c_dict['nombre_widget'],
            c_dict['pn_kw_widget'],
            c_dict['cos_phi_widget'],
            c_dict['esencial_widget'],
            c_dict['barra_widget'],
            boton_quitar
        ], layout=widgets.Layout(width='100%', align_items='center'))
        
        # Asignar anchos en porcentaje a cada widget
        fila_principal.children[0].layout.width = '35%' # Nombre
        fila_principal.children[1].layout.width = '10%' # Pn
        fila_principal.children[2].layout.width = '10%' # Cos
        fila_principal.children[3].layout.width = '15%' # Esencial
        fila_principal.children[4].layout.width = '15%' # Barra
        fila_principal.children[5].layout.width = '15%' # Botón
        
        # --- 2e. Crear el VBox final para este consumidor ---
        fila_consumidor_vbox = widgets.VBox([
            fila_principal,
            modos_accordion
        ], layout=widgets.Layout(border='1px solid #ddd', padding='5px', margin='5px 0'))
        
        items_para_vbox.append(fila_consumidor_vbox)
        
    # --- 3. Actualizar el VBox principal ---
    lista_consumidores_output.children = tuple(items_para_vbox)

def calcular_balance_y_dimensionamiento():
    """
    Función principal. Lee todos los widgets de la Pestaña 1,
    calcula el balance y actualiza todas las pestañas de salida.
    ESTA FUNCIÓN AHORA SE LLAMA MANUALMENTE CON EL BOTÓN 'ACTUALIZAR'.
    """
    
    # --- 1. Lectura de Datos (desde Pestaña 1) ---
    datos_consumidores = []
    # Filtrar solo los que NO son generadores (Pn > 0 o nombre no contiene "Generador")
    lista_consumo_real = [
        c for c in global_consumidores 
        if c['pn_kw_widget'].value > 0 or "generador" not in c['nombre_widget'].value.lower()
    ]

    for c_dict in lista_consumo_real:
        consumidor = {
            'nombre': c_dict['nombre_widget'].value,
            'pn_kw': c_dict['pn_kw_widget'].value,
            'cos_phi': c_dict['cos_phi_widget'].value,
            'esencial': c_dict['esencial_widget'].value,
            'barra': c_dict['barra_widget'].value,
            'modos': {}
        }
        for modo in modos_operacion:
            kn = c_dict['modos_widgets'][modo]['kn'].value
            ksr = c_dict['modos_widgets'][modo]['ksr'].value
            consumidor['modos'][modo] = {'kn': kn, 'ksr': ksr}
        
        datos_consumidores.append(consumidor)

    # --- 2. Cálculo del Balance (Pestaña 2) ---
    with balance_output:
        clear_output(wait=True)
        
        data_kw = []
        data_kva = []
        totales = {modo: {'kw': 0, 'kva': 0} for modo in modos_operacion}

        for c in datos_consumidores:
            pn_kw = c['pn_kw']
            cos_phi = c['cos_phi']
            
            row_kw = {"Consumidor": c['nombre'], "Pn (kW)": pn_kw, "cos φ": cos_phi}
            row_kva = {"Consumidor": c['nombre'], "Pn (kW)": pn_kw, "cos φ": cos_phi}
            
            for modo in modos_operacion:
                kn = c['modos'][modo]['kn']
                ksr = c['modos'][modo]['ksr']
                ku = kn * ksr # Factor de utilización total
                
                # Potencia activa consumida (kW)
                pc_kw = pn_kw * ku
                
                # Potencia aparente consumida (kVA)
                sc_kva = pc_kw / cos_phi if cos_phi > 0 else 0
                
                row_kw[modo] = pc_kw
                row_kva[modo] = sc_kva
                
                # Sumar a totales
                totales[modo]['kw'] += pc_kw
                totales[modo]['kva'] += sc_kva
            
            data_kw.append(row_kw)
            data_kva.append(row_kva)

        if not data_kw:
            display(widgets.HTML("<p>No hay consumidores (con Pn > 0) para calcular el balance.</p>"))
            # Limpiar Pestaña 3 (Dimensionamiento)
            with sizing_output:
                clear_output(wait=True)
                display(widgets.HTML("<p>N/A - Calcule el balance primero.</p>"))
            # Limpiar Pestaña 5 (Requisitos)
            # --- CORRECCIÓN: Pasar lista vacía ---
            verificar_requisitos([], totales, "N/A", 0, 0)
            actualizar_tab_seleccion_gen() # Actualizar Tab 6
            actualizar_tab_emergencia() # Actualizar Tab 7
            actualizar_tab_shore(0, 0) # Actualizar Tab 3
            motor_arranque_label.value = "Motor más grande: <b>N/A</b>" # Actualizar Tab 3
            return

        # Crear DataFrames de Pandas
        df_kw = pd.DataFrame(data_kw)
        df_kva = pd.DataFrame(data_kva)
        
        # Añadir filas de totales
        total_kw_row = {"Consumidor": "TOTAL (kW)"}
        total_kva_row = {"Consumidor": "TOTAL (kVA)"}
        for modo in modos_operacion:
            total_kw_row[modo] = totales[modo]['kw']
            total_kva_row[modo] = totales[modo]['kva']
            
        df_kw = pd.concat([df_kw, pd.DataFrame([total_kw_row])], ignore_index=True)
        df_kva = pd.concat([df_kva, pd.DataFrame([total_kva_row])], ignore_index=True)

        # Mostrar tablas
        display(widgets.HTML("<h3>Balance de Potencia Activa (kW)</h3>"))
        display(df_kw.style.format(precision=2).set_properties(**{'text-align': 'right'}))
        display(widgets.HTML("<hr><h3>Balance de Potencia Aparente (kVA)</h3>"))
        display(df_kva.style.format(precision=2).set_properties(**{'text-align': 'right'}))

    # --- 3. Cálculo de Dimensionamiento (Pestaña 3) ---
    with sizing_output:
        clear_output(wait=True)
        
        # Resetear estado global (parcialmente)
        global_app_state["max_kw"] = 0
        global_app_state["req_kw_n1_3gen"] = 0
        global_app_state["req_kw_n1_2gen"] = 0
        global_app_state["emerg_kw"] = 0
        global_app_state["emerg_kva"] = 0
        global_app_state["puerto_kw"] = 0
        global_app_state["puerto_kva"] = 0
        global_app_state["largest_motor_kw"] = 0
        global_app_state["largest_motor_cos_phi"] = 0.8 # Default

        if not datos_consumidores:
            display(widgets.HTML("<p>No hay consumidores para calcular el dimensionamiento.</p>"))
            return

        # Encontrar el peor caso (excluyendo Emergencia)
        modos_principales = [m for m in modos_operacion if m != "Emergencia"]
        peor_caso = "N/A"
        max_kw = 0
        max_kva = 0
        
        for modo in modos_principales:
            if totales[modo]['kw'] > max_kw:
                max_kw = totales[modo]['kw']
                max_kva = totales[modo]['kva']
                peor_caso = modo
                
        # Guardar estado global
        global_app_state["max_kw"] = max_kw
        
        if max_kw == 0:
            display(widgets.HTML("<p>La carga máxima calculada es 0 kW.</p>"))
        else:
            display(widgets.HTML(f"<h4>Peor Caso (Planta Principal): {peor_caso}</h4>"))
            display(widgets.HTML(f"<ul><li>Potencia Activa Máxima: <b>{max_kw:.2f} kW</b></li><li>Potencia Aparente Máxima: <b>{max_kva:.2f} kVA</b></li></ul>"))
            
            # --- Cálculo N-1 (SOLAS) ---
            display(widgets.HTML("<h4>Dimensionamiento N-1 (SOLAS)</h4>"))
            display(widgets.HTML("<p>Se debe poder alimentar la carga máxima con un generador fuera de servicio.</p>"))
            
            # Opción 1: 3 Generadores (2 operativos N-1)
            req_kw_3gen = max_kw / 2
            global_app_state["req_kw_n1_3gen"] = req_kw_3gen
            display(widgets.HTML(f"<b>Opción 3 Generadores (2 op.):</b> Se requieren 3 generadores de <b>{req_kw_3gen:.2f} kW</b> cada uno."))
            
            # Opción 2: 2 Generadores (1 operativo N-1)
            req_kw_2gen = max_kw
            global_app_state["req_kw_n1_2gen"] = req_kw_2gen
            display(widgets.HTML(f"<b>Opción 2 Generadores (1 op.):</b> Se requieren 2 generadores de <b>{req_kw_2gen:.2f} kW</b> cada uno."))

            # Guardar estado de Emergencia
            global_app_state["emerg_kw"] = totales['Emergencia']['kw']
            global_app_state["emerg_kva"] = totales['Emergencia']['kva']
            
            # Guardar estado de Puerto
            global_app_state["puerto_kw"] = totales['Puerto']['kw']
            global_app_state["puerto_kva"] = totales['Puerto']['kva']

    # --- 4. Actualizar Pestañas Dependientes ---
    
    # --- Actualizar Pestaña 3 (Arranque Motor) ---
    motor_nombre = "N/A"
    if datos_consumidores:
        # Encontrar el motor más grande (mayor Pn_kW)
        try:
            c_motor = max(datos_consumidores, key=lambda c: c['pn_kw'])
            global_app_state["largest_motor_kw"] = c_motor['pn_kw']
            global_app_state["largest_motor_cos_phi"] = c_motor['cos_phi']
            motor_nombre = f"{c_motor['nombre']} ({c_motor['pn_kw']} kW)"
        except ValueError:
            motor_nombre = "N/A (lista vacía)"
            
    motor_arranque_label.value = f"Motor más grande: <b>{motor_nombre}</b>"
    with arranque_output: clear_output() # Limpiar resultados de arranque anteriores
    
    # --- Actualizar Pestaña 5 (Requisitos) ---
    # --- CORRECCIÓN: Pasar la lista 'datos_consumidores' ---
    verificar_requisitos(datos_consumidores, totales, peor_caso, max_kw, max_kva)
    
    # --- Actualizar Pestaña 2 (Gráfico) ---
    actualizar_grafico_balance(totales)
    
    # --- Actualizar Pestaña 3 (Toma de Tierra) ---
    actualizar_tab_shore(totales['Puerto']['kw'], totales['Puerto']['kva'])
    
    # --- Actualizar Pestaña 6 (Selección Generador) ---
    actualizar_tab_seleccion_gen()
    
    # --- Actualizar Pestaña 7 (Emergencia) ---
    actualizar_tab_emergencia()

def on_cargar_std_clicked(b):
    """Carga la lista de consumidores estándar."""
    global global_consumidores
    global_consumidores = get_lista_std()
    
    # Actualizar todas las vistas
    actualizar_lista_consumidores()
    on_actualizar_calculos_clicked(None) # Usar la función wrapper
    
    with json_output:
        clear_output()
        print("Lista estándar cargada.")

def on_limpiar_lista_clicked(b):
    """Borra todos los consumidores de la lista."""
    global global_consumidores
    global_consumidores = []
    
    # Limpiar todas las salidas
    actualizar_lista_consumidores()
    on_actualizar_calculos_clicked(None) # Usar la función wrapper
    
    with trafo_output: clear_output()
    with balance_chart_output: clear_output()
    with shore_output: clear_output()
    with json_output:
        clear_output()
        print("Lista de consumidores borrada.")


def on_calc_trafo_clicked(b):
    """Calcula el tamaño del transformador (Pestaña 3)"""
    with trafo_output:
        clear_output(wait=True)
        carga_kva = input_carga_trafo_kva.value
        if carga_kva <= 0:
            print("Ingrese un valor de carga kVA positivo.")
            return
            
        req_kva = carga_kva * 1.15 # Regla del 115%
        
        # Sugerir tamaño comercial estándar (redondeando hacia arriba)
        standar_sizes = [10, 15, 25, 30, 45, 50, 75, 100, 112.5, 150, 200, 225, 250, 300]
        sugerido = "N/A"
        for size in standar_sizes:
            if size >= req_kva:
                sugerido = f"{size} kVA"
                break
        
        print(f"Carga Normal: {carga_kva:.2f} kVA")
        print(f"Capacidad Requerida (115%): {req_kva:.2f} kVA")
        print(f"Capacidad comercial recomendada: {sugerido}")

def on_calc_volt_drop_clicked(b):
    """
    Calcula la caída de tensión Y LA AMPACIDAD.
    """
    with volt_output:
        clear_output(wait=True)
        I = volt_I.value
        L_m = volt_L.value # Longitud en metros
        seccion_key = volt_seccion.value
        cos_phi = volt_cosphi.value
        Vn = volt_Vn.value
        
        if not all([I > 0, L_m > 0, Vn > 0, 0.1 <= cos_phi <= 1.0]):
            print("Error: Todos los valores deben ser positivos y cos φ debe estar entre 0.1 y 1.0.")
            return

        # 1. Obtener datos del cable de la DB
        cable_data = CABLE_DATABASE[seccion_key]
        R_ohm_km = cable_data['R_ohm_km']
        X_ohm_km = cable_data['X_ohm_km']
        ampacidad = cable_data['Ampacidad_A'] # <-- NUEVO
        
        # --- NUEVO: Verificación de Ampacidad ---
        print(f"--- 1. Verificación de Ampacidad (Seguridad) ---")
        print(f"Corriente Ingresada (I): {I:.2f} A")
        print(f"Ampacidad del Cable ({seccion_key}): {ampacidad:.2f} A")
        if I > ampacidad:
            print(f"ADVERTENCIA DE SEGURIDAD: La corriente ({I:.2f} A) SUPERA la ampacidad del cable ({ampacidad:.2f} A).")
        else:
            print(f"OK: La corriente está dentro del límite de ampacidad del cable.")
        
        print("\n--- 2. Verificación Caída de Tensión (Eficiencia) ---")
        
        # 2. Convertir R y X a ohm/m (ya que L está en m)
        R_ohm_m = R_ohm_km / 1000.0
        X_ohm_m = X_ohm_km / 1000.0
        
        # 3. Calcular sin φ
        sin_phi = np.sin(np.arccos(cos_phi))
        
        # 4. Aplicar la fórmula AC Trifásica:
        delta_U_voltios = np.sqrt(3) * I * L_m * (R_ohm_m * cos_phi + X_ohm_m * sin_phi)
        
        # 5. Calcular Porcentaje
        delta_U_porc = (delta_U_voltios / Vn) * 100
        
        print(f"  R: {R_ohm_m:.4f} Ω/m, X: {X_ohm_m:.4f} Ω/m")
        print(f"  Cos φ: {cos_phi:.2f}, Sin φ: {sin_phi:.2f}")
        print(f"Caída de Tensión (ΔU): {delta_U_voltios:.2f} V")
        print(f"Caída de Tensión (%): {delta_U_porc:.2f} %")
        
        # 6. Comparar con límite (del doc 'Calculo de pérdidas de carga.doc')
        limite = 6.0
        if delta_U_porc > limite:
            print(f"ADVERTENCIA: Supera el límite del {limite}% (requerido por clase).")
        else:
            print(f"OK: Cae dentro del límite del {limite}%.")

# --- CORRECCIÓN: Función 'verificar_requisitos' ahora acepta 'datos_consumidores' ---
def verificar_requisitos(datos_consumidores, totales, peor_caso, max_kw, max_kva):
    """Actualiza la Pestaña 5 con la verificación N-1 y la lista de esenciales."""
    with requisitos_output:
        clear_output(wait=True)
        
        if max_kw == 0 and all(totales[m]['kw'] == 0 for m in totales):
            display(widgets.HTML("<p>No se ha calculado el balance de cargas.</p>"))
            return
            
        # --- 1. Lista de Consumidores Esenciales ---
        display(widgets.HTML("<h4>Consumidores Esenciales (SOLAS)</h4>"))
        display(widgets.HTML("<p><i>Consumidores marcados como 'Esencial' y activos (Ku > 0) en modo Emergencia:</i></p>"))
        lista_esenciales_html = "<ul>"
        count_esenciales = 0
        
        # --- CORRECCIÓN: Iterar sobre 'datos_consumidores' (la lista filtrada) ---
        for c in datos_consumidores:
            if c['esencial']:
                # Calcular Ku para el modo Emergencia
                kn = c['modos']['Emergencia']['kn']
                ksr = c['modos']['Emergencia']['ksr']
                ku = kn * ksr
                
                if ku > 0:
                    nombre = c['nombre']
                    pn_kw = c['pn_kw']
                    pc_kw = pn_kw * ku
                    lista_esenciales_html += f"<li>{nombre} (<b>{pc_kw:.2f} kW</b>)</li>"
                    count_esenciales += 1
        
        if count_esenciales == 0:
            lista_esenciales_html += "<li>No hay consumidores esenciales activos en modo Emergencia.</li>"
        lista_esenciales_html += "</ul>"
        display(widgets.HTML(lista_esenciales_html))

        # --- 2. Verificación N-1 ---
        display(widgets.HTML("<hr><h4>Verificación Cumplimiento N-1</h4>"))
        if max_kw == 0:
            display(widgets.HTML("<p>No hay carga máxima (excl. Emergencia) calculada.</p>"))
        else:
            display(widgets.HTML(f"<p>Carga máxima a cubrir (Peor caso: {peor_caso}): <b>{max_kw:.2f} kW</b></p>"))
            
            # Opción 3 Generadores
            req_kw_3gen = global_app_state["req_kw_n1_3gen"]
            capacidad_3gen_n1 = req_kw_3gen * 2 # 2 generadores operativos
            if req_kw_3gen > 0 and capacidad_3gen_n1 >= max_kw:
                display(widgets.HTML(f"<p style='color:green; font-weight:bold;'>[OK] Opción 3 Gen. (c/u {req_kw_3gen:.2f} kW): CUBIERTA (Capacidad N-1: {capacidad_3gen_n1:.2f} kW)</p>"))
            else:
                 display(widgets.HTML(f"<p style='color:red; font-weight:bold;'>[FALLA] Opción 3 Gen. (c/u {req_kw_3gen:.2f} kW): NO CUBIERTA (Capacidad N-1: {capacidad_3gen_n1:.2f} kW)</p>"))
           
            # Opción 2 Generadores
            req_kw_2gen = global_app_state["req_kw_n1_2gen"]
            capacidad_2gen_n1 = req_kw_2gen * 1 # 1 generador operativo
            if req_kw_2gen > 0 and capacidad_2gen_n1 >= max_kw:
                display(widgets.HTML(f"<p style='color:green; font-weight:bold;'>[OK] Opción 2 Gen. (c/u {req_kw_2gen:.2f} kW): CUBIERTA (Capacidad N-1: {capacidad_2gen_n1:.2f} kW)</p>"))
            else:
                 display(widgets.HTML(f"<p style='color:red; font-weight:bold;'>[FALLA] Opción 2 Gen. (c/u {req_kw_2gen:.2f} kW): NO CUBIERTA (Capacidad N-1: {capacidad_2gen_n1:.2f} kW)</p>"))
             
        # --- 3. Recordatorios de Documentos ---
        display(widgets.HTML("<hr><h4>Recordatorios de Requisitos (Documentos)</h4>"))
        display(widgets.HTML("""
            <ul>
                <li><b>Caída de Tensión:</b> No debe exceder el <b>6%</b> (del doc. 'Calculo de pérdidas de carga').</li>
                <li><b>Transformadores:</b> Capacidad recomendada de al menos <b>115%</b> de la carga normal (del doc. 'Calculo transformadores').</li>
            </ul>
        """))


# --- FUNCIONES PARA PESTAÑA 6 (GENERADOR PRINCIPAL) ---

def actualizar_tab_seleccion_gen():
    """Actualiza el label de potencia requerida en la Pestaña 6."""
    config = gen_config_select.value
    margen_porc = gen_margin_slider.value
    
    req_kw_base = 0
    if config == '2gen':
        req_kw_base = global_app_state["req_kw_n1_2gen"]
    elif config == '3gen':
        req_kw_base = global_app_state["req_kw_n1_3gen"]
        
    req_kw_final = req_kw_base * (1 + margen_porc / 100.0)
    
    gen_req_label.value = f"Potencia Requerida por Generador: <b>{req_kw_final:.2f} kW</b> (incluye {margen_porc}% margen)"
    
    # Limpiar resultados anteriores al cambiar la configuración
    with gen_detalle_output:
        clear_output()
    gen_resultados_select.options = []
    
    # Limpiar estado global del generador seleccionado
    global_app_state["selected_gen_kw"] = 0
    global_app_state["selected_gen_kva"] = 0
    # Actualizar label de Icc en Pestaña 4
    icc_gen_kva_label.value = "Gen. kVA (de Pestaña 6): <b>--- kVA</b>"


def on_config_gen_changed(change):
    """Recalcula el label de potencia al cambiar config o margen."""
    actualizar_tab_seleccion_gen()
    
def on_buscar_modelos_clicked(b):
    """Busca en la GEN_DATABASE los modelos que cumplen el requisito."""
    with gen_detalle_output:
        clear_output()
    
    config = gen_config_select.value
    margen_porc = gen_margin_slider.value
    frecuencia = gen_freq_select.value
    
    req_kw_base = 0
    if config == '2gen':
        req_kw_base = global_app_state["req_kw_n1_2gen"]
    elif config == '3gen':
        req_kw_base = global_app_state["req_kw_n1_3gen"]
        
    req_kw_final = req_kw_base * (1 + margen_porc / 100.0)
    
    if req_kw_final == 0:
        gen_resultados_select.options = [("N/A - Calcule el balance primero", "N/A")]
        return
        
    col_potencia = f"Potencia_kW_{frecuencia}Hz"
    
    resultados = []
    for fab, mod, p_60, p_50 in GEN_DATABASE:
        p_nominal = p_60 if frecuencia == 60 else p_50
        
        if p_nominal >= req_kw_final:
            label = f"{fab} {mod} ({p_nominal} kW @ {frecuencia}Hz)"
            unique_id = f"{fab}|{mod}|{p_nominal}|{frecuencia}"
            resultados.append((label, unique_id))
            
    if not resultados:
         gen_resultados_select.options = [("No se encontraron modelos", "N/A")]
    else:
        # Ordenar por potencia (ascendente)
        resultados_sorted = sorted(resultados, key=lambda x: float(x[1].split('|')[2]))
        gen_resultados_select.options = resultados_sorted

def on_gen_seleccionado_changed(change):
    """Muestra los detalles del generador seleccionado."""
    with gen_detalle_output:
        clear_output(wait=True)
        
        selected_id = change['new']
        if not selected_id or selected_id == "N/A":
            global_app_state["selected_gen_kw"] = 0 # Limpiar estado
            global_app_state["selected_gen_kva"] = 0
            icc_gen_kva_label.value = "Gen. kVA (de Pestaña 6): <b>--- kVA</b>"
            return
            
        try:
            fab, mod, p_nominal, frec = selected_id.split('|')
            p_nominal_float = float(p_nominal)
            # Asumir PF=0.8 para el generador
            p_nominal_kva = p_nominal_float / 0.8 
            
            # --- NUEVO: Actualizar estado global y Pestaña 4 ---
            global_app_state["selected_gen_kw"] = p_nominal_float
            global_app_state["selected_gen_kva"] = p_nominal_kva
            icc_gen_kva_label.value = f"Gen. kVA (de Pestaña 6): <b>{p_nominal_kva:.2f} kVA</b>"
            
            display(widgets.HTML(f"<h4>Detalles del Modelo Seleccionado</h4>"))
            display(widgets.HTML(f"""
                <ul>
                    <li><b>Fabricante:</b> {fab}</li>
                    <li><b>Modelo:</b> {mod}</li>
                    <li><b>Potencia Nominal:</b> {p_nominal} kW ({p_nominal_kva:.2f} kVA @ 0.8 PF)</li>
                    <li><b>Frecuencia:</b> {frec} Hz</li>
                </ul>
            """))
            
            # Comparar con el requisito
            config = gen_config_select.value
            margen_porc = gen_margin_slider.value
            
            req_kw_base = 0
            if config == '2gen':
                req_kw_base = global_app_state["req_kw_n1_2gen"]
            elif config == '3gen':
                req_kw_base = global_app_state["req_kw_n1_3gen"]
            req_kw_final = req_kw_base * (1 + margen_porc / 100.0)

            margen_real = ((p_nominal_float / req_kw_final) - 1) * 100 if req_kw_final > 0 else 0
            
            display(widgets.HTML(f"<p>Este modelo ({p_nominal_float:.2f} kW) cumple el requisito de <b>{req_kw_final:.2f} kW</b> con un margen real del <b>{margen_real:.2f}%</b>.</p>"))
            
        except Exception as e:
            print(f"Error al parsear selección: {e}")
            global_app_state["selected_gen_kw"] = 0 # Limpiar estado en error
            global_app_state["selected_gen_kva"] = 0
            icc_gen_kva_label.value = "Gen. kVA (de Pestaña 6): <b>--- kVA</b>"


# --- FUNCIONES PARA PESTAÑA 7 (EMERGENCIA) ---

def actualizar_tab_emergencia():
    """Actualiza los labels y listas en la Pestaña 7."""
    emerg_kw = global_app_state["emerg_kw"]
    emerg_kva = global_app_state["emerg_kva"]
    
    emerg_load_label.value = f"Carga de Emergencia Calculada: <b>{emerg_kw:.2f} kW / {emerg_kva:.2f} kVA</b>"
    
    with emerg_consumidores_output:
        clear_output(wait=True)
        lista_html = "<ul>"
        count = 0
        for c_dict in global_consumidores:
            # Iterar sobre los widgets
            kn = c_dict['modos_widgets']['Emergencia']['kn'].value
            ksr = c_dict['modos_widgets']['Emergencia']['ksr'].value
            ku = kn * ksr
            if ku > 0:
                nombre = c_dict['nombre_widget'].value
                if "generador" not in nombre.lower(): # Excluir los "generadores"
                    pn_kw = c_dict['pn_kw_widget'].value
                    pc_kw = pn_kw * ku
                    lista_html += f"<li>{nombre} (<b>{pc_kw:.2f} kW</b>)</li>"
                    count += 1
        
        if count == 0:
            lista_html = "<p><i>No hay consumidores activos en modo Emergencia.</i></p>"
        else:
            lista_html += "</ul>"
        
        display(widgets.HTML(lista_html))

    # Limpiar resultados anteriores
    with emerg_gen_detalle_output: clear_output()
    emerg_gen_resultados_select.options = []
    with emerg_bat_output: clear_output()
    global_app_state["selected_emerg_gen_kw"] = 0


def on_buscar_gen_emerg_clicked(b):
    """Busca en la EMERGENCY_GEN_DATABASE los modelos que cumplen."""
    with emerg_gen_detalle_output:
        clear_output()
    
    frecuencia = emerg_gen_freq_select.value
    margen_porc = emerg_gen_margin_slider.value
    req_kw_base = global_app_state["emerg_kw"]
    
    req_kw_final = req_kw_base * (1 + margen_porc / 100.0)
    
    if req_kw_final == 0:
        emerg_gen_resultados_select.options = [("N/A - Carga de Emergencia es 0", "N/A")]
        return
        
    resultados = []
    for fab, mod, p_60, p_50 in EMERGENCY_GEN_DATABASE:
        p_nominal = p_60 if frecuencia == 60 else p_50
        
        if p_nominal >= req_kw_final:
            label = f"{fab} {mod} ({p_nominal} kW @ {frecuencia}Hz)"
            unique_id = f"{fab}|{mod}|{p_nominal}|{frecuencia}"
            resultados.append((label, unique_id))
            
    if not resultados:
         emerg_gen_resultados_select.options = [("No se encontraron modelos", "N/A")]
    else:
        # Ordenar por potencia (ascendente)
        resultados_sorted = sorted(resultados, key=lambda x: float(x[1].split('|')[2]))
        emerg_gen_resultados_select.options = resultados_sorted

def on_gen_emerg_seleccionado_changed(change):
    """Muestra los detalles del generador de EMERGENCIA seleccionado."""
    with emerg_gen_detalle_output:
        clear_output(wait=True)
        
        selected_id = change['new']
        if not selected_id or selected_id == "N/A":
            global_app_state["selected_emerg_gen_kw"] = 0 # Limpiar estado
            return
            
        try:
            fab, mod, p_nominal, frec = selected_id.split('|')
            p_nominal_float = float(p_nominal)
            
            # --- NUEVO: Guardar en estado global ---
            global_app_state["selected_emerg_gen_kw"] = p_nominal_float
            
            display(widgets.HTML(f"<h4>Detalles del Modelo Seleccionado</h4>"))
            display(widgets.HTML(f"""
                <ul>
                    <li><b>Fabricante:</b> {fab}</li>
                    <li><b>Modelo:</b> {mod}</li>
                    <li><b>Potencia Nominal:</b> {p_nominal} kW</li>
                    <li><b>Frecuencia:</b> {frec} Hz</li>
                </ul>
            """))
            
            # Comparar con el requisito
            req_kw_base = global_app_state["emerg_kw"]
            margen_porc = emerg_gen_margin_slider.value
            req_kw_final = req_kw_base * (1 + margen_porc / 100.0)
            margen_real = ((p_nominal_float / req_kw_final) - 1) * 100 if req_kw_final > 0 else 0
            
            display(widgets.HTML(f"<p>Este modelo ({p_nominal_float:.2f} kW) cumple el requisito de <b>{req_kw_final:.2f} kW</b> con un margen real del <b>{margen_real:.2f}%</b>.</p>"))

        except Exception as e:
            print(f"Error al parsear selección: {e}")
            global_app_state["selected_emerg_gen_kw"] = 0 # Limpiar en error


def on_emerg_source_changed(change):
    """Muestra u oculta los VBox de Generador o Baterías."""
    source = change['new']
    if source == 'Generador':
        emerg_gen_box.layout.display = 'block'
        emerg_bat_box.layout.display = 'none'
    else: # Baterías
        emerg_gen_box.layout.display = 'none'
        emerg_bat_box.layout.display = 'block'

def on_calc_bateria_clicked(b):
    """Calcula la capacidad del banco de baterías."""
    with emerg_bat_output:
        clear_output(wait=True)
        
        emerg_kw = global_app_state["emerg_kw"]
        horas = emerg_bat_horas.value
        voltaje = emerg_bat_voltaje.value
        
        if emerg_kw <= 0:
            print("Error: La carga de emergencia (kW) es 0.")
            return
        if horas <= 0 or voltaje <= 0:
            print("Error: Las horas y el voltaje deben ser positivos.")
            return
            
        # Calcular P = V * I -> I = P / V
        corriente_total_A = (emerg_kw * 1000) / voltaje
        
        # Capacidad (Ah) = Corriente (A) * Horas (h)
        capacidad_Ah = corriente_total_A * horas
        
        # Aplicar factor de descarga (ej. 0.8) y eficiencia
        capacidad_req_Ah = capacidad_Ah / 0.8 # Asumimos 80% prof. de descarga
        
        display(widgets.HTML("<h4>Dimensionamiento Banco de Baterías</h4>"))
        display(widgets.HTML(f"<p>Carga de Emergencia: <b>{emerg_kw:.2f} kW</b></p>"))
        display(widgets.HTML(f"<p>Tensión del Banco: <b>{voltaje} V</b></p>"))
        display(widgets.HTML(f"<p>Corriente de Descarga: <b>{corriente_total_A:.2f} A</b></p>"))
        display(widgets.HTML(f"<p>Autonomía Requerida: <b>{horas} h</b></p>"))
        display(widgets.HTML(f"<ul><li>Capacidad Teórica (100% descarga): {capacidad_Ah:.2f} Ah</li><li><b>Capacidad Recomendada (80% DOD): {capacidad_req_Ah:.2f} Ah</b></li></ul>"))


# --- NUEVAS FUNCIONES (GUARDAR/CARGAR, ICC, ARRANQUE) ---

def on_guardar_json_clicked(b):
    """
    Lee el estado actual de global_consumidores (desde los widgets)
    y lo guarda en un archivo JSON.
    """
    with json_output:
        clear_output(wait=True)
        
        config_data = []
        for c_dict in global_consumidores:
            consumidor = {
                'nombre': c_dict['nombre_widget'].value,
                'pn_kw': c_dict['pn_kw_widget'].value,
                'cos_phi': c_dict['cos_phi_widget'].value,
                'esencial': c_dict['esencial_widget'].value,
                'barra': c_dict['barra_widget'].value,
                'modos': {}
            }
            for modo in modos_operacion:
                consumidor['modos'][modo] = {
                    'kn': c_dict['modos_widgets'][modo]['kn'].value,
                    'ksr': c_dict['modos_widgets'][modo]['ksr'].value
                }
            config_data.append(consumidor)
        
        # Convertir a JSON string
        json_string = json.dumps(config_data, indent=2)
        
        # Crear enlace de descarga
        try:
            # Esta parte solo funciona en Colab/Jupyter, no en Voila desplegado
            # Intentará crear un enlace, si falla, imprimirá un error
            b64_json = b64encode(json_string.encode()).decode()
            href = f'<a href="data:application/json;base64,{b64_json}" download="balance_electrico_config.json">Descargar Configuración (balance_electrico_config.json)</a>'
            display(HTML(href))
            print("Configuración lista para descargar.")
        except Exception as e:
            print(f"Error al generar el enlace de descarga (esperado en Voila): {e}")

def on_upload_json_changed(change):
    """
    Se activa cuando se sube un archivo JSON.
    Lee el archivo, reconstruye la lista global_consumidores.
    """
    global global_consumidores
    
    with json_output:
        clear_output(wait=True)
        
        if not change['new']:
            print("Carga cancelada.")
            return
            
        # Obtener el archivo subido
        # En Voila, change['new'] es un diccionario, no una lista
        uploaded_file = change['new']
        if isinstance(uploaded_file, (list, tuple)):
            uploaded_file = uploaded_file[0]
            
        try:
            # Leer el contenido del archivo
            content_str = uploaded_file['content'].decode('utf-8')
            config_data = json.loads(content_str)
            
            # Reconstruir la lista global_consumidores
            nueva_lista_consumidores = []
            for c_base in config_data:
                # Asegurar que todos los campos existan (compatibilidad)
                c_base_safe = {
                    'nombre': c_base.get('nombre', 'Sin Nombre'),
                    'pn_kw': c_base.get('pn_kw', 0),
                    'cos_phi': c_base.get('cos_phi', 0.8),
                    'esencial': c_base.get('esencial', False),
                    'barra': c_base.get('barra', 'N/A'),
                    'modos': c_base.get('modos', {m: {'kn': 0, 'ksr': 0} for m in modos_operacion})
                }
                nueva_lista_consumidores.append(get_consumidor_dict(c_base_safe))
            
            global_consumidores = nueva_lista_consumidores
            
            # Actualizar toda la app
            actualizar_lista_consumidores()
            on_actualizar_calculos_clicked(None) # Usar la función wrapper
            print(f"Configuración cargada con éxito desde '{uploaded_file['name']}'.")
            
        except Exception as e:
            print(f"Error al leer el archivo JSON: {e}")
            print("Asegúrese de que sea un archivo JSON válido exportado por esta app.")
        
        # Limpiar el widget de subida para permitir subir el mismo archivo de nuevo
        upload_json.value = {}


def on_check_shore_clicked(b):
    """Verifica la carga de puerto vs la toma de tierra (Pestaña 3)"""
    with shore_output:
        clear_output(wait=True)
        carga_puerto_kva = global_app_state["puerto_kva"]
        capacidad_shore_kva = input_shore_kva.value
        
        print(f"Carga en Modo 'Puerto' (calculada): {carga_puerto_kva:.2f} kVA")
        print(f"Capacidad Toma de Tierra: {capacidad_shore_kva:.2f} kVA")
        
        if capacidad_shore_kva >= carga_puerto_kva:
            print(f"OK: La toma de tierra ({capacidad_shore_kva:.2f} kVA) es SUFICIENTE.")
        else:
            exceso = carga_puerto_kva - capacidad_shore_kva
            print(f"ADVERTENCIA: La toma de tierra NO es suficiente. Faltan {exceso:.2f} kVA.")
            print("Se requerirá operar un generador auxiliar en puerto.")


def on_calc_icc_clicked(b):
    """Calcula el cortocircuito (Pestaña 4)"""
    with icc_output:
        clear_output(wait=True)
        gen_kva = global_app_state["selected_gen_kva"]
        gen_xd = icc_gen_xd.value
        Vn = icc_Vn.value
        
        if gen_kva <= 0:
            print("Error: Seleccione un generador principal (Pestaña 6) primero.")
            return
        if not (0 < gen_xd < 1.0):
            print("Error: La reactancia Xd'' (p.u.) debe ser un valor entre 0 y 1 (ej. 0.15).")
            return
        if Vn <= 0:
            print("Error: La tensión debe ser positiva.")
            return

        # 1. Calcular Corriente Nominal (In) del generador
        In_A = (gen_kva * 1000) / (np.sqrt(3) * Vn)
        
        # 2. Calcular Corriente de Cortocircuito (Icc)
        I_cc_A = In_A / gen_xd
        I_cc_kA = I_cc_A / 1000.0
        
        display(widgets.HTML(f"<h4>Resultados de Cortocircuito (en bornes Gen.)</h4>"))
        display(widgets.HTML(f"<ul><li>Generador: {gen_kva:.2f} kVA, {Vn} V, Xd'': {gen_xd} p.u.</li></ul>"))
        display(widgets.HTML(f"Corriente Nominal (In): <b>{In_A:.2f} A</b>"))
        display(widgets.HTML(f"Corriente Cortocircuito (Icc): <b>{I_cc_A:.2f} A</b> ó <b>{I_cc_kA:.2f} kA</b>"))
        display(widgets.HTML(f"<p><i>Nota: Las protecciones (interruptores) en el tablero principal deben tener una capacidad de ruptura (Icu) <b>mayor</b> a {I_cc_kA:.2f} kA.</i></p>"))


def on_verificar_arranque_clicked(b):
    """Verifica el arranque del motor más grande (Pestaña 3)"""
    with arranque_output:
        clear_output(wait=True)
        
        # 1. Datos del Generador (Seleccionado en Pestaña 6)
        gen_kva = global_app_state.get("selected_gen_kva", 0)
        gen_xd_pu = gen_xd_transient.value
        
        # 2. Datos del Motor (Detectado del balance)
        motor_kw = global_app_state.get("largest_motor_kw", 0)
        motor_cos_phi = global_app_state.get("largest_motor_cos_phi", 0.8)
        
        # 3. Datos de Arranque (Inputs)
        lrc_factor = motor_lrc_factor.value
        cos_phi_arranque = motor_cos_phi_arranque.value
        
        if gen_kva == 0 or motor_kw == 0:
            print("Error: Calcule el balance Y seleccione un generador (Pestaña 6) primero.")
            return
        
        display(widgets.HTML("<h4>1. KVA de Arranque del Motor</h4>"))
        
        # Calcular In del motor
        if motor_cos_phi <= 0: motor_cos_phi = 0.8 # Evitar división por cero
        motor_kva = motor_kw / motor_cos_phi
        motor_in = (motor_kva * 1000) / (np.sqrt(3) * 440) # Asumimos 440V
        
        # Calcular KVA de arranque
        kva_arranque = (np.sqrt(3) * 440 * (motor_in * lrc_factor)) / 1000.0
        kw_arranque = kva_arranque * cos_phi_arranque
        
        display(widgets.HTML(f"Motor Pn: {motor_kw:.2f} kW"))
        display(widgets.HTML(f"Motor KVA (arranque): <b>{kva_arranque:.2f} kVA</b>"))
        display(widgets.HTML(f"Motor KW (arranque): {kw_arranque:.2f} kW"))

        display(widgets.HTML("<hr><h4>2. Capacidad del Generador</h4>"))
        display(widgets.HTML(f"Generador KVA (nominal): <b>{gen_kva:.2f} kVA</b>"))
        
        # Capacidad de arranque (kva) del generador
        gen_cap_arranque_kva = (1 / gen_xd_pu) * gen_kva
        display(widgets.HTML(f"Generador KVA (cap. arranque con Xd''={gen_xd_pu}): <b>{gen_cap_arranque_kva:.2f} kVA</b>"))

        display(widgets.HTML("<hr><h4>3. Verificación</h4>"))
        if gen_cap_arranque_kva < kva_arranque:
            display(widgets.HTML(f"<p style='color:red; font-weight:bold;'>[FALLA] Los KVA de arranque ({kva_arranque:.2f}) superan la capacidad del generador ({gen_cap_arranque_kva:.2f}).</p>"))
        else:
            display(widgets.HTML(f"<p style='color:green; font-weight:bold;'>[OK] El generador puede suministrar los KVA de arranque.</p>"))

        # Estimar caída de tensión (simplificado)
        # (Gen KVA / Motor KVA_arranque) * Xd''
        volt_dip_porc = (kva_arranque / gen_cap_arranque_kva) * 100
        
        display(widgets.HTML(f"Caída de tensión (Dip) estimada en barras: <b>{volt_dip_porc:.2f} %</b>"))
        if volt_dip_porc > 20.0:
            display(widgets.HTML(f"<p style='color:red;'>ADVERTENCIA: Caída de tensión ({volt_dip_porc:.2f}%) supera el 20%. Puede causar que otros contactores caigan.</p>"))
        elif volt_dip_porc > 15.0:
            display(widgets.HTML(f"<p style='color:orange;'>PRECAUCIÓN: Caída de tensión ({volt_dip_porc:.2f}%) supera el 15% (límite usual).</p>"))
        else:
            display(widgets.HTML(f"OK: Caída de tensión aceptable (menor al 15%)."))


def actualizar_grafico_balance(totales):
    """Dibuja el gráfico de barras del balance de cargas (Pestaña 2)"""
    with balance_chart_output:
        clear_output(wait=True)
        
        modos = list(totales.keys())
        kw_values = [totales[m]['kw'] for m in modos]
        
        if sum(kw_values) == 0:
            display(widgets.HTML("<p><i>No hay datos para graficar.</i></p>"))
            return
            
        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(modos, kw_values, color='skyblue')
        
        ax.set_ylabel('Potencia Activa (kW)')
        ax.set_title('Balance de Cargas por Modo de Operación')
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Añadir etiquetas de valor sobre las barras
        ax.bar_label(bars, fmt='%.1f kW', padding=3)
        
        # Ajustar el límite Y para dar espacio a las etiquetas
        ax.set_ylim(top=max(kw_values) * 1.15)
        
        plt.tight_layout()
        plt.show()

def actualizar_tab_shore(puerto_kw, puerto_kva):
    """Actualiza el label en la Pestaña 3, sección Toma de Tierra."""
    label_shore_carga.value = f"Carga en 'Puerto' (Calculada): <b>{puerto_kva:.2f} kVA</b> ({puerto_kw:.2f} kW)"
    # Limpiar resultado anterior
    with shore_output:
        clear_output()

def on_exportar_excel_clicked(b):
    """
    Genera un archivo Excel con los DataFrames del balance (kW y kVA)
    y lo ofrece para descargar.
    """
    with balance_export_output:
        clear_output(wait=True)
        
        # 1. Recalcular los DataFrames (similar a calcular_balance)
        datos_consumidores = []
        lista_consumo_real = [
            c for c in global_consumidores 
            if c['pn_kw_widget'].value > 0 or "generador" not in c['nombre_widget'].value.lower()
        ]
        
        for c_dict in lista_consumo_real:
            consumidor = { 'nombre': c_dict['nombre_widget'].value, 'pn_kw': c_dict['pn_kw_widget'].value, 'cos_phi': c_dict['cos_phi_widget'].value, 'modos': {} }
            for modo in modos_operacion:
                consumidor['modos'][modo] = {'kn': c_dict['modos_widgets'][modo]['kn'].value, 'ksr': c_dict['modos_widgets'][modo]['ksr'].value}
            datos_consumidores.append(consumidor)

        if not datos_consumidores:
            print("No hay datos para exportar.")
            return

        data_kw, data_kva = [], []
        totales = {modo: {'kw': 0, 'kva': 0} for modo in modos_operacion}
        for c in datos_consumidores:
            pn_kw, cos_phi = c['pn_kw'], c['cos_phi']
            row_kw, row_kva = {"Consumidor": c['nombre'], "Pn (kW)": pn_kw, "cos φ": cos_phi}, {"Consumidor": c['nombre'], "Pn (kW)": pn_kw, "cos φ": cos_phi}
            for modo in modos_operacion:
                kn, ksr = c['modos'][modo]['kn'], c['modos'][modo]['ksr']
                ku = kn * ksr
                pc_kw = pn_kw * ku
                sc_kva = pc_kw / cos_phi if cos_phi > 0 else 0
                row_kw[modo], row_kva[modo] = pc_kw, sc_kva
                totales[modo]['kw'] += pc_kw
                totales[modo]['kva'] += sc_kva
            data_kw.append(row_kw)
            data_kva.append(row_kva)

        total_kw_row = {"Consumidor": "TOTAL (kW)"}; total_kva_row = {"Consumidor": "TOTAL (kVA)"}
        for modo in modos_operacion:
            total_kw_row[modo] = totales[modo]['kw']; total_kva_row[modo] = totales[modo]['kva']
            
        df_kw = pd.DataFrame(data_kw); df_kva = pd.DataFrame(data_kva)
        df_kw = pd.concat([df_kw, pd.DataFrame([total_kw_row])], ignore_index=True)
        df_kva = pd.concat([df_kva, pd.DataFrame([total_kva_row])], ignore_index=True)

        # 2. Crear el archivo Excel en memoria
        try:
            output_stream = io.BytesIO()
            with pd.ExcelWriter(output_stream, engine='openpyxl') as writer:
                df_kw.to_excel(writer, sheet_name='Balance_kW', index=False)
                df_kva.to_excel(writer, sheet_name='Balance_kVA', index=False)
            
            output_stream.seek(0)
            
            # 3. Crear enlace de descarga
            b64_excel = b64encode(output_stream.read()).decode()
            href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_excel}" download="balance_electrico_TP3.xlsx">Descargar Balance (balance_electrico_TP3.xlsx)</a>'
            display(HTML(href))
            print("Archivo Excel listo para descargar.")

        except Exception as e:
            print(f"Error al generar el Excel: {e}")


# --- NUEVA FUNCIÓN: GENERAR DIAGRAMA UNIFILAR (CON SVG MANUAL) ---

def on_generar_diagrama_clicked(b):
    """
    Genera el diagrama unifilar (SLD) dinámicamente como un SVG
    basándose en la columna "Barra" de la Pestaña 1.
    """
    global global_app_state
    with diagrama_output:
        clear_output(wait=True)
        display(widgets.HTML("<i>Generando diagrama unifilar...</i>"))
        
        try:
            # --- 1. Obtener Datos Dinámicos ---
            gen_kw = global_app_state.get("selected_gen_kw", 0)
            gen_kw_label = f"{gen_kw:.0f}kW" if gen_kw > 0 else "N/A kW"
            gen_config = gen_config_select.value # '2gen' o '3gen'
            
            emerg_gen_kw = global_app_state.get("selected_emerg_gen_kw", 0)
            if emerg_gen_kw == 0: # Fallback si no se seleccionó
                emerg_gen_kw = global_app_state.get("emerg_kw", 0)
            emerg_gen_label = f"{emerg_gen_kw:.0f}kW"

            # --- 2. Leer la configuración de consumidores ---
            consumidores_por_barra = {barra: [] for barra in barras_opciones}
            for c_dict in global_consumidores:
                barra = c_dict['barra_widget'].value
                if barra != "N/A":
                    # Ignorar los "Generadores" de la lista de consumidores
                    if "generador" not in c_dict['nombre_widget'].value.lower():
                        consumidores_por_barra[barra].append({
                            'nombre': c_dict['nombre_widget'].value,
                            'pn_kw': c_dict['pn_kw_widget'].value
                        })

            # --- 3. Definir Funciones Helper de Dibujo SVG ---
            
            def draw_busbar(x, y, width, label):
                return f"""
                    <rect x="{x}" y="{y}" width="{width}" height="10" fill="black" />
                    <text x="{x - 10}" y="{y + 8}" font-size="12" text-anchor="end" font-family="Arial">{label}</text>
                """

            def draw_generator(x, y, label):
                # Auto-wrap para etiqueta
                label_parts = label.split('\n')
                tspan = f'<tspan x="0" dy="0">{label_parts[0]}</tspan>'
                if len(label_parts) > 1:
                    tspan += f'<tspan x="0" dy="1.2em">{label_parts[1]}</tspan>'
                
                return f"""
                    <g transform="translate({x},{y})">
                        <circle cx="0" cy="0" r="15" stroke="black" stroke-width="2" fill="none" />
                        <text x="0" y="5" font-size="14" text-anchor="middle" font-family="Arial" font-weight="bold">G</text>
                        <line x1="0" y1="15" x2="0" y2="30" stroke="black" stroke-width="2" />
                        <text x="0" y="-20" font-size="12" text-anchor="middle" font-family="Arial">{tspan}</text>
                    </g>
                """

            def draw_motor(x, y, label):
                # Auto-wrap para etiqueta
                label_parts = label.split('\n')
                tspan_html = f'<tspan x="0" dy="0">{label_parts[0]}</tspan>'
                if len(label_parts) > 1:
                    # Aplicar auto-wrap a la segunda línea (nombre largo)
                    words = label_parts[1].split()
                    current_line = ""
                    for word in words:
                        if len(current_line + " " + word) > 20: # Límite 20 chars
                            tspan_html += f'<tspan x="0" dy="1.2em">{current_line.strip()}</tspan>'
                            current_line = word
                        else:
                            current_line += f" {word}"
                    tspan_html += f'<tspan x="0" dy="1.2em">{current_line.strip()}</tspan>'
                
                return f"""
                    <g transform="translate({x},{y})">
                        <circle cx="0" cy="0" r="15" stroke="black" stroke-width="2" fill="none" />
                        <text x="0" y="5" font-size="14" text-anchor="middle" font-family="Arial" font-weight="bold">M</text>
                        <line x1="0" y1="-15" x2="0" y2="-30" stroke="black" stroke-width="2" />
                        <text x="0" y="25" font-size="11" text-anchor="middle" font-family="Arial">{tspan_html}</text>
                    </g>
                """
            
            def draw_load(x, y, label):
                # Auto-wrap para etiqueta
                label_parts = label.split('\n')
                tspan_html = f'<tspan x="0" dy="0">{label_parts[0]}</tspan>'
                if len(label_parts) > 1:
                    # Aplicar auto-wrap a la segunda línea (nombre largo)
                    words = label_parts[1].split()
                    current_line = ""
                    for word in words:
                        if len(current_line + " " + word) > 20: # Límite 20 chars
                            tspan_html += f'<tspan x="0" dy="1.2em">{current_line.strip()}</tspan>'
                            current_line = word
                        else:
                            current_line += f" {word}"
                    tspan_html += f'<tspan x="0" dy="1.2em">{current_line.strip()}</tspan>'

                return f"""
                    <g transform="translate({x},{y})">
                        <rect x="-15" y="-10" width="30" height="20" stroke="black" stroke-width="2" fill="none" />
                        <line x1="0" y1="-10" x2="0" y2="-30" stroke="black" stroke-width="2" />
                        <text x="0" y="25" font-size="11" text-anchor="middle" font-family="Arial">{tspan_html}</text>
                    </g>
                """

            def draw_switch(x1, y1, x2, y2, label, open=False):
                # Dibuja un interruptor simple (línea con un corte)
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2
                open_offset = 8 if open else 0
                return f"""
                    <line x1="{x1}" y1="{y1}" x2="{mid_x - 5}" y2="{mid_y - 5}" stroke="black" stroke-width="2" />
                    <line x1="{mid_x - 5}" y1="{mid_y - 5 - open_offset}" x2="{mid_x + 5}" y2="{mid_y + 5}" stroke="black" stroke-width="2" />
                    <line x1="{mid_x + 5}" y1="{mid_y + 5}" x2="{x2}" y2="{y2}" stroke="black" stroke-width="2" />
                    <text x="{mid_x + 8}" y="{mid_y - 8}" font-size="12" font-family="Arial">{label}</text>
                """
            
            def draw_transformer(x, y, label):
                return f"""
                    <g transform="translate({x},{y})">
                        <circle cx="0" cy="-10" r="10" stroke="black" stroke-width="2" fill="none" />
                        <circle cx="0" cy="10" r="10" stroke="black" stroke-width="2" fill="none" />
                        <line x1="0" y1="-20" x2="0" y2="-30" stroke="black" stroke-width="2" />
                        <line x1="0" y1="20" x2="0" y2="30" stroke="black" stroke-width="2" />
                        <text x="0" y="45" font-size="12" text-anchor="middle" font-family="Arial">{label}</text>
                    </g>
                """

            # --- 4. Construir el String SVG ---
            # SVG más ancho (1200px) y alto (700px)
            svg_parts = [
                '<svg width="1200" height="700" xmlns="http://www.w3.org/2000/svg" style="background-color:white; border:1px solid #ccc; font-family: Arial;">',
                '<defs><style>.label {{ font-size: 12px; font-family: Arial; }}</style></defs>'
            ]
            
            # Coordenadas y anchos ajustados
            MSB_A_Y = 150
            MSB_B_Y = 150
            EMSB_Y = 450
            T1_BUS_Y = 450
            GEN_Y = 50
            LOAD_Y = 280 # Más espacio para etiquetas
            EMSB_LOAD_Y = 580 # Más espacio para etiquetas
            T1_LOAD_Y = 580 # Más espacio para etiquetas
            
            MSB_A_X, MSB_A_W = 100, 450  # Más ancha
            MSB_B_X, MSB_B_W = 650, 450  # Más ancha
            EMSB_X, EMSB_W = 100, 450   # Más ancha
            T1_BUS_X, T1_BUS_W = 650, 450 # Más ancha

            # --- A. Barras (Buses) ---
            svg_parts.append(draw_busbar(MSB_A_X, MSB_A_Y, MSB_A_W, "MSB-A 440V"))
            svg_parts.append(draw_busbar(MSB_B_X, MSB_B_Y, MSB_B_W, "MSB-B 440V"))
            svg_parts.append(draw_busbar(EMSB_X, EMSB_Y, EMSB_W, "EMSB 440V"))
            svg_parts.append(draw_busbar(T1_BUS_X, T1_BUS_Y, T1_BUS_W, "220V (T1)"))

            # --- B. Bus-Tie ---
            bus_tie_x1 = MSB_A_X + MSB_A_W
            bus_tie_x2 = MSB_B_X
            svg_parts.append(draw_switch(bus_tie_x1, MSB_A_Y + 5, bus_tie_x2, MSB_B_Y + 5, "Bus-Tie"))

            # --- C. Generadores Principales ---
            if gen_config == '2gen':
                g1_x = MSB_A_X + 150 # Centrado
                svg_parts.append(draw_generator(g1_x, GEN_Y, f"G-1\n{gen_kw_label}"))
                svg_parts.append(draw_switch(g1_x, GEN_Y + 30, g1_x, MSB_A_Y, "Q1"))
                
                g2_x = MSB_B_X + MSB_B_W - 150 # Centrado
                svg_parts.append(draw_generator(g2_x, GEN_Y, f"G-2\n{gen_kw_label}"))
                svg_parts.append(draw_switch(g2_x, GEN_Y + 30, g2_x, MSB_B_Y, "Q2"))
            else: # 3 Gen
                g1_x = MSB_A_X + 100
                svg_parts.append(draw_generator(g1_x, GEN_Y, f"G-1\n{gen_kw_label}"))
                svg_parts.append(draw_switch(g1_x, GEN_Y + 30, g1_x, MSB_A_Y, "Q1"))
                
                g2_x = MSB_A_X + 250
                svg_parts.append(draw_generator(g2_x, GEN_Y, f"G-2\n{gen_kw_label}"))
                svg_parts.append(draw_switch(g2_x, GEN_Y + 30, g2_x, MSB_A_Y, "Q2"))
                
                g3_x = MSB_B_X + 150
                svg_parts.append(draw_generator(g3_x, GEN_Y, f"G-3\n{gen_kw_label}"))
                svg_parts.append(draw_switch(g3_x, GEN_Y + 30, g3_x, MSB_B_Y, "Q3"))

            # --- D. Sistema de Emergencia ---
            feed_norm_x = EMSB_X + 100
            svg_parts.append(f'<line x1="{feed_norm_x}" y1="{MSB_A_Y + 10}" x2="{feed_norm_x}" y2="{EMSB_Y - 20}" stroke="black" stroke-width="2" />')
            svg_parts.append(draw_switch(feed_norm_x, EMSB_Y - 20, feed_norm_x, EMSB_Y, "Feed Normal"))
            
            ge_x = EMSB_X + 250
            svg_parts.append(draw_generator(ge_x, EMSB_Y - 100, f"G-E\n{emerg_gen_label}"))
            svg_parts.append(draw_switch(ge_x, EMSB_Y - 70, ge_x, EMSB_Y, "Feed Emerg.", open=True))

            # --- E. Transformador ---
            t1_x = T1_BUS_X + 150 # Centrado
            svg_parts.append(draw_transformer(t1_x, T1_BUS_Y - 100, "T1 440/220V"))
            svg_parts.append(f'<line x1="{t1_x}" y1="{T1_BUS_Y - 70}" x2="{t1_x}" y2="{T1_BUS_Y}" stroke="black" stroke-width="2" />') # Conexión a barra
            svg_parts.append(draw_switch(MSB_B_X + MSB_B_W - 100, MSB_B_Y + 10, t1_x, T1_BUS_Y - 130, "Q-T1")) # Feed desde MSB-B
            
            # --- F. Dibujar Cargas (ROBUSTO) ---
            def draw_cargas_svg(barra_x, barra_y, barra_w, cargas, load_y):
                svg_cargas = []
                num_cargas = len(cargas)
                if num_cargas == 0:
                    return svg_cargas
                
                # Calcular espaciado
                # Asegurar un mínimo de 100px por carga si es posible
                spacing = max(100, barra_w / (num_cargas + 1))
                total_width_needed = spacing * (num_cargas - 1)
                
                # Centrar el bloque de cargas
                start_x = barra_x + (barra_w - total_width_needed) / 2
                
                for i, c in enumerate(cargas):
                    pos_x = start_x + i * spacing
                    
                    # Determinar tipo de ícono
                    nombre_lower = c['nombre'].lower()
                    if any(term in nombre_lower for term in ["motor", "bomba", "thruster", "compresor", "ventilador"]):
                        svg_cargas.append(draw_motor(pos_x, load_y, f"{c['pn_kw']:.0f}kW\n{c['nombre']}"))
                    else:
                        svg_cargas.append(draw_load(pos_x, load_y, f"{c['pn_kw']:.0f}kW\n{c['nombre']}"))
                    
                    # Conexión y switch
                    svg_cargas.append(draw_switch(pos_x, barra_y + 10, pos_x, load_y - 30, f"Q-{i+1}"))
                
                return svg_cargas

            svg_parts.extend(draw_cargas_svg(MSB_A_X, MSB_A_Y, MSB_A_W, consumidores_por_barra["MSB-A"], LOAD_Y))
            svg_parts.extend(draw_cargas_svg(MSB_B_X, MSB_B_Y, MSB_B_W, consumidores_por_barra["MSB-B"], LOAD_Y))
            svg_parts.extend(draw_cargas_svg(EMSB_X, EMSB_Y, EMSB_W, consumidores_por_barra["EMSB"], EMSB_LOAD_Y))
            svg_parts.extend(draw_cargas_svg(T1_BUS_X, T1_BUS_Y, T1_BUS_W, consumidores_por_barra["220V (T1)"], T1_LOAD_Y))

            svg_parts.append('</svg>')
            svg_string = "\n".join(svg_parts)
            
            # --- 5. Mostrar el Diagrama ---
            clear_output(wait=True)
            global_app_state["ultimo_diagrama_svg"] = svg_string # Guardar para exportar
            display(HTML(svg_string)) # Muestra el diagrama en el output
            
        except Exception as e:
            clear_output(wait=True)
            display(widgets.HTML(f"<h3 style='color:red;'>Error al generar el diagrama SVG:</h3>"))
            display(widgets.HTML(f"<pre>{e}</pre>"))


def on_exportar_diagrama_clicked(b):
    """Exporta el último SVG generado."""
    with diagrama_export_output:
        clear_output(wait=True)
        svg_data = global_app_state.get("ultimo_diagrama_svg", "")
        
        if not svg_data:
            print("Error: Genere un diagrama primero (botón 'Generar/Actualizar').")
            return
            
        try:
            # Codificar el string SVG para la URL
            b64_svg = b64encode(svg_data.encode('utf-8')).decode('utf-8')
            href = f'<a href="data:image/svg+xml;base64,{b64_svg}" download="diagrama_unifilar_TP3.svg">Descargar Diagrama (diagrama_unifilar_TP3.svg)</a>'
            display(HTML(href))
            print("Diagrama SVG listo para descargar.")
        except Exception as e:
            print(f"Error al generar el enlace de descarga: {e}")


# --- 6. CONECTAR BOTONES A FUNCIONES ---
boton_agregar.on_click(on_agregar_consumidor_clicked)
boton_cargar_std.on_click(on_cargar_std_clicked)
boton_limpiar_lista.on_click(on_limpiar_lista_clicked)
boton_actualizar_calculos.on_click(on_actualizar_calculos_clicked) # <-- CONEXIÓN NUEVA

# Conexiones Pestaña 3
boton_calc_trafo.on_click(on_calc_trafo_clicked)
boton_check_shore.on_click(on_check_shore_clicked)
boton_verificar_arranque.on_click(on_verificar_arranque_clicked)

# Conexiones Pestaña 4
volt_boton.on_click(on_calc_volt_drop_clicked)
boton_calc_icc.on_click(on_calc_icc_clicked)

# Conexiones Pestaña 2
boton_exportar_excel.on_click(on_exportar_excel_clicked)

# Conexiones Pestaña 6
gen_config_select.observe(on_config_gen_changed, names='value')
gen_margin_slider.observe(on_config_gen_changed, names='value')
gen_buscar_boton.on_click(on_buscar_modelos_clicked)
gen_resultados_select.observe(on_gen_seleccionado_changed, names='value')

# Conexiones Pestaña 7
emerg_source_select.observe(on_emerg_source_changed, names='value')
emerg_gen_buscar_boton.on_click(on_buscar_gen_emerg_clicked)
emerg_gen_resultados_select.observe(on_gen_emerg_seleccionado_changed, names='value')
emerg_bat_calc_boton.on_click(on_calc_bateria_clicked)

# Conexiones Pestaña 1 (Guardar/Cargar)
boton_guardar_json.on_click(on_guardar_json_clicked)
upload_json.observe(on_upload_json_changed, names='value')

# Conexiones Pestaña 8 (Diagrama)
boton_generar_diagrama.on_click(on_generar_diagrama_clicked)
boton_exportar_diagrama.on_click(on_exportar_diagrama_clicked)


# --- 7. MOSTRAR LA APLICACIÓN ---

# Título principal
display(HTML("<h1>Herramienta de Balance Eléctrico (TP3 - 73.15)</h1>"))
display(HTML("<p><i>Desarrollado para el Trabajo Práctico N°3. Use las pestañas para navegar por la aplicación.</i></p>"))

# Mostrar las pestañas
try:
    display(app_tabs)

    # --- 8. EJECUTAR CÁLCULOS INICIALES (para mostrar estado por defecto) ---
    actualizar_lista_consumidores()
    
    # --- CAMBIO IMPORTANTE: COMENTAR ESTA LÍNEA PARA EL DEPLOY ---
    # on_actualizar_calculos_clicked(None) 
    # --- FIN DEL CAMBIO ---
    
    # Mostrar un mensaje de que la app cargó pero necesita el cálculo inicial
    with json_output:
        clear_output()
        display(HTML("<p style='color:blue;'><b>Aplicación cargada.</b> Presione 'Cargar Lista Estándar' o 'Actualizar Balance' para comenzar.</p>"))


except Exception as e:
    display(HTML(f"<h2 style='color:red;'>Error Inesperado al Iniciar la App</h2><pre>{e}</pre>"))

print("¡Aplicación de Balance Eléctrico cargada con éxito!")
