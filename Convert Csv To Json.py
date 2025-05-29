import opendatasets as od
import os
import pandas as pd
import json

# Descargar dataset desde Kaggle
dataset_link = "https://www.kaggle.com/datasets/joebeachcapital/top-1000-steam-games"
od.download(dataset_link)

# Cambiar al directorio descargado
os.chdir("top-1000-steam-games")

# Verificar archivos disponibles
print("Archivos disponibles:", os.listdir())

# Nombre del archivo CSV
archivo = "steam_app_data.csv"

# Cargar el archivo CSV
df = pd.read_csv(archivo)

# Mostrar las columnas para verificar nombres exactos (opcional)
print("Columnas disponibles:", df.columns.tolist())

# Seleccionar columnas específicas (ajusta según los nombres exactos del archivo)
columnas = ['name', 'detailed_description', 'short_description', 'categories', 'genres']
columnas_existentes = [col for col in columnas if col in df.columns]
df = df[columnas_existentes]

import ast

def limpiar_lista_como_span(texto):
    try:
        lista = ast.literal_eval(texto)
        return " ".join(f"<span class='badge bg-secondary'>{item['description']}</span>" for item in lista)
    except:
        return ""

# Aplica limpieza si existen esas columnas
if 'categories' in df.columns:
    df['categories'] = df['categories'].apply(limpiar_lista_como_span)

if 'genres' in df.columns:
    df['genres'] = df['genres'].apply(limpiar_lista_como_span)


# Convertir a JSON y guardar
json_data = df.to_json(orient="records", indent=4, force_ascii=False)
with open("steam_data.json", "w", encoding="utf-8") as json_file:
    json_file.write(json_data)

print("✅ Archivo JSON creado exitosamente: steam_data.json")

