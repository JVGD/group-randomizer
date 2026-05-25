import streamlit as st
import random
from streamlit_gsheets import GSheetsConnection

def randomize_groups(units, num_groups):
    """
    Randomizes a list of units (singles or couples) into a specified number of groups.
    Attempts to keep the total number of people per group as even as possible.
    """
    random.shuffle(units)
    
    # Initialize groups
    groups = [[] for _ in range(num_groups)]
    group_people_counts = [0] * num_groups
    
    # Distribute units into groups using a greedy approach (smallest group first)
    for unit in units:
        # Find the index of the group with the fewest people
        min_idx = group_people_counts.index(min(group_people_counts))
        groups[min_idx].append(unit)
        group_people_counts[min_idx] += len(unit)
    
    return groups

def main():
    st.set_page_config(page_title="Grupos Aleatorios", page_icon="🎲")

    # Password Protection
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔐 Acceso Restringido")
        password_input = st.text_input("Introduce la contraseña para continuar:", type="password")
        if st.button("Entrar"):
            if password_input == st.secrets.get("access", {}).get("password"):
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta 😕")
        return

    st.title("🎲 Grupos Aleatorios")
    st.write("Introduce una lista de nombres y el número de grupos para aleatorizarlos.")
    
    st.info("💡 **Truco para parejas:** Si quieres que dos personas vayan siempre juntas, escríbelas en la misma línea separadas por ' y ' (ej: *Javier y Ana Maria*).")

    # Load default names from Google Sheets
    default_names = ""
    
    # Try Google Sheets (Public Link method)
    try:
        with st.spinner("Descargando data desde google sheets..."):
            conn = st.connection("gsheets", type=GSheetsConnection)
            # Read the sheet (requires "Anyone with the link" in Google Sheets)
            df = conn.read(ttl="10m") 
            if df is not None and not df.empty:
                # Get the first column and join names
                lines = df.iloc[:, 0].dropna().astype(str).tolist()
                default_names = "\n".join(lines)
            else:
                st.warning("⚠️ La hoja de cálculo está vacía o no se pudo leer.")
    except Exception as e:
        # If it fails, we show a hint about the configuration
        st.sidebar.warning("📌 Google Sheets no configurado. Para cargar la lista automáticamente, configura `.streamlit/secrets.toml`.")
        # Optionally log the error for debugging if needed: 
        # st.sidebar.error(f"Error: {e}")

    # Input names
    names_input = st.text_area(
        "Introduce los nombres (uno por línea):",
        value=default_names,
        placeholder="Javier y Ana María\nJuan B\nMiguel Marquez\nJesus y Paloma",
        height=300
    )
    
    # Number of groups
    num_groups = st.number_input(
        "Número de grupos:",
        min_value=1,
        value=2,
        step=1
    )

    if st.button("Aleatorizar Grupos", type="primary"):
        # Process input lines into units
        lines = [line.strip() for line in names_input.split("\n") if line.strip()]
        
        units = []
        for line in lines:
            if " y " in line:
                # It's a couple
                names = [n.strip() for n in line.split(" y ")]
                units.append(names)
            else:
                # It's a single
                units.append([line])
        
        if not units:
            st.error("Por favor, introduce al menos un nombre.")
            return
            
        total_people = sum(len(u) for u in units)
        if num_groups > total_people:
            st.warning(f"Nota: Has solicitado {num_groups} grupos, pero solo hay {total_people} personas. Algunos grupos estarán vacíos.")
        
        # Randomize
        groups = randomize_groups(units, num_groups)
        
        # Display results
        st.header("Grupos Resultantes")
        
        # Calculate grid layout
        cols_per_row = 3
        for i in range(0, len(groups), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                group_idx = i + j
                if group_idx < len(groups):
                    with cols[j]:
                        people_in_group = sum(len(u) for u in groups[group_idx])
                        st.subheader(f"Grupo {group_idx + 1} ({people_in_group} pers.)")
                        if groups[group_idx]:
                            for unit in groups[group_idx]:
                                if len(unit) > 1:
                                    st.write(f"- {' y '.join(unit)}")
                                else:
                                    st.write(f"- {unit[0]}")
                        else:
                            st.write("*Vacío*")

        # Export section for WhatsApp
        st.divider()
        st.header("📤 Exportar")
        st.info("💡 **Pista:** Formato optimizado para copiar y pegar directamente en WhatsApp.")
        
        whatsapp_text = "🎲 *Resultado de los Grupos*\n\n"
        for i, group in enumerate(groups):
            people_in_group = sum(len(u) for u in group)
            whatsapp_text += f"*Grupo {i + 1}* ({people_in_group} pers.)\n"
            if group:
                for unit in group:
                    if len(unit) > 1:
                        whatsapp_text += f"• {' y '.join(unit)}\n"
                    else:
                        whatsapp_text += f"• {unit[0]}\n"
            else:
                whatsapp_text += "_Vacío_\n"
            whatsapp_text += "\n"
        
        st.text_area("Copia el texto aquí:", value=whatsapp_text, height=250)

if __name__ == "__main__":
    main()
