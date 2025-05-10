import streamlit as st
import pandas as pd
import folium
import numpy as np
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import plotly.express as px

# Cargar datos
torrevieja_property = pd.read_csv('Torrevieja\\Spain-torrevieja_Property_Extended_Match_2023-11-23\\Spain-torrevieja_Property_Extended_Match_2023-11-23.csv')
torrevieja_daily = pd.read_csv('Torrevieja\\Spain-torrevieja_Daily_Match_2023-11-23\\Spain-torrevieja_Daily_Match_2023-11-23.csv')
torrevieja_monthly = pd.read_csv('Torrevieja\\Spain-torrevieja_Monthly_Match_2023-11-23\\Spain-torrevieja_Monthly_Match_2023-11-23.csv')

# Conversión de fecha y columna mes
torrevieja_daily['Date'] = pd.to_datetime(torrevieja_daily['Date'], errors='coerce')
torrevieja_daily['mes'] = torrevieja_daily['Date'].dt.to_period('M').astype(str)

# Limitar número de propiedades para mejorar rendimiento
torrevieja_daily = torrevieja_daily[torrevieja_daily['Property ID'].isin(torrevieja_daily['Property ID'].unique()[:100])]

# Unir coordenadas
torrevieja_daily = torrevieja_daily.merge(
    torrevieja_property[['Property ID', 'Latitude', 'Longitude']],
    on='Property ID',
    how='left'
)

# Streamlit config
st.set_page_config(layout="wide")
# st.title("Mapa interactivo de apartamentos turísticos en Torrevieja")

# Selección de fecha
fecha_seleccionada = st.date_input("Selecciona una fecha:", value=torrevieja_daily["Date"].min().date())

# Selección de tipos de estado
statuses = ['A', 'B', 'R']
status_labels = {'A': 'Disponible', 'B': 'Bloqueado', 'R': 'Reservado'}
selected_statuses = st.multiselect(
    "Filtrar por tipo de estado:",
    options=statuses,
    format_func=lambda x: status_labels[x],
    default=statuses
)

# Filtrar por fecha y estado
df_filtrado = torrevieja_daily[
    (torrevieja_daily['Date'].dt.date == fecha_seleccionada) &
    (torrevieja_daily['Status'].isin(selected_statuses))
]

# Crear mapa
m = folium.Map(location=[37.978, -0.682], zoom_start=13)
color_map = {'A': 'green', 'B': 'orange', 'R': 'red'}

# Añadir marcadores
for _, row in df_filtrado.iterrows():
    df_info = torrevieja_property[torrevieja_property['Property ID'] == row['Property ID']].iloc[0]
    popup_text = ""
    if pd.notna(df_info['Overall Rating']):
        popup_text += f"<b>Rating:</b> {df_info['Overall Rating']}<br>"
    if pd.notna(df_info['Number of Reviews']):
        popup_text += f"<b>Reseñas:</b> {int(df_info['Number of Reviews'])}<br>"
    if pd.notna(row['Price (Native)']):
        popup_text += f"<b>Precio:</b> {round(row['Price (Native)'], 2)}€/noche"

    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        tooltip=row['Property ID'],
        popup=popup_text,
        icon=folium.Icon(color=color_map.get(row['Status'], 'gray'), icon='home', prefix='fa')
    ).add_to(m)

# Mostrar mapa
map_data = st_folium(m, width=1000, height=600)

# Extraer clic
clicked = map_data.get("last_object_clicked_tooltip")

