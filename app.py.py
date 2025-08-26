import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import time

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
conn = sqlite3.connect("cheques.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS cheques (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_recepcion TEXT,
    fecha_emision TEXT,
    fecha_cobro TEXT,
    cliente TEXT,
    numero_cheque TEXT,
    banco TEXT,
    importe REAL,
    estado TEXT, 
    destino TEXT 
)
""")
conn.commit()

# --- FUNCIONES AUXILIARES ---
def formatear_fecha_db(fecha_obj):
    """Convierte objeto date a string YYYY-MM-DD para guardar en DB"""
    if fecha_obj:
        return fecha_obj.strftime("%Y-%m-%d")
    return None

def mostrar_fecha(fecha_str):
    """Convierte YYYY-MM-DD desde DB a DD/MM/YYYY para mostrar"""
    try:
        if fecha_str:
            return datetime.strptime(fecha_str, "%Y-%m-%d").strftime("%d/%m/%Y")
        return ""
    except (ValueError, TypeError):
        return fecha_str

def format_currency_es(amount):
    """
    Formatea un número a formato de moneda español (separador de miles con punto, decimal con coma).
    Ej: 1234567.89 -> "$1.234.567,89"
    """
    if not isinstance(amount, (int, float)):
        return amount
    
    formatted = f"{amount:,.2f}"
    
    parts = formatted.split('.')
    integer_part = parts[0].replace(',', '.')
    decimal_part = parts[1] if len(parts) > 1 else "00"
    
    return f"${integer_part},{decimal_part}"

@st.cache_data
def load_clients(file_path="clientes.xlsx"):
    """
    Carga una lista de clientes desde un archivo Excel.
    El archivo Excel debe tener una columna llamada 'Cliente'.
    """
    try:
        df_clients = pd.read_excel(file_path)
        if 'Cliente' in df_clients.columns:
            return sorted(df_clients['Cliente'].dropna().unique().tolist())
        else:
            st.warning(f"El archivo '{file_path}' no contiene una columna 'Cliente'. Asegúrate de que exista y tenga ese nombre.")
            return []
    except FileNotFoundError:
        st.warning(f"Archivo de clientes '{file_path}' no encontrado. Crea un archivo Excel con una columna 'Cliente' para cargar clientes existentes, o agrega nuevos clientes directamente.")
        return []
    except Exception as e:
        st.error(f"Error al cargar clientes desde Excel: {e}")
        return []

@st.cache_data
def load_banks(file_path="bancos.xlsx"):
    """
    Carga una lista de bancos desde un archivo Excel.
    El archivo Excel debe tener al menos las columnas 'Código' y 'Banco'.
    """
    try:
        df_banks = pd.read_excel(file_path)
        if 'Código' in df_banks.columns and 'Banco' in df_banks.columns:
            banks_data = df_banks[['Código', 'Banco']].drop_duplicates().sort_values(by='Código')
            return [(str(row['Código']), row['Banco']) for index, row in banks_data.iterrows()]
        else:
            st.warning(f"El archivo '{file_path}' no contiene las columnas 'Código' y/o 'Banco'. Asegúrate de que existan y tengan esos nombres.")
            return []
    except FileNotFoundError:
        st.warning(f"Archivo de bancos '{file_path}' no encontrado. Crea un archivo Excel con columnas 'Código' y 'Banco' para cargar bancos existentes, o agrega nuevos bancos directamente.")
        return []
    except Exception as e:
        st.error(f"Error al cargar bancos desde Excel: {e}")
        return []

@st.cache_data
def load_providers(file_path="proveedores.xlsx"):
    """
    Carga una lista de proveedores desde un archivo Excel.
    El archivo Excel debe tener una columna llamada 'Proveedor'.
    """
    try:
        df_providers = pd.read_excel(file_path)
        if 'Proveedor' in df_providers.columns:
            return sorted(df_providers['Proveedor'].dropna().unique().tolist())
        else:
            st.warning(f"El archivo '{file_path}' no contiene una columna 'Proveedor'. Asegúrate de que exista y tenga ese nombre.")
            return []
    except FileNotFoundError:
        st.warning(f"Archivo de proveedores '{file_path}' no encontrado. Crea un archivo Excel con una columna 'Proveedor' para cargar proveedores existentes, o agrega nuevos proveedores directamente.")
        return []
    except Exception as e:
        st.error(f"Error al cargar proveedores desde Excel: {e}")
        return []

@st.cache_data
def load_accounts(file_path="cuentas.xlsx"):
    """
    Carga una lista de cuentas bancarias desde un archivo Excel.
    El archivo Excel debe tener una columna llamada 'Cuenta'.
    """
    try:
        df_accounts = pd.read_excel(file_path)
        if 'Cuenta' in df_accounts.columns:
            return sorted(df_accounts['Cuenta'].dropna().unique().tolist())
        else:
            st.warning(f"El archivo '{file_path}' no contiene una columna 'Cuenta'. Asegúrate de que exista y tenga ese nombre.")
            return []
    except FileNotFoundError:
        st.warning(f"Archivo de cuentas '{file_path}' no encontrado. Crea un archivo Excel con una columna 'Cuenta' para cargar cuentas existentes, o agrega nuevas cuentas directamente.")
        return []
    except Exception as e:
        st.error(f"Error al cargar cuentas desde Excel: {e}")
        return []

# --- APP ---
st.set_page_config(page_title="Gestión de Cheques", page_icon="📑", layout="wide")

# --- LOGIN FUNCIONALITY ---
# Credenciales actualizadas
VALID_USERNAME = "administracion"
VALID_PASSWORD = "Virginia123"

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'login_error' not in st.session_state:
    st.session_state.login_error = ""

def login_form():
    st.sidebar.empty() # Clear sidebar content
    # Clear main content by only showing login form
    st.title("📑 Gestión de Cheques")
    st.markdown("---")
    st.subheader("🔑 Iniciar Sesión")
    
    with st.form("login_form"):
        username = st.text_input("Usuario", key="login_username")
        password = st.text_input("Contraseña", type="password", key="login_password")
        login_button = st.form_submit_button("Iniciar Sesión")

        if login_button:
            if username == VALID_USERNAME and password == VALID_PASSWORD:
                st.session_state.logged_in = True
                st.session_state.login_error = ""
                st.success("¡Sesión iniciada correctamente!")
                time.sleep(1)
                st.rerun()
            else:
                st.session_state.login_error = "Credenciales incorrectas. Por favor, inténtelo de nuevo."
                st.error(st.session_state.login_error)
    st.markdown("---")

if not st.session_state.logged_in:
    login_form()
    st.stop() # Stop further execution if not logged in

# --- MAIN APP CONTENT (ONLY IF LOGGED IN) ---
# Título principal y botón de cerrar sesión
col_title, col_logout = st.columns([0.8, 0.2])
with col_title:
    st.title("📑 Gestión de Cheques")
with col_logout:
    st.markdown("<div style='text-align: right; padding-top: 20px;'>", unsafe_allow_html=True)
    if st.button("🚪 Cerrar Sesión", key="btn_logout_main"):
        st.session_state.logged_in = False
        st.session_state.menu_choice = "Listado de Cheques" # Reset menu choice on logout
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# Inicializar el estado de la elección del menú
if 'menu_choice' not in st.session_state:
    st.session_state.menu_choice = "Listado de Cheques"
if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = False
if 'select_all_cheques' not in st.session_state:
    st.session_state.select_all_cheques = False

st.sidebar.title("Menú de Navegación")
st.sidebar.markdown(
    """
    <style>
    .stSidebar .stButton > button {
        font-size: 14px;
        padding: 5px 10px;
        height: auto;
        line-height: 1.2;
    }
    .stSidebar .stText {
        font-size: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if st.sidebar.button("➕ Ingresar Cheque", key="btn_ingresar"):
    st.session_state.menu_choice = "Ingresar Cheque"
if st.sidebar.button("📋 Listado de Cheques", key="btn_listado"):
    st.session_state.menu_choice = "Listado de Cheques"

choice = st.session_state.menu_choice

# --- INGRESAR CHEQUE ---
if choice == "Ingresar Cheque":
    st.subheader("➕ Ingresar un nuevo cheque")
    st.divider()

    with st.form("form_ingresar_cheque", clear_on_submit=True):
        col_fecha_recepcion, col_fecha_emision, col_fecha_cobro = st.columns(3)
        with col_fecha_recepcion:
            fecha_recepcion = st.date_input("Fecha de recepción", format="DD/MM/YYYY", key="fecha_recepcion_input")
        with col_fecha_emision:
            fecha_emision = st.date_input("Fecha de emisión", format="DD/MM/YYYY", key="fecha_emision_input")
        with col_fecha_cobro:
            fecha_cobro = st.date_input("Fecha de cobro", format="DD/MM/YYYY", key="fecha_cobro_input")

        # Cliente
        client_options = load_clients()
        display_client_options = ["-- Seleccionar un cliente --", "Agregar nuevo cliente..."] + client_options
        selected_client_from_list = st.selectbox(
            "Cliente",
            options=display_client_options,
            key="cliente_selectbox",
            index=0
        )
        cliente_final = ""
        if selected_client_from_list == "Agregar nuevo cliente...":
            new_client_name = st.text_input("Ingrese el nombre del nuevo cliente", key="new_client_input")
            cliente_final = new_client_name
        elif selected_client_from_list != "-- Seleccionar un cliente --":
            cliente_final = selected_client_from_list

        # Banco
        bank_data = load_banks()
        bank_display_options = ["-- Seleccionar un banco --", "Agregar nuevo banco..."] + [f"{code} - {name}" for code, name in bank_data]
        
        selected_bank_from_list = st.selectbox(
            "Banco",
            options=bank_display_options,
            key="banco_selectbox",
            index=0
        )

        banco_final = ""
        if selected_bank_from_list == "Agregar nuevo banco...":
            new_bank_name = st.text_input("Ingrese el nombre del nuevo banco", key="new_bank_input")
            banco_final = new_bank_name
        elif selected_bank_from_list != "-- Seleccionar un banco --":
            banco_final = selected_bank_from_list.split(' - ', 1)[1] if ' - ' in selected_bank_from_list else selected_bank_from_list

        col_num_cheque, col_importe = st.columns(2)
        with col_num_cheque:
            numero_cheque = st.text_input("Número de cheque", key="numero_cheque_input")
        with col_importe:
            importe = st.number_input("Importe", min_value=0.0, format="%.2f", key="importe_input")
        
        estado = "Pendiente"
        destino = ""

        submitted = st.form_submit_button("➕ Guardar cheque")
        if submitted:
            if not cliente_final:
                st.error("❌ Por favor, seleccione o ingrese un cliente.")
            elif not banco_final:
                st.error("❌ Por favor, seleccione o ingrese un banco.")
            elif not all([fecha_recepcion, fecha_emision, fecha_cobro, numero_cheque, importe]):
                st.error("❌ Por favor, complete todos los campos para guardar el cheque.")
            else:
                try:
                    c.execute("""
                    INSERT INTO cheques 
                    (fecha_recepcion, fecha_emision, fecha_cobro, cliente, numero_cheque, banco, importe, estado, destino) 
                    VALUES (?,?,?,?,?,?,?,?,?)
                    """, (
                        formatear_fecha_db(fecha_recepcion),
                        formatear_fecha_db(fecha_emision),
                        formatear_fecha_db(fecha_cobro),
                        cliente_final,
                        numero_cheque, banco_final, importe, estado, destino
                    ))
                    conn.commit()
                    st.success("✅ Cheque guardado correctamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"⚠️ Error al guardar el cheque: {e}")

# --- LISTADO DE CHEQUES ---
elif choice == "Listado de Cheques":
    st.subheader("📋 Listado de cheques")
    st.divider()

    df = pd.read_sql("SELECT * FROM cheques", conn)

    if not df.empty:
        df["fecha_recepcion"] = df["fecha_recepcion"].apply(mostrar_fecha)
        df["fecha_emision"] = df["fecha_emision"].apply(mostrar_fecha)
        df["fecha_cobro"] = df["fecha_cobro"].apply(mostrar_fecha)

        # --- FILTROS ---
        st.sidebar.subheader("🔍 Filtros")
        
        if st.sidebar.button("🧹 Limpiar Filtros", key="btn_clear_filters"):
            st.session_state['filtro_cliente'] = ""
            st.session_state['filtro_banco'] = ""
            st.session_state['filtro_numero_cheque'] = ""
            st.session_state['filtro_estado'] = "Todos"
            st.session_state['filtro_fecha_inicio'] = None
            st.session_state['filtro_fecha_fin'] = None
            st.rerun()

        cliente_filtro = st.sidebar.text_input("Cliente", value=st.session_state.get('filtro_cliente', ''), key="filtro_cliente")
        banco_filtro = st.sidebar.text_input("Banco", value=st.session_state.get('filtro_banco', ''), key="filtro_banco")
        numero_cheque_filtro = st.sidebar.text_input("Número de Cheque", value=st.session_state.get('filtro_numero_cheque', ''), key="filtro_numero_cheque")
        
        estado_default_index = 0
        if st.session_state.get('filtro_estado') in ["Todos"] + df["estado"].unique().tolist():
            estado_default_index = (["Todos"] + df["estado"].unique().tolist()).index(st.session_state['filtro_estado'])

        estado_filtro = st.sidebar.selectbox("Estado", ["Todos"] + df["estado"].unique().tolist(), index=estado_default_index, key="filtro_estado")
        
        col_fecha_inicio, col_fecha_fin = st.sidebar.columns(2)
        with col_fecha_inicio:
            fecha_inicio_filtro = st.date_input("Desde Fecha de Cobro", value=st.session_state.get('filtro_fecha_inicio', None), key="filtro_fecha_inicio")
        with col_fecha_fin:
            fecha_fin_filtro = st.date_input("Hasta Fecha de Cobro", value=st.session_state.get('filtro_fecha_fin', None), key="filtro_fecha_fin")

        # Aplicar filtros
        df_filtered = df.copy()

        if cliente_filtro:
            df_filtered = df_filtered[df_filtered["cliente"].str.contains(cliente_filtro, case=False, na=False)]
        if banco_filtro:
            df_filtered = df_filtered[df_filtered["banco"].str.contains(banco_filtro, case=False, na=False)]
        if numero_cheque_filtro:
            df_filtered = df_filtered[df_filtered["numero_cheque"].str.contains(numero_cheque_filtro, case=False, na=False)]
        if estado_filtro != "Todos":
            df_filtered = df_filtered[df_filtered["estado"] == estado_filtro]

        if fecha_inicio_filtro and fecha_fin_filtro:
            df_filtered["fecha_cobro_dt"] = pd.to_datetime(df_filtered["fecha_cobro"], format="%d/%m/%Y", errors="coerce")
            df_filtered = df_filtered[(df_filtered["fecha_cobro_dt"] >= pd.to_datetime(fecha_inicio_filtro)) &
                                    (df_filtered["fecha_cobro_dt"] <= pd.to_datetime(fecha_fin_filtro))]
            df_filtered.drop(columns=["fecha_cobro_dt"], inplace=True)
            
        # --- SELECT ALL CHECKBOX LOGIC ---
        col_select_all, _ = st.columns([0.2, 0.8])
        with col_select_all:
            st.session_state.select_all_cheques = st.checkbox(
                "Tildar todos los cheques visibles", # Texto actualizado
                value=st.session_state.select_all_cheques,
                key="select_all_checkbox_header"
            )

        # Apply "select all" state to the 'Seleccionar' column before data_editor
        df_to_display = df_filtered.copy()
        if st.session_state.select_all_cheques:
            df_to_display['Seleccionar'] = True # Selecciona todos los cheques visibles
        else:
            df_to_display['Seleccionar'] = False

        # Crear una columna formateada para la visualización del importe
        df_to_display['Importe Formateado'] = df_to_display['importe'].apply(format_currency_es)

        columnas_display = ["Seleccionar", "id", "numero_cheque", "cliente", "banco", "Importe Formateado",
                            "fecha_recepcion", "fecha_emision", "fecha_cobro",
                            "estado", "destino"]
        
        edited_df = st.data_editor(
            df_to_display[columnas_display],
            column_config={
                "Seleccionar": st.column_config.CheckboxColumn(
                    "Seleccionar",
                    help="Marca los cheques para realizar acciones",
                    default=False,
                ),
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "numero_cheque": st.column_config.Column("Número Cheque", disabled=True),
                "cliente": st.column_config.Column("Cliente", disabled=True),
                "banco": st.column_config.Column("Banco", disabled=True),
                "Importe Formateado": st.column_config.TextColumn(
                    "Importe",
                    disabled=True, 
                ),
                "fecha_recepcion": st.column_config.Column("Fecha Recepción", disabled=True),
                "fecha_emision": st.column_config.Column("Fecha Emisión", disabled=True),
                "fecha_cobro": st.column_config.Column("Fecha Cobro", disabled=True),
                "estado": st.column_config.Column("Estado", disabled=True),
                "destino": st.column_config.Column("Destino", disabled=True),
            },
            hide_index=True,
            use_container_width=True,
            key="cheque_data_editor"
        )

        # --- SECCIÓN DE TOTALIZADOR Y DESCARGA ---
        seleccionados = edited_df[edited_df["Seleccionar"] == True]["id"].tolist()
        
        if seleccionados:
            df_selected_cheques = df_filtered[df_filtered['id'].isin(seleccionados)]
            total_importes_seleccionados = df_selected_cheques["importe"].sum()
            st.divider()
            st.markdown(f"**Total de importes seleccionados:** **{format_currency_es(total_importes_seleccionados)}**")
        else:
            st.divider()
            st.info("ℹ️ No hay cheques seleccionados. Tilda los cheques en la tabla para ver el total.")

        st.markdown("")
        if not df_filtered.empty:
            output = io.BytesIO()
            df_to_excel = df_filtered.drop(columns=['Seleccionar', 'Importe Formateado'], errors='ignore')
            # Para exportar a Excel y que sea interpretable como número,
            # lo mejor es quitar los caracteres de moneda y dejar el número.
            # Excel puede aplicar su propio formato de moneda después.
            df_to_excel['importe'] = df_to_excel['importe'].apply(lambda x: str(x).replace('.', '') if isinstance(x, (int, float)) else x) # Quitar separadores de miles para Excel
            df_to_excel.to_excel(output, index=False, sheet_name='Cheques')
            output.seek(0)

            st.download_button(
                label="📊 Descargar Listado en Excel",
                data=output.getvalue(),
                file_name=f"listado_cheques_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Descarga la tabla visible de cheques a un archivo Excel."
            )
        # --- FIN SECCIÓN DE TOTALIZADOR Y DESCARGA ---

        if seleccionados:
            st.divider()
            st.subheader("Acciones con cheques seleccionados")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("### 💰 Depositar Cheques")
                account_options = load_accounts()
                display_account_options = ["-- Seleccionar una cuenta --", "Agregar nueva cuenta..."] + account_options

                selected_account_from_list = st.selectbox(
                    "Seleccione o ingrese una cuenta bancaria destino:",
                    options=display_account_options,
                    key="cuenta_deposito_selectbox"
                )

                cuenta_final = ""
                if selected_account_from_list == "Agregar nueva cuenta...":
                    new_account_name = st.text_input("Ingrese el número/nombre de la nueva cuenta", key="new_account_input")
                    cuenta_final = new_account_name
                elif selected_account_from_list != "-- Seleccionar una cuenta --":
                    cuenta_final = selected_account_from_list

                if st.button("Confirmar Depósito", key="btn_confirmar_deposito"):
                    if not cuenta_final:
                        st.warning("⚠️ Por favor, seleccione o ingrese una cuenta bancaria destino.")
                    else:
                        if seleccionados:
                            for cheque_id in seleccionados:
                                c.execute("UPDATE cheques SET estado=?, destino=? WHERE id=?",
                                          ("Depositado", cuenta_final, cheque_id))
                            conn.commit()
                            st.success(f"✅ Se depositaron {len(seleccionados)} cheques en {cuenta_final}.")
                            st.rerun() 
                        else:
                            st.warning("⚠️ Selecciona al menos un cheque para depositar.")

            with col2:
                st.markdown("### 📤 Entregar Cheques")
                provider_options = load_providers()
                display_provider_options = ["-- Seleccionar un proveedor --", "Agregar nuevo proveedor..."] + provider_options

                selected_provider_from_list = st.selectbox(
                    "Seleccione o ingrese un proveedor receptor:",
                    options=display_provider_options,
                    key="proveedor_selectbox"
                )

                proveedor_final = ""
                if selected_provider_from_list == "Agregar nuevo proveedor...":
                    new_provider_name = st.text_input("Ingrese el nombre del nuevo proveedor", key="new_proveedor_input")
                    proveedor_final = new_provider_name
                elif selected_provider_from_list != "-- Seleccionar un proveedor --":
                    proveedor_final = selected_provider_from_list

                if st.button("Confirmar Entrega", key="btn_confirmar_entrega"):
                    if not proveedor_final:
                        st.warning("⚠️ Por favor, seleccione o ingrese un proveedor receptor.")
                    else:
                        if seleccionados:
                            for cheque_id in seleccionados:
                                c.execute("UPDATE cheques SET estado=?, destino=? WHERE id=?",
                                          ("Entregado", proveedor_final, cheque_id))
                            conn.commit()
                            st.success(f"✅ Se entregaron {len(seleccionados)} cheques a {proveedor_final}.")
                            st.rerun()
                        else:
                            st.warning("⚠️ Selecciona al menos un cheque para entregar.")
            
            with col3:
                st.markdown("### 🗑️ Eliminar Cheques")
                st.markdown(" ")
                if not st.session_state.confirm_delete:
                    if st.button("🗑️ Eliminar Seleccionados", key="btn_eliminar_seleccionados"):
                        if seleccionados:
                            st.session_state.confirm_delete = True
                            st.warning(f"⚠️ ¿Estás seguro de que deseas eliminar {len(seleccionados)} cheques? Esta acción es irreversible.")
                        else:
                            st.warning("⚠️ Selecciona al menos un cheque para eliminar.")
                
                if st.session_state.confirm_delete:
                    col_confirm_yes, col_confirm_no = st.columns(2)
                    with col_confirm_yes:
                        if st.button("✅ Sí, eliminar definitivamente", key="btn_confirm_delete_yes"):
                            if seleccionados:
                                try:
                                    for cheque_id in seleccionados:
                                        c.execute("DELETE FROM cheques WHERE id=?", (cheque_id,))
                                    conn.commit()
                                    st.success(f"🗑️ Se eliminaron {len(seleccionados)} cheques correctamente.")
                                    st.session_state.confirm_delete = False
                                    st.rerun() 
                                except Exception as e:
                                    st.error(f"⚠️ Error al eliminar cheques: {e}")
                            else:
                                st.error("❌ No hay cheques seleccionados para eliminar.")
                    with col_confirm_no:
                        if st.button("❌ Cancelar", key="btn_confirm_delete_no"):
                            st.session_state.confirm_delete = False
                            st.info("Operación de eliminación cancelada.")
                            st.rerun()
            
            # --- SECCIÓN DE HISTORIAL DE CHEQUES (SE MUESTRA DIRECTAMENTE) ---
            st.divider()
            st.subheader("📜 Historial de Cheques Seleccionados")
            
            st.session_state.history_cheques_data = df_filtered[df_filtered['id'].isin(seleccionados)].to_dict('records')

            for cheque_data in st.session_state.history_cheques_data:
                expand_title = f"**Cheque Nº {cheque_data.get('numero_cheque', 'N/A')} - {cheque_data.get('cliente', 'N/A')}**"
                with st.expander(expand_title):
                    for key, value in cheque_data.items():
                        if key not in ['Seleccionar', 'Importe Formateado']:
                            if key == 'importe':
                                st.write(f"**{key.replace('_', ' ').title()}:** {format_currency_es(value)}")
                            else:
                                st.write(f"**{key.replace('_', ' ').title()}:** {value}")

        else:
            st.info("ℹ️ Selecciona cheques en la tabla para realizar acciones.")

    else:
        st.info("ℹ️ No hay cheques cargados todavía.")




