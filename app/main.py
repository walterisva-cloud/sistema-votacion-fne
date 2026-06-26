
import os
import csv
import io
import random
from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector

#from flask import render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False # Para que no convierta tildes a códigos raros en JSON
app.config['TEMPLATES_AUTO_RELOAD'] = True
# Forzar a que Flask use UTF-8 internamente para los strings
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.secret_key = 'clave_secreta_colegio' # Para manejar las sesiones de los jueces

# Esto fuerza a que TODAS las respuestas del servidor digan que son UTF-8
@app.after_request
def set_utf8_encoding(response):
    if response.content_type and 'text/html' in response.content_type:
        response.set_data(response.get_data()) # Refresca el contenido
        response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response
def add_header(response):
    # Indica al navegador que guarde las imágenes por 1 hora (3600 segundos)
    if response.content_type.startswith('image'):
        response.cache_control.max_age = 3600
    return response


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre = request.form['nombre']
        pin = request.form['pin']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM jueces WHERE nombre = %s AND pin = %s", (nombre, pin))
        juez = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if juez:
            session['juez_id'] = juez['id']
            session['juez_nombre'] = juez['nombre']
            session['es_admin'] = True if juez['nombre'] == 'Admin' else False
            return redirect(url_for('index'))
            
    return render_template('login.html')
# Configuración de la conexión a la DB
# En get_db_connection agrega 'charset'
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            # --- AJUSTES DE CODIFICACIÓN ---
            charset='utf8mb4',
            use_unicode=True,
            collation='utf8mb4_unicode_ci'
        )
        
        # Opcional: Forzar la sesión de MySQL apenas se conecta
        # Esto asegura que el servidor sepa que Python habla UTF-8
        cursor = conn.cursor()
        cursor.execute("SET NAMES utf8mb4")
        cursor.execute("SET CHARACTER SET utf8mb4")
        cursor.execute("SET character_set_connection=utf8mb4")
        cursor.close()
        
        return conn
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

# --- Función auxiliar para leer la configuración ---
def obtener_estado_resultados():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT valor FROM configuracion WHERE nombre_config = 'resultados_visibles'")
    config = cursor.fetchone()
    cursor.close()
    conn.close()
    return config['valor'] == '1' if config else False

def obtener_tipo_evento():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT valor FROM configuracion WHERE nombre_config = 'tipo_evento'")
    config = cursor.fetchone()
    cursor.close()
    conn.close()
    # '1' es Chico 10 (M), cualquier otra cosa es Reina (F)
    return 'M' if config and config['valor'] == '1' else 'F'

# 💡 AGREGAR ESTA FUNCIÓN AUXILIAR PARA OBTENER EL NOMBRE DEL COLEGIO DINÁMICAMENTE
def obtener_nombre_colegio():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM configuracion WHERE id = 3")
        res = cursor.fetchone()
        cursor.close()
        conn.close()
        if res and res[0]:
            return res[0]
    except Exception as e:
        print(f"Error al obtener colegio: {e}")
    return "Secundario N° 43" # Nombre por defecto si no existe en la BD

# 1. ACTUALIZAR RUTA DE CONFIGURACIÓN PARA ENVIAR CANDIDATOS A LA WEB
@app.route('/admin/config-colegio')
def admin_config_colegio():
    if not session.get('es_admin'):
        return redirect(url_for('index'))
    
    colegio_actual = obtener_nombre_colegio()
    
    jueces_lista = []
    candidatos_lista = []
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Traer Jueces
        cursor.execute("SELECT id, nombre, pin FROM jueces ORDER BY id DESC")
        jueces_lista = cursor.fetchall()
        
        # Traer Candidatos (para la columna de bajas)
        cursor.execute("SELECT id, nombre, genero, activo FROM candidatas ORDER BY genero DESC, nombre ASC")
        candidatos_lista = cursor.fetchall()
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error al recuperar datos: {e}")

    return render_template('admin_carga.html', 
                           colegio_actual=colegio_actual, 
                           jueces=jueces_lista, 
                           candidatos=candidatos_lista)

