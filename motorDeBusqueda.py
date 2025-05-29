import os
from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import re
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Ruta para servir la interfaz HTML
@app.route('/')
def index():
    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(ruta_actual, 'page1.html')

# Cargar datos una sola vez
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

# Endpoint correcto
@app.route('/api/recomendar', methods=['POST'])
def recomendar():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No se enviaron datos JSON"}), 400

    favoritos_usuario = [item.get('title', '').strip() for item in data]
    juegos_usuario = juegos_cod[juegos_cod['title'].isin(favoritos_usuario)]

    if juegos_usuario.empty:
        return jsonify({"error": "No se encontraron juegos favoritos en la base de datos"}), 400

    perfil_usuario = juegos_usuario.drop(['title', 'genres'], axis=1, errors='ignore').sum().to_frame().T
    juegos_filtrados = juegos_cod[~juegos_cod['title'].isin(favoritos_usuario)]

    generos_cols = [col for col in perfil_usuario.columns if col not in ['title', 'genres']]
    juegos_generos = juegos_filtrados[generos_cols]

    similitudes = cosine_similarity(juegos_generos, perfil_usuario)
    juegos_filtrados = juegos_filtrados.copy()
    juegos_filtrados['similitud'] = similitudes

    recomendados = juegos_filtrados.sort_values(by='similitud', ascending=False)
    top_20 = recomendados.head(20)
    resultado = juegos.loc[top_20.index][['title', 'short_description', 'categories']]

    return jsonify(resultado.to_dict(orient="records"))

if __name__ == "__main__":
    app.run(debug=True)
