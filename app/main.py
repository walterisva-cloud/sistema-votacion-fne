from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import os
import time
from flask import flash # Agregá esto arriba en los imports

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
    for i, c in enumerate(candidatas_db, start=1): # start=1 para que empiece en 1 y no en 0
        candidata_limpia = dict(c)
        
        # Inyectamos el campo dinámico en memoria
        candidata_limpia['numero_orden'] = i
        
        try:
            candidata_limpia['nombre'] = c['nombre'].encode('latin1').decode('utf-8')
        except:
            pass
        candidatas.append(candidata_limpia)
    # ---------------------------------------------------
    
    # Obtenemos los IDs de los votos realizados por este juez
    cursor.execute("SELECT candidata_id FROM votos WHERE juez_id = %s", (juez_id,))
    votos_realizados = [v['candidata_id'] for v in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    # --- 💡 LÓGICA DE CONTROL EN MEMORIA (PYTHON PURO) ---
    # 1. Obtenemos un conjunto (set) de todos los IDs de los candidatos del evento actual
    ids_candidatas_evento = {c['id'] for c in candidatas}
    
    # 2. Filtramos los votos realizados por el juez que correspondan SOLAMENTE al género activo
    # (Esto evita problemas si quedaron votos viejos guardados en la base de datos de otros eventos)
    votos_filtrados_genero = [vid for vid in votos_realizados if vid in ids_candidatas_evento]
    
    # 3. Comparamos si la cantidad de votos de este género es igual o mayor a la cantidad de participantes
    ya_voto_a_todos = (len(votos_filtrados_genero) >= len(ids_candidatas_evento)) and (len(ids_candidatas_evento) > 0)

    # Al final de la ruta, antes del render_template, agregamos esta línea:
    modo_correccion = session.get('modo_correccion', False)
    
    return render_template('index.html', 
                           candidatas=candidatas, 
                           votos_realizados=votos_realizados, 
                           juez=session['juez_nombre'],
                           resultados_habilitados=obtener_estado_resultados(),
                           es_admin=session.get('es_admin'),
                           genero_evento=genero_actual,
                           ya_voto_a_todos=ya_voto_a_todos,
                           modo_correccion=modo_correccion) # <-- PASAMOS ESTA NUEVA VARIABLE
    
@app.route('/activar_correccion_sesion', methods=['POST'])
def activar_correccion_sesion():
    session['modo_correccion'] = True
    return {'status': 'success'}, 200

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
    # Usamos buffered=True para evitar desincronizaciones si hay subconsultas
    cursor = conn.cursor(dictionary=True, buffered=True)
    
    # 1. Traemos los datos del candidato e incluimos sus votos previos si existen
    query = """
    SELECT 
        c.id, c.nombre, c.foto, c.genero, sub.posicion AS numero_orden,
        v.cat_belleza, v.cat_simpatia, v.cat_elegancia,
        IF(v.id IS NOT NULL, 1, 0) as ya_votado
    FROM (
        SELECT id, ROW_NUMBER() OVER (PARTITION BY genero ORDER BY id) as posicion
        FROM candidatas
    ) sub
    JOIN candidatas c ON c.id = sub.id
    LEFT JOIN votos v ON c.id = v.candidata_id AND v.juez_id = %s
    WHERE c.id = %s;
    """
    
    cursor.execute(query, (juez_id, id))
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

    # 2. Control para habilitar el botón de modificación global
    # Contamos cuántos participantes hay en total del género activo
    cursor.execute("SELECT COUNT(1) as total FROM candidatas WHERE genero = %s", (genero_actual,))
    total_candidatas = cursor.fetchone()['total']
    
    # Contamos cuántos votos ya cargó este juez para este género
    cursor.execute("""
        SELECT COUNT(1) as total FROM votos v
        JOIN candidatas c ON v.candidata_id = c.id
        WHERE v.juez_id = %s AND c.genero = %s
    """, (juez_id, genero_actual))
    total_votos_juez = cursor.fetchone()['total']
    
    # Si ya votó a todos, habilitamos la bandera para mostrar el botón en la plantilla
    ya_voto_a_todos = (total_votos_juez >= total_candidatas) and (total_candidatas > 0)
        
    cursor.close()
    conn.close()
    
    return render_template('votar.html', 
                           candidata=candidata, 
                           ya_voto_a_todos=ya_voto_a_todos)

@app.route('/guardar_voto', methods=['POST'])
def guardar_voto():
    if 'juez_id' not in session:
        return redirect(url_for('login'))

    # 1. Capturamos los datos del formulario
    c_id = request.form.get('candidata_id')
    v_belleza = request.form.get('cat_belleza')
    v_simpatia = request.form.get('cat_simpatia')
    v_elegancia = request.form.get('cat_elegancia')
    
    # 2. Verificamos que nada esté vacío
    if not all([c_id, v_belleza, v_simpatia, v_elegancia]):
        flash("Formulario incompleto. Por favor, selecciona todos los puntos.", "danger")
        return redirect(url_for('index'))

    conn = None
    cursor = None
    try:
        # 3. Conversión a números y cálculo del total
        c_id = int(c_id)
        b = int(v_belleza)
        s = int(v_simpatia)
        e = int(v_elegancia)
        total = b + s + e
        
        juez_id = session['juez_id']

        conn = get_db_connection()
        cursor = conn.cursor()

        # 4. Ajustamos el SQL con ON DUPLICATE KEY UPDATE
        # Si la combinación (juez_id, candidata_id) ya existe, se ejecutan los UPDATE correspondientes
        sql = """
            INSERT INTO votos 
            (juez_id, candidata_id, cat_belleza, cat_simpatia, cat_elegancia, total_puntos) 
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                cat_belleza = VALUES(cat_belleza),
                cat_simpatia = VALUES(cat_simpatia),
                cat_elegancia = VALUES(cat_elegancia),
                total_puntos = VALUES(total_puntos);
        """
        
        cursor.execute(sql, (juez_id, c_id, b, s, e, total))
        conn.commit()
        
        # Personalizamos el mensaje flash dependiendo de si se creó o se editó
        if cursor.rowcount == 2:
            flash("¡Calificación modificada con éxito!", "success")
        else:
            flash("¡Voto registrado con éxito!", "success")

    except mysql.connector.Error as err:
        if conn: conn.rollback() # Limpiamos cualquier estado pendiente en la transacción
        print(f"Error en DB: {err}")
        flash("Error al procesar el voto en la base de datos.", "danger")
    
    finally:
        # Cerramos correctamente en orden inverso para evitar el "Commands out of sync"
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
        # Mantenemos el buffered=True por seguridad de hilos
        cursor = conn.cursor(dictionary=True, buffered=True)
        
        # Guardamos las variables de control al principio
        genero_actual = obtener_tipo_evento()
        es_administrador = session.get('es_admin')

        # 1. Ranking con detección de empates
        sql_ranking = """
            SELECT c.nombre, 
                   IFNULL(SUM(v.cat_belleza), 0) as belleza, 
                   IFNULL(SUM(v.cat_simpatia), 0) as simpatia, 
                   IFNULL(SUM(v.cat_elegancia), 0) as elegancia,
                   (IFNULL(SUM(v.cat_belleza), 0) + 
                    IFNULL(SUM(v.cat_simpatia), 0) + 
                    IFNULL(SUM(v.cat_elegancia), 0)) as total 
            FROM candidatas c 
            LEFT JOIN votos v ON c.id = v.candidata_id 
            WHERE c.genero = %s
            GROUP BY c.id, c.nombre 
            ORDER BY total DESC, elegancia DESC, belleza DESC, simpatia DESC
        """
        cursor.execute(sql_ranking, (genero_actual,))
        ranking_raw = cursor.fetchall()

        # --- CORRECCIÓN DE ACENTOS EN RANKING ---
        ranking = []
        for r in ranking_raw:
            candidata_r = dict(r)
            try:
                candidata_r['nombre'] = r['nombre'].encode('latin1').decode('utf-8')
            except:
                pass
            ranking.append(candidata_r)

        # --- LÓGICA DE EMPATE DETALLADA ---
        hay_empate = False
        categorias_empatadas = []

        if len(ranking) > 1:
            primer_puesto = ranking[0]
            segundo_puesto = ranking[1]

            if primer_puesto['total'] == segundo_puesto['total'] and primer_puesto['total'] > 0:
                hay_empate = True
                if primer_puesto['belleza'] == segundo_puesto['belleza']:
                    categorias_empatadas.append("Belleza")
                if primer_puesto['simpatia'] == segundo_puesto['simpatia']:
                    categorias_empatadas.append("Simpatía")
                if primer_puesto['elegancia'] == segundo_puesto['elegancia']:
                    categorias_empatadas.append("Elegancia")

        # Solo el admin ve la participación detallada
        participacion = []
        if es_administrador:
            # 💡 TRUCO DE SEGURIDAD: Vaciamos cualquier basura del cursor antes de otra consulta larga
            try: cursor.fetchall() 
            except: pass
            
            cursor.execute("""
                SELECT j.nombre as juez, c.nombre as candidata 
                FROM votos v 
                JOIN jueces j ON v.juez_id = j.id 
                JOIN candidatas c ON v.candidata_id = c.id
                ORDER BY v.id DESC
            """)
            participacion = cursor.fetchall()
        
        # 💡 TRUCO DE SEGURIDAD: Vaciamos nuevamente antes del monitor
        try: cursor.fetchall() 
        except: pass

        # --- MONITOR DE ACTIVIDAD DE JUECES EN TIEMPO REAL ---
        # 1. Averiguamos cuántos candidatos hay del género actual
        cursor.execute("SELECT COUNT(1) as total FROM candidatas WHERE genero = %s", (genero_actual,))
        total_candidatas_genero = cursor.fetchone()['total']
        
        # 💡 Limpieza rápida para el siguiente SELECT
        try: cursor.fetchall() 
        except: pass

        # 2. Consultamos cuántos votos reales lleva cada juez (EXCLUYENDO AL ADMIN)
        query_monitoreo = """
            SELECT 
                j.id as juez_id,
                j.nombre as juez_nombre,
                COUNT(v.id) as votos_emitidos
            FROM jueces j
            LEFT JOIN votos v ON j.id = v.juez_id 
            LEFT JOIN candidatas c ON v.candidata_id = c.id AND c.genero = %s
            WHERE j.nombre != 'Admin'
            GROUP BY j.id, j.nombre
            ORDER BY votos_emitidos ASC, j.nombre ASC;
        """
        cursor.execute(query_monitoreo, (genero_actual,))
        jueces_raw = cursor.fetchall()
        
        # 3. Procesamos los datos y calculamos porcentajes en memoria
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

        # 💡 Limpieza final antes del último select de config
        try: cursor.fetchall() 
        except: pass

        # LEER EL ESTADO ACTUAL DE LA CONFIGURACIÓN
        cursor.execute("SELECT valor FROM configuracion WHERE nombre_config = 'resultados_visibles'")
        config = cursor.fetchone()
        habilitado = (config['valor'] == '1') if config else False

        # Almacenamos el estado de resultados antes de renderizar
        resultados_hab = obtener_estado_resultados()

        return render_template('resultados.html', 
                               ranking=ranking,
                               participacion=participacion,
                               genero_evento=genero_actual,
                               resultados_habilitados=resultados_hab,
                               es_admin=es_administrador,
                               juez=session['juez_nombre'],
                               hay_empate=hay_empate,
                               estado_jueces=estado_jueces,
                               todos_terminaron=todos_terminaron)

    except mysql.connector.Error as err:
        print(f"Error en la base de datos: {err}")
        return f"Error técnico: {err}", 500
        
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    
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
    