# 2. NUEVA RUTA PARA CAMBIAR EL ESTADO (DAR DE BAJA / ALTA)
@app.route('/admin/cambiar_estado_candidato/<int:candidato_id>', methods=['POST'])
def cambiar_estado_candidato(candidato_id):
    if not session.get('es_admin'):
        return redirect(url_for('index'))
        
    estado_actual = request.form.get('estado_actual') # Tomamos el valor de la interfaz
    nuevo_estado = 0 if estado_actual == '1' else 1
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE candidatas SET activo = %s WHERE id = %s", (nuevo_estado, candidato_id))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Estado del candidato actualizado correctamente.", "success")
    except Exception as e:
        print(f"Error al cambiar estado: {e}")
        flash("No se pudo cambiar el estado.", "danger")
        
    return redirect(url_for('admin_gestion_vivos'))

@app.route('/admin/agregar_juez', methods=['POST'])
def admin_agregar_juez():
    if not session.get('es_admin'):
        flash("Acceso denegado.", "danger")
        return redirect(url_for('index'))

    nombre_juez = request.form.get('nombre_juez', '').strip()
    if not nombre_juez:
        flash("El nombre del juez es obligatorio.", "warning")
        return redirect(url_for('admin_gestion_vivos'))

    # Generamos un PIN de 4 dígitos al azar
    pin = str(random.randint(1000, 9999))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO jueces (nombre, pin) VALUES (%s, %s)", (nombre_juez, pin))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash(f"¡Juez '{nombre_juez}' agregado con éxito! PIN: {pin}", "success")
    except Exception as e:
        print(f"❌ Error al insertar juez: {e}")
        flash("No se pudo registrar el juez en la base de datos.", "danger")

    return redirect(url_for('admin_gestion_vivos'))

