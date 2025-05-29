import os
from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import re
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Ruta para servir index.html desde la misma carpeta del script
@app.route('/')
def index():
    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(ruta_actual, 'page1.html')


# Cargar y procesar datos solo una vez al iniciar el servidor
juegos = pd.read_json('top-1000-steam-games/steam_data.json')
juegos['title'] = juegos['name']
juegos['genres'] = juegos['genres'].apply(lambda x: re.findall(r">([^<]+)<", x))

juegos_cod = juegos.copy()
for index, row in juegos.iterrows():
    for genre in row['genres']:
        juegos_cod.at[index, genre] = 1
juegos_cod = juegos_cod.fillna(0)
juegos_cod = juegos_cod.drop(['detailed_description', 'short_description', 'categories'], axis=1, errors='ignore')
juegos_cod['gameId'] = juegos_cod.index


# Ruta para recibir POST con juegos favoritos y devolver recomendaciones
@app.route('top-1000-steam-games\reco_output.json', methods=['POST'])
def recomendar():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No se enviaron datos JSON"}), 400

    # Se espera que data sea lista de títulos: [{ "title": "Nombre Juego" }, ...]
    favoritos_usuario = [item.get('title', '').strip() for item in data]

    # Filtrar juegos que usuario indicó
    juegos_usuario = juegos_cod[juegos_cod['title'].isin(favoritos_usuario)]

    if juegos_usuario.empty:
        return jsonify({"error": "No se encontraron juegos favoritos en la base de datos"}), 400

    # Crear perfil usuario sumando vectores de géneros
    perfil_usuario = juegos_usuario.drop(['title', 'genres'], axis=1, errors='ignore').sum().to_frame().T

    # Juegos a recomendar (excluyendo los favoritos)
    juegos_filtrados = juegos_cod[~juegos_cod['title'].isin(favoritos_usuario)]

    # Columnas de géneros
    generos_cols = [col for col in perfil_usuario.columns if col not in ['title', 'genres']]

    juegos_generos = juegos_filtrados[generos_cols]

    # Calcular similitud coseno
    similitudes = cosine_similarity(juegos_generos, perfil_usuario)

    juegos_filtrados = juegos_filtrados.copy()
    juegos_filtrados['similitud'] = similitudes

    # Ordenar y tomar top 20
    recomendados = juegos_filtrados.sort_values(by='similitud', ascending=False)
    top_20 = recomendados.head(20)

    # Obtener info para devolver
    resultado = juegos.loc[top_20.index][['title', 'short_description', 'categories']]

    return jsonify(resultado.to_dict(orient="records"))


if __name__ == "__main__":
    app.run(debug=True)
