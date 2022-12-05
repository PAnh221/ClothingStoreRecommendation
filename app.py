import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask, jsonify, render_template, request
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'clothing_store'

mysql = MySQL(app)


@app.route('/recommend', methods=['GET'])
def recommend():
    # if request.method == 'GET':
    #     return "Login via the login Form"

    cursor = mysql.connection.cursor()

    query_string = "SELECT * FROM wishlists"
    cursor.execute(query_string)
    row_headers = [x[0] for x in cursor.description]

    data = cursor.fetchall()
    json_data = []
    for result in data:
        json_data.append(dict(zip(row_headers, result)))

    cursor.close()

    return jsonify({'wishlist': json_data})


app.run(host='localhost', port=8081)