@app.route('/admin/eliminar_juez/<int:juez_id>', methods=['POST'])
def eliminar_juez(juez_id):
    if not session.get('es_admin'):
        return redirect(url_for('index'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Eliminamos el juez de la tabla
        cursor.execute("DELETE FROM jueces WHERE id = %s", (juez_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        # flash('Juez eliminado correctamente', 'success') # Opcional si usás mensajes flash
    except Exception as e:
        print(f"Error al eliminar juez: {e}")
        
    # Redirigimos exactamente al mismo panel de gestión en vivo
    return redirect(url_for('admin_gestion_vivos'))

@app.route('/admin/cargar_masiva', methods=['POST'])
def admin_cargar_masiva():
    if not session.get('es_admin'):
        flash("Acceso denegado.", "danger")
        return redirect(url_for('index'))
        
    if 'archivo_csv' not in request.files:
        flash("No se seleccionó ningún archivo.", "warning")
        return redirect(url_for('admin_config_colegio'))

    file = request.files['archivo_csv']
    nombre_colegio = request.form.get('nombre_colegio', '').strip()

    if file.filename == '' or not nombre_colegio:
        flash("Formulario incompleto. Debes ingresar el nombre del colegio y el archivo.", "warning")
        return redirect(url_for('admin_config_colegio'))

    if file and file.filename.endswith('.csv'):
        try:
            contenido_bytes = file.stream.read()
            texto_csv = contenido_bytes.decode("utf-8-sig")
            
            primera_linea = texto_csv.split('\n')[0] if texto_csv else ""
            separador = ';' if ';' in primera_linea else ','
            
            stream = io.StringIO(texto_csv, newline=None)
            reader = csv.DictReader(stream, delimiter=separador)

            conn = get_db_connection()
            cursor = conn.cursor()

            # 🌟 GUARDAR O ACTUALIZAR EL NOMBRE DEL COLEGIO (id = 3)
            sql_colegio = """
                INSERT INTO configuracion (id, nombre_config, valor) 
                VALUES (3, 'nombre_colegio', %s) 
                ON DUPLICATE KEY UPDATE valor = VALUES(valor);
            """
            cursor.execute(sql_colegio, (nombre_colegio,))

            # Limpieza de las tablas de alumnos y votos
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            cursor.execute("TRUNCATE TABLE votos;")
            cursor.execute("TRUNCATE TABLE candidatas;")

            contador_f = 0
            contador_m = 0

            for row in reader:
                key_nombre = next((k for k in row if k.strip().lower() == 'nombre'), None)
                key_genero = next((k for k in row if k.strip().lower() == 'genero'), None)
                
                if not key_nombre or not key_genero or not row[key_nombre]:
                    continue
                    
                nombre = row[key_nombre].strip()
                genero = row[key_genero].strip().upper()

                if genero == 'F':
                    contador_f += 1
                    foto_nombre = f"cand ({contador_f}).jpeg"
                elif genero == 'M':
                    contador_m += 1
                    foto_nombre = f"chico ({contador_m}).jpeg"
                else:
                    foto_nombre = "default.jpg"

                sql = "INSERT INTO candidatas (nombre, genero, foto) VALUES (%s, %s, %s)"
                cursor.execute(sql, (nombre, genero, foto_nombre))

            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
            conn.commit()
            session.pop('modo_correccion', None)

            flash(f"¡Inicialización exitosa para {nombre_colegio}! {contador_f} Mujeres y {contador_m} Varones.", "success")
            
        except Exception as e:
            if 'conn' in locals() and conn: conn.rollback()
            print(f"❌ Error en Carga Masiva: {e}")
            flash(f"Error al procesar la inicialización: {str(e)}", "danger")
        finally:
            if 'cursor' in locals() and cursor: cursor.close()
            if 'conn' in locals() and conn: conn.close()
    else:
        flash("Formato de archivo incorrecto.", "danger")

    return redirect(url_for('index'))

@app.route('/')
def index():
    if 'juez_id' not in session:
        return redirect(url_for('login'))
    
    genero_actual = obtener_tipo_evento()
    juez_id = session['juez_id']
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Filtramos por el género configurado
    cursor.execute("SELECT * FROM candidatas WHERE genero = %s ORDER BY id", (genero_actual,))
    candidatas_db = cursor.fetchall()
    
    # --- PROCESAMOS NOMBRES E INYECTAMOS NUMERO_ORDEN ---
    candidatas = []
    for i, c in enumerate(candidatas_db, start=1):
        candidata_limpia = dict(c)
        candidata_limpia['numero_orden'] = i
        try:
            candidata_limpia['nombre'] = c['nombre'].encode('latin1').decode('utf-8')
        except:
            pass
        candidatas.append(candidata_limpia)
    
    # 🚀 CORRECCIÓN AQUÍ: Traemos los IDs únicos de candidatos votados en votos_detalle
    cursor.execute("""
        SELECT DISTINCT candidata_id 
        FROM votos_detalle 
        WHERE juez_id = %s
    """, (juez_id,))
    votos_realizados = [v['candidata_id'] for v in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    # --- LÓGICA DE CONTROL EN MEMORIA ---
    ids_candidatas_evento = {c['id'] for c in candidatas}
    votos_filtrados_genero = [vid for vid in votos_realizados if vid in ids_candidatas_evento]
    ya_voto_a_todos = (len(votos_filtrados_genero) >= len(ids_candidatas_evento)) and (len(ids_candidatas_evento) > 0)

    modo_correccion = session.get('modo_correccion', False)
    
    return render_template('index.html', 
                           candidatas=candidatas, 
                           votos_realizados=votos_realizados, 
                           juez=session['juez_nombre'],
                           resultados_habilitados=obtener_estado_resultados(),
                           es_admin=session.get('es_admin'),
                           genero_evento=genero_actual,
                           ya_voto_a_todos=ya_voto_a_todos,
                           modo_correccion=modo_correccion,
                           colegio=obtener_nombre_colegio())
    
@app.route('/activar_correccion_sesion', methods=['POST'])
def activar_correccion_sesion():
    session['modo_correccion'] = True
    return {'status': 'success'}, 200

@app.route('/admin/gestion-vivos')
def admin_gestion_vivos():
    if not session.get('es_admin'):
        return redirect(url_for('index'))
    
    jueces_lista = []
    candidatos_lista = []
    
    # 💡 MUY IMPORTANTE: Dejalos vacíos o con None al inicializar. 
    # Si la base de datos funciona, se tienen que llenar con lo que haya guardado.
    config = {'puntaje_min': 5, 'puntaje_max': 10} 
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Traer Jueces y Candidatos existentes
        cursor.execute("SELECT id, nombre, pin FROM jueces ORDER BY id DESC")
        jueces_lista = cursor.fetchall()
        cursor.execute("SELECT id, nombre, genero, activo FROM candidatas ORDER BY genero DESC, nombre ASC")
        candidatos_lista = cursor.fetchall()
        
        # Traer configuraciones dinámicas
        cursor.execute("SELECT nombre_config, valor FROM configuracion WHERE nombre_config IN ('puntaje_min', 'puntaje_max')")
        filas_config = cursor.fetchall()
        
        for row in filas_config:
            # Forzamos a quitar espacios vacíos por las dudas con .strip()
            clave = row['nombre_config'].strip()
            
            if clave == 'puntaje_min':
                config['puntaje_min'] = int(row['valor'])
            elif clave == 'puntaje_max':
                config['puntaje_max'] = int(row['valor'])
                
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error en panel de gestión: {e}")

    return render_template('admin_gestion.html', jueces=jueces_lista, candidatos=candidatos_lista, config=config)

@app.route('/admin/guardar_limites_puntaje', methods=['POST'])
def guardar_limites_puntaje():
    if not session.get('es_admin'):
        return redirect(url_for('index'))
    
    try:
        # 1. Recuperamos los datos asegurando el nombre exacto del input HTML
        p_min_raw = request.form.get('puntaje_min')
        p_max_raw = request.form.get('puntaje_max')
        
        # 2. Imprimimos en la terminal de Docker para auditar qué viaja desde la web
        print(f"--> [DEBUG VOTA] Recibido del formulario - Min: {p_min_raw}, Max: {p_max_raw}")
        
        if p_min_raw and p_max_raw:
            # Convertimos a entero de forma segura
            p_min = int(p_min_raw)
            p_max = int(p_max_raw)
            
            # 3. Validamos que el mínimo sea estrictamente menor que el máximo
            if p_min < p_max:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Modificamos usando tus registros basados en 'nombre_config'
                cursor.execute("UPDATE configuracion SET valor = %s WHERE nombre_config = 'puntaje_min'", (str(p_min),))
                cursor.execute("UPDATE configuracion SET valor = %s WHERE nombre_config = 'puntaje_max'", (str(p_max),))
                
                conn.commit()
                print("--> [DEBUG VOTA] ¡Base de datos actualizada con éxito!")
                cursor.close()
                conn.close()
            else:
                print(f"--> [DEBUG VOTA] Validación fallida: {p_min} no es menor que {p_max}")
                
    except Exception as e:
        print(f"--> [DEBUG VOTA] ERROR crítico al guardar límites: {e}")
        
    return redirect(url_for('admin_gestion_vivos'))
# --- NUEVA RUTA PARA EL ADMIN ---
@app.route('/toggle_resultados', methods=['POST'])
def toggle_resultados():
    if not session.get('es_admin'):
        return "Acceso denegado", 403
    
    nuevo_estado = request.form.get('estado') # Recibirá '1' o '0'
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE configuracion SET valor = %s WHERE nombre_config = 'resultados_visibles'", (nuevo_estado,))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash("Estado de resultados actualizado", "success")
    return redirect(url_for('resultados'))


@app.route('/cambiar_evento', methods=['POST'])
def cambiar_evento():
    if not session.get('es_admin'):
        return "Acceso denegado", 403
    
    nuevo_tipo = request.form.get('tipo') # Recibe '0' o '1'
    nombre_evento = "Elección Reina" if nuevo_tipo == '0' else "Elección Chico 10"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    # Actualizamos el valor en la tabla de configuración
    cursor.execute("UPDATE configuracion SET valor = %s WHERE nombre_config = 'tipo_evento'", (nuevo_tipo,))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash(f"Sistema configurado para: {nombre_evento}", "success")
    # Redirigimos a resultados para ver el cambio impactado
    return redirect(url_for('resultados'))    

@app.route('/votar/<int:id>')
def votar(id):
    if 'juez_id' not in session:
        return redirect(url_for('login'))
        
    juez_id = session['juez_id']
    genero_actual = obtener_tipo_evento() # Obtenemos si es 'F' o 'M'
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    
    # 1. Traemos únicamente los datos del participante (quitamos las columnas fijas del LEFT JOIN anterior)
    query = """
    SELECT 
        c.id, c.nombre, c.foto, c.genero, sub.posicion AS numero_orden
    FROM (
        SELECT id, ROW_NUMBER() OVER (PARTITION BY genero ORDER BY id) as posicion
        FROM candidatas
    ) sub
    JOIN candidatas c ON c.id = sub.id
    WHERE c.id = %s;
    """
    
    cursor.execute(query, (id,))
    candidata_raw = cursor.fetchone()
    
    if not candidata_raw:
        cursor.close()
        conn.close()
        return "Candidato no encontrado", 404
        
    candidata = dict(candidata_raw)
    try:
        candidata['nombre'] = candidata_raw['nombre'].encode('latin1').decode('utf-8')
    except:
        pass

    # 2. Traer las CATEGORÍAS activas de la base de datos
    cursor.execute("SELECT id, nombre, icono FROM categorias ORDER BY id ASC")
    categorias_raw = cursor.fetchall()

    # 🚀 CONTROL ABSOLUTO DE CARACTERES: Nombres perfectos e íconos planos e indestructibles
    lista_categorias = []
    for row in categorias_raw:
        cat = dict(row)
        try:
            cat['nombre'] = row['nombre'].encode('latin1').decode('utf-8')
        except:
            pass
            
        try:
            if row['icono']:
                cat['icono'] = row['icono'].encode('latin1').decode('utf-8')
            else:
                cat['icono'] = ""
        except:
            cat['icono'] = "" # Si tira error por caracteres raros, lo vaciamos por seguridad

        # Mapeamos los nombres limpios con tildes para la interfaz visual
        if cat['nombre'].lower() in ['desempenio', 'desempeño']:
            cat['nombre'] = 'Desenvolvimiento'
        elif cat['nombre'].lower() == 'simpatia':
            cat['nombre'] = 'Simpatía'
            
        lista_categorias.append(cat)

    # 3. Traer los VOTOS PREVIOS que este juez ya asignó a este participante (para Modo Corrección)
    cursor.execute("""
        SELECT categoria_id, puntaje 
        FROM votos_detalle 
        WHERE juez_id = %s AND candidata_id = %s
    """, (juez_id, id))
    
    # Armamos un diccionario simple en Python para mapearlo fácil en el HTML -> { categoria_id: puntaje }
    votos_previos = {row['categoria_id']: row['puntaje'] for row in cursor.fetchall()}
    
    # Agregamos una bandera simulando el 'ya_votado' si el mapa tiene registros
    candidata['ya_votado'] = 1 if len(votos_previos) > 0 else 0

    # 4. Control para habilitar el botón de modificación global (Adaptado a votos_detalle)
    cursor.execute("SELECT COUNT(1) as total FROM candidatas WHERE genero = %s", (genero_actual,))
    total_candidatas = cursor.fetchone()['total']
    
    # Contamos cuántos participantes únicos ya votó este juez (usando un DISTINCT)
    cursor.execute("""
        SELECT COUNT(DISTINCT vd.candidata_id) as total 
        FROM votos_detalle vd
        JOIN candidatas c ON vd.candidata_id = c.id
        WHERE vd.juez_id = %s AND c.genero = %s
    """, (juez_id, genero_actual))
    total_votos_juez = cursor.fetchone()['total']
    
    ya_voto_a_todos = (total_votos_juez >= total_candidatas) and (total_candidatas > 0)
    
    # 5. Recuperar límites de puntaje desde configuracion
    p_min, p_max = 5, 10
    cursor.execute("SELECT nombre_config, valor FROM configuracion WHERE nombre_config IN ('puntaje_min', 'puntaje_max')")
    for row in cursor.fetchall():
        if row['nombre_config'] == 'puntaje_min':
            p_min = int(row['valor'])
        elif row['nombre_config'] == 'puntaje_max':
            p_max = int(row['valor'])
            
    cursor.close()
    conn.close()

    lista_puntajes = list(range(p_min, p_max + 1))
    
    return render_template('votar.html', 
                           candidata=candidata, 
                           ya_voto_a_todos=ya_voto_a_todos,
                           lista_puntajes=lista_puntajes,
                           lista_categorias=lista_categorias,
                           votos_previos=votos_previos)

@app.route('/guardar_voto', methods=['POST'])
def guardar_voto():
    if 'juez_id' not in session:
        return redirect(url_for('login'))

    c_id = request.form.get('candidata_id')
    juez_id = session['juez_id']

    if not c_id:
        flash("Error al procesar la solicitud.", "danger")
        return redirect(url_for('index'))

    # Filtramos del request.form solo los elementos que corresponden a las calificaciones
    votos_recibidos = {k: v for k, v in request.form.items() if k.startswith('categoria_')}

    if not votos_recibidos:
        flash("Formulario incompleto. Por favor selecciona los puntajes.", "danger")
        return redirect(url_for('index'))

    conn = None
    cursor = None
    hubo_modificacion = False
    
    try:
        c_id = int(c_id)
        conn = get_db_connection()
        cursor = conn.cursor()

        # Recorremos cada una de las categorías enviadas por el jurado
        for key, value in votos_recibidos.items():
            # Extraemos el ID de la categoría del nombre del input (ej: 'categoria_4' -> 4)
            categoria_id = int(key.split('_')[1])
            puntaje = int(value)

            sql = """
                INSERT INTO votos_detalle (juez_id, candidata_id, categoria_id, puntaje)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    puntaje = VALUES(puntaje);
            """
            cursor.execute(sql, (juez_id, c_id, categoria_id, puntaje))
            
            # Si rowcount es 2, significa que MySQL actualizó un registro preexistente
            if cursor.rowcount == 2:
                hubo_modificacion = True

        conn.commit()
        
        if hubo_modificacion:
            flash("¡Calificación modificada con éxito!", "success")
        else:
            flash("¡Voto registrado con éxito!", "success")

    except mysql.connector.Error as err:
        if conn: conn.rollback()
        print(f"Error procesando votación dinámica: {err}")
        flash("Error al procesar el voto en la base de datos.", "danger")
    
    finally:
        if cursor:
            try: cursor.close()
            except: pass
        if conn:
            try: conn.close()
            except: pass

    return redirect(url_for('index'))
    
@app.route('/resultados')
def resultados():
    if 'juez_id' not in session:
        return redirect(url_for('login'))
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
        
        genero_actual = obtener_tipo_evento()
        es_administrador = session.get('es_admin')

        # 🚀 SOLUCIÓN DEFINITIVA: Usamos CONCAT para armar los LIKE sin romper el formato de Python
        sql_ranking = """
            SELECT 
                c.nombre as nombre, 
                CAST(IFNULL(SUM(CASE WHEN LOWER(cat.nombre) LIKE CONCAT('%%', 'belleza', '%%') THEN vd.puntaje ELSE 0 END), 0) AS SIGNED) as belleza, 
                CAST(IFNULL(SUM(CASE WHEN LOWER(cat.nombre) LIKE CONCAT('%%', 'simpat', '%%') THEN vd.puntaje ELSE 0 END), 0) AS SIGNED) as simpatia, 
                CAST(IFNULL(SUM(CASE WHEN LOWER(cat.nombre) LIKE CONCAT('%%', 'elegan', '%%') THEN vd.puntaje ELSE 0 END), 0) AS SIGNED) as elegancia,
                CAST(IFNULL(SUM(vd.puntaje), 0) AS SIGNED) as total 
            FROM candidatas c 
            LEFT JOIN votos_detalle vd ON c.id = vd.candidata_id 
            LEFT JOIN categorias cat ON vd.categoria_id = cat.id
            WHERE c.genero = %s
            GROUP BY c.id, c.nombre 
            ORDER BY total DESC, nombre ASC;
        """
        cursor.execute(sql_ranking, (genero_actual,))
        ranking_raw = cursor.fetchall()

        # Decodificación de acentos en el ranking
        ranking = []
        for r in ranking_raw:
            candidata_r = dict(r)
            try:
                candidata_r['nombre'] = r['nombre'].encode('latin1').decode('utf-8')
            except:
                pass
            ranking.append(candidata_r)

        # Si la tabla está vacía, inicializamos un diccionario dummy
        if not ranking:
            ranking = [{'nombre': 'Sin datos', 'belleza': 0, 'simpatia': 0, 'elegancia': 0, 'total': 0}]

        # --- LÓGICA DE EMPATE DETALLADA ---
        hay_empate = False
        categorias_empatadas = []

        if len(ranking) > 1:
            primer_puesto = ranking[0]
            segundo_puesto = ranking[1]

            if 'total' in primer_puesto and 'total' in segundo_puesto:
                if primer_puesto['total'] == segundo_puesto['total'] and primer_puesto['total'] > 0:
                    hay_empate = True
                    if primer_puesto.get('belleza') == segundo_puesto.get('belleza'):
                        categorias_empatadas.append("Belleza")
                    if primer_puesto.get('simpatia') == segundo_puesto.get('simpatia'):
                        categorias_empatadas.append("Simpatía")
                    if primer_puesto.get('elegancia') == segundo_puesto.get('elegancia'):
                        categorias_empatadas.append("Elegancia")

        # 🚀 PARTICIPACIÓN DETALLADA: Corregida para ser compatible con DISTINCT de MySQL
        participacion = []
        if es_administrador:
            try: cursor.fetchall() 
            except: pass
            
            cursor.execute("""
                SELECT DISTINCT j.nombre as juez, c.nombre as candidata 
                FROM votos_detalle vd 
                JOIN jueces j ON vd.juez_id = j.id 
                JOIN candidatas c ON vd.candidata_id = c.id
                ORDER BY juez ASC, candidata ASC;
            """)
            participacion = cursor.fetchall()
        
        try: cursor.fetchall() 
        except: pass

       # --- MONITOR DE ACTIVIDAD DE JUECES EN TIEMPO REAL ---
        cursor.execute("SELECT COUNT(1) as total FROM candidatas WHERE genero = %s AND activo = 1", (genero_actual,))
        total_candidatas_genero = cursor.fetchone()['total']
        
        try: cursor.fetchall() 
        except: pass

        query_monitoreo = """
            SELECT 
                j.id as juez_id,
                j.nombre as juez_nombre,
                COUNT(DISTINCT vd.candidata_id) as votos_emitidos
            FROM jueces j
            CROSS JOIN candidatas c ON c.genero = %s AND c.activo = 1
            LEFT JOIN votos_detalle vd ON j.id = vd.juez_id AND c.id = vd.candidata_id
            WHERE j.nombre != 'Admin'
            GROUP BY j.id, j.nombre
            ORDER BY votos_emitidos ASC, j.nombre ASC;
        """
        # 🚀 CORRECCIÓN AQUÍ: Le agregamos (genero_actual,) para que MySQL tenga el parámetro que le falta
        cursor.execute(query_monitoreo, (genero_actual,))
        jueces_raw = cursor.fetchall()
        
        estado_jueces = []
        todos_terminaron = True
        
        for j in jueces_raw:
            juez_limpio = {
                'nombre': j['juez_nombre'],
                'votos_emitidos': j['votos_emitidos'],
                'total_esperado': total_candidatas_genero,
                'porcentaje': 0
            }
            
            try:
                juez_limpio['nombre'] = j['juez_nombre'].encode('latin1').decode('utf-8')
            except:
                pass
                
            if total_candidatas_genero > 0:
                juez_limpio['porcentaje'] = int((j['votos_emitidos'] / total_candidatas_genero) * 100)
                
            if juez_limpio['porcentaje'] < 100:
                todos_terminaron = False
                
            estado_jueces.append(juez_limpio)

        try: cursor.fetchall() 
        except: pass

        resultados_hab = obtener_estado_resultados()

        # LISTA DE CATEGORÍAS PARA EL ABM DEL MODAL
        lista_categorias = []
        try:
            conn_cat = get_db_connection()
            cursor_cat = conn_cat.cursor(dictionary=True)
            cursor_cat.execute("SELECT id, nombre, icono FROM categorias ORDER BY id ASC")
            categorias_raw = cursor_cat.fetchall()
            
            for row in categorias_raw:
                cat = dict(row)
                try:
                    cat['nombre'] = row['nombre'].encode('latin1').decode('utf-8')
                except:
                    pass
                try:
                    if row['icono']:
                        cat['icono'] = row['icono'].encode('latin1').decode('utf-8')
                except:
                    pass
                lista_categorias.append(cat)
            cursor_cat.close()
            conn_cat.close()
        except Exception as e:
            print(f"Error al traer categorías: {e}")

        return render_template('resultados.html', 
                               ranking=ranking,
                               participacion=participacion,
                               genero_evento=genero_actual,
                               resultados_habilitados=resultados_hab,
                               es_admin=es_administrador,
                               juez=session['juez_nombre'],
                               hay_empate=hay_empate,
                               estado_jueces=estado_jueces,
                               todos_terminaron=todos_terminaron, 
                               lista_categorias=lista_categorias,
                               colegio=obtener_nombre_colegio())

    except mysql.connector.Error as err:
        print(f"Error en la base de datos: {err}")
        return f"Error técnico: {err}", 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/admin/categoria/guardar', methods=['POST'])
def admin_categoria_guardar():
    if not session.get('es_admin'):
        return redirect(url_for('index'))
    
    cat_id = request.form.get('categoria_id')
    nombre = request.form.get('nombre')
    icono = request.form.get('icono', '✨')
    
    if not nombre:
        flash("El nombre de la categoría es obligatorio.", "danger")
        return redirect(url_for('resultados')) # O la ruta de tu panel principal
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if cat_id: # MODO EDICIÓN
            cursor.execute("""
                UPDATE categorias 
                SET nombre = %s, icono = %s 
                WHERE id = %s
            """, (nombre, icono, int(cat_id)))
            flash("¡Categoría actualizada con éxito!", "success")
        else: # MODO ALTA
            cursor.execute("""
                INSERT INTO categorias (nombre, icono) 
                VALUES (%s, %s)
            """, (nombre, icono))
            flash("¡Nueva categoría añadida con éxito!", "success")
            
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error al guardar categoría: {e}")
        flash("Error al procesar la categoría en la base de datos.", "danger")
        
    return redirect(url_for('resultados'))


@app.route('/admin/categoria/eliminar/<int:id>', methods=['POST'])
def admin_categoria_eliminar(id):
    if not session.get('es_admin'):
        return redirect(url_for('index'))
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Borramos en cascada los votos detallados vinculados a esta categoría
        cursor.execute("DELETE FROM votos_detalle WHERE categoria_id = %s", (id,))
        
        # 2. Borramos la categoría base
        cursor.execute("DELETE FROM categorias WHERE id = %s", (id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        flash("Categoría eliminada correctamente.", "success")
    except Exception as e:
        print(f"Error al eliminar categoría: {e}")
        flash("Error al eliminar la categoría.", "danger")
        
    return redirect(url_for('resultados'))        
    
@app.route('/logout')
def logout():
    session.clear() # Esto borra toda la información del juez
    return redirect(url_for('login'))
import os
from flask import Flask, render_template # ... tus otros imports

@app.after_request
def add_header(response):
    # Si la respuesta es una imagen, le decimos al navegador que la guarde por 2 horas
    if response.content_type and response.content_type.startswith('image'):
        response.cache_control.max_age = 7200
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