if clicked:
    apto_data = torrevieja_property[torrevieja_property['Property ID'] == clicked].iloc[0]
    st.sidebar.title(f"{apto_data['Listing Title'].capitalize()}")
    st.sidebar.subheader(f"{apto_data['Property Type'].capitalize()}")
    image_url = apto_data['Listing Main Image URL']
    if pd.notna(image_url):
        st.sidebar.image(image_url, caption="Foto del apartamento", use_container_width=True)

    url = apto_data['Listing URL']
    if 'airbnb' in url:
        sitio_web = 'Airbnb'
        icon_url = 'https://upload.wikimedia.org/wikipedia/commons/6/69/Airbnb_Logo_Bélo.svg'
    elif 'vrbo' in url:
        sitio_web = 'Vrbo'
        icon_url = 'https://commons.wikimedia.org/wiki/File:Vrbo.svg'
    else:
        sitio_web = 'sitio web'
        icon_url = 'https://commons.wikimedia.org/wiki/File:Internet-web-browser.svg'

    sidebar_info = []

    sidebar_info.append(f"- **Capacidad**: {int(apto_data['Max Guests'])}")

    if pd.notna(apto_data['Bedrooms']):
        sidebar_info.append(f"- **Habitaciones**: {int(apto_data['Bedrooms'])}")
    if pd.notna(apto_data['Bathrooms']):
        sidebar_info.append(f"- **Baños**: {int(apto_data['Bathrooms'])}")
    if pd.notna(url):
        sidebar_info.append(f"""- **URL**: [Ver en {sitio_web}]({url}) <img src="{icon_url}" alt="{sitio_web}" width="50" style="vertical-align:middle; margin-left:5px"/>""")
    if pd.notna(apto_data['Check-in Time']):
        sidebar_info.append(f"- **Check-in**: {apto_data['Check-in Time']}")
    if pd.notna(apto_data['Checkout Time']):
        sidebar_info.append(f"- **Check-out**: {apto_data['Checkout Time']}")
    if pd.notna(apto_data['Cleaning Fee (Native)']):
        sidebar_info.append(f"- **Tasas de limpieza**: {apto_data['Cleaning Fee (Native)']}€")
    if pd.notna(apto_data['Cancellation Policy']):
        sidebar_info.append(f"- **Política de cancelación**: {apto_data['Cancellation Policy']}")
    if pd.notna(apto_data['Overall Rating']):
        sidebar_info.append(f"- **Valoración**: {apto_data['Overall Rating']}")
    if pd.notna(apto_data['Number of Reviews']):
        sidebar_info.append(f"- **Número de reseñas**: {apto_data['Number of Reviews']}")

    st.sidebar.markdown("\n".join(sidebar_info), unsafe_allow_html=True)

    # Gráficas de reservas históricas
    datos_mensuales = torrevieja_monthly[torrevieja_monthly['Property ID'] == clicked]

    fig_ingresos = px.bar(
        datos_mensuales,
        x='Reporting Month',
        y='Revenue (Native)',
        title=f'Ingresos mensuales - Propiedad {clicked}',
        labels={'Revenue (Native)': 'Ingresos (€)', 'Reporting Month': 'Mes'}
    )
    st.sidebar.plotly_chart(fig_ingresos, use_container_width=True)

    fig_occupancy = px.bar(
        datos_mensuales,
        x='Reporting Month',
        y='Occupancy Rate',
        title=f'Ratio de Ocupación - Propiedad {clicked}',
        labels={'Occupancy Rate': 'Ratio de ocupación', 'Reporting Month': 'Mes'}
    )
    st.sidebar.plotly_chart(fig_occupancy, use_container_width=True)

    fig_reservas = px.bar(
        datos_mensuales,
        x='Reporting Month',
        y='Number of Reservations',
        title=f'Número de reservas - Propiedad {clicked}',
        labels={'Number of Reservations': 'Número de reservas', 'Reporting Month': 'Mes'}
    )
    st.sidebar.plotly_chart(fig_reservas, use_container_width=True)

    fig_reservas = px.bar(
        datos_mensuales,
        x='Reporting Month',
        y='ADR (Native)',
        title=f'ADR - Propiedad {clicked}',
        labels={'ADR (Native)': 'ADR (€)', 'Reporting Month': 'Mes'}
    )
    st.sidebar.plotly_chart(fig_reservas, use_container_width=True)