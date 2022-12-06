import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask, jsonify
from flask_mysqldb import MySQL
# pip install Flask-Cors==1.10.3
from flask_cors import CORS, cross_origin
import random
from config.helper_function import *  
from repository.db_query import *
# from tabulate import tabulate


app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'clothing_store'

mysql = MySQL(app)

@app.route('/recommend/<user_id>', methods=['GET'])
@cross_origin(origin='*',headers=['Content-Type','Authorization'])
def recommend(user_id):
    cursor = mysql.connection.cursor()

    # Query all products in DB
    cursor.execute(getall_product_query_string())

    col_names = ["id", "category_id", "name", "price"]

    table_product_data = pd.DataFrame(data=json_transform(cursor))

    # Get all product id in wishlist
    cursor.execute(getall_wishlist_query_string(user_id))
    data = cursor.fetchall()

    # Array contains all productId in wishlist
    list_product_id = []
    for product in data:
        list_product_id.append(product[0])

    # Create column combine feature
    for col_name in col_names:
        table_product_data[col_name] = table_product_data[col_name].fillna('')

    def combineFeatures(row):
        return str(row['category_id']) + " " + row['name'] + " " + str(row['price'])

    table_product_data["combineFeatures"] = table_product_data.apply(
        combineFeatures, axis=1)

    # Create count matrix for combined features
    cv = CountVectorizer()

    matrix = cv.fit_transform(table_product_data["combineFeatures"])

    # Calculate cosine similarity based on count matrix vectors
    cosineSimilarity = cosine_similarity(matrix)

    recommend_list = []

    # Loop id in product in wishlist
    for Id in list_product_id:
        # calculate cosine beetween 2 vectors & sort by highest similarity
        similar_products = list(enumerate(cosineSimilarity[getIndexById(Id, table_product_data)]))
        sorted_similar_products = sorted(
            similar_products, key=lambda x: x[1], reverse=True)

        # Loop top 5 recommened product of each wishlist product
        i = 0
        for product in sorted_similar_products:
            # Remove same product in wishlist
            if (getProductName(product[0], table_product_data) != getProductName(getIndexById(Id, table_product_data), table_product_data)):
                # maximum 100 recommened products
                if (len(recommend_list) > 48):
                    break

                # query for each product by id
                # product[0] = index of recommended product in matrix
                cursor.execute(get_pros_query_string(getIdByIndex(product[0], table_product_data)))

                # push to api list
                recommend_list += json_transform(cursor)
                i = i + 1

                # maximum 5 recommend products per
                if i > 4:
                    break

    # Close connection
    cursor.close()
    
    # duplicate recommend remove    
    dup_id = set()

    duplicate_filter_list = []

    # Check all in arr, if id not in the set, append for the new array
    for obj in recommend_list:
        if obj["id"] not in dup_id:
            duplicate_filter_list.append(obj)
            dup_id.add(obj["id"])
    
    # Randomize the recommended list
    random.shuffle(duplicate_filter_list)

    return jsonify({'list': duplicate_filter_list})


app.run(host='localhost', port=8081)
