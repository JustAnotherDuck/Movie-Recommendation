from flask import Flask, request, jsonify
import pandas as pd
import numpy as np

app = Flask(__name__)

# Load data once at startup
df = pd.read_csv('data/movies.csv').merge(pd.read_csv('data/ratings.csv'), on='movieId')

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    movie_name = data.get('movie_name', '').strip()

    movie_in_db = df['title'] == movie_name

    if not np.any(movie_in_db):
        movie_name_words = [w.strip() for w in movie_name.lower().split(' ') if w != 'the']
        similar_names_with_points = []

        for title in df['title'].values:
            points = sum(word in title.lower().split(' ') for word in movie_name_words)
            if points > 0:
                similar_names_with_points.append((title, points))

        similar_names_with_points.sort(key=lambda x: x[1], reverse=True)
        top_similar = [x[0] for x in similar_names_with_points[:5]]

        return jsonify({
            'status': 'not_found',
            'suggestions': top_similar
        })

    movie_db = df[movie_in_db].sort_values(by='rating', ascending=False)

    recommended_movies = []

    for user in movie_db.iloc[:5]['userId'].values:
        rated_movies = df[df['userId'] == user]
        rated_movies = rated_movies[rated_movies['title'] != movie_name]\
                        .sort_values(by='rating', ascending=False)\
                        .iloc[:5]
        recommended_movies.extend(rated_movies['title'].values)

    recommended_movies = np.unique(recommended_movies)
    given_movie_genres = df[movie_in_db].iloc[0]['genres'].split('|')
    
    scores = {}
    for movie in recommended_movies:
        movie_d = df[df['title'] == movie].iloc[0]
        movie_genres = movie_d['genres'].split('|')
        score = sum(genre in movie_genres for genre in given_movie_genres)
        scores[movie] = score

    final_recommendations = sorted(scores, key=scores.get, reverse=True)

    return jsonify({
        'status': 'found',
        'recommendations': final_recommendations
    })

if __name__ == '__main__':
    app.run(debug=True)
