import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask, jsonify, render_template, request
from flask_mysqldb import MySQL
# from tabulate import tabulate

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'clothing_store'

mysql = MySQL(app)


@app.route('/recommend/<userId>', methods=['GET'])
def recommend(userId):
    # Query
    getall_product_query_string = "select p.id, category_id, name, t.price from products p, types t where p.id = t.product_id group by p.id"

    getall_wishlist_query_string = "select p.id ,p.category_id, p.name, w.price from wishlists w, products p where w.product_id = p.id and w.user_id=" + userId

    cursor = mysql.connection.cursor()

    # Query all products in DB
    cursor.execute(getall_product_query_string)

    # Qurn query data into table
    row_headers = [x[0] for x in cursor.description]
    data = cursor.fetchall()
    json_data = []
    for result in data:
        json_data.append(dict(zip(row_headers, result)))

    col_names = ["id", "category_id", "name", "price"]

    table_product_data = pd.DataFrame(data=json_data)

    # Get all product id in wishlist
    cursor.execute(getall_wishlist_query_string)
    data = cursor.fetchall()

    # Array contains all productId in wishlist
    list_product_id = []
    for product in data:
        list_product_id.append(product[0])

    # Create column combine feature
    for col_name in col_names:
        table_product_data[col_name] = table_product_data[col_name].fillna('')

    def combineFeatures(row):
        return str(row['id']) + str(row['category_id']) + " " + row['name'] + " " + str(row['price'])

    table_product_data["combineFeatures"] = table_product_data.apply(
        combineFeatures, axis=1)

    # Create count matrix for combined features
    cv = CountVectorizer()

    matrix = cv.fit_transform(table_product_data["combineFeatures"])

    # Calculate cosine similarity based on count matrix vectors
    cosineSimilarity = cosine_similarity(matrix)

    def getIndexById(id):
        i = table_product_data.index
        index = table_product_data["id"] == id
        result = i[index]
        listResult = result.tolist()
        return listResult[0]


    def getProductName(index):
        return table_product_data[table_product_data.index == index]["name"].values[0]

    def getIdByIndex(index):
        return table_product_data[table_product_data.index == index]["id"].values[0]

    # Return array
    recommend_list = []

    # Loop id in product in wishlist
    for Id in list_product_id:
        # calculate cosine beetween 2 vectors & sort by highest similarity
        similar_products = list(enumerate(cosineSimilarity[getIndexById(Id)]))
        sorted_similar_products = sorted(
            similar_products, key=lambda x: x[1], reverse=True)

        # Loop top 5 recommened product of each wishlist product
        i = 0
        for product in sorted_similar_products:
            # Remove same product in wishlist
            if (getProductName(product[0]) != getProductName(getIndexById(Id))):
                # maximum 100 recommened products
                if (len(recommend_list) > 48):
                    break

                # query for each product by id
                # product[0] = index of recommended product in matrix
                pros_query_string = "select p.id, p.name, p.image, p.avg_rating, t.price from products p, types t where t.product_id = p.id and p.id = " + \
                    str(getIdByIndex(product[0])) + " group by p.id"
                cursor.execute(pros_query_string)
                data = cursor.fetchall()

                # convert to json for api
                row_headers = [x[0] for x in cursor.description]
                json_recommend_list = []
                for product in data:
                    json_recommend_list.append(dict(zip(row_headers, product)))

                # push to api list
                recommend_list += json_recommend_list

                i = i + 1

                # maximum 5 recommend products per
                if i > 4:
                    break

    # Close connection
    cursor.close()

    return jsonify({'wishlist': recommend_list})


app.run(host='localhost', port=8081)
