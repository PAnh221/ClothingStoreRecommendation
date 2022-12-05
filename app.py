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
    # query
    getall_product_query_string = "select p.id, category_id, name, t.price from products p, types t where p.id = t.product_id group by p.id"

    getall_wishlist_query_string = "select p.id ,p.category_id, p.name, w.price from wishlists w, products p where w.product_id = p.id and w.user_id=" + userId

    cursor = mysql.connection.cursor()

    # query all products in DB
    cursor.execute(getall_product_query_string)

    # turn query data into table
    row_headers = [x[0] for x in cursor.description]
    data = cursor.fetchall()
    json_data = []
    for result in data:
        json_data.append(dict(zip(row_headers, result)))

    col_names = ["id", "category_id", "name", "price"]

    table_product_data = pd.DataFrame(data=json_data)

    # get all product id in wishlist
    cursor.execute(getall_wishlist_query_string)
    data = cursor.fetchall()

    # array contains all productId in wishlist
    list_product_id = []
    for product in data:
        list_product_id.append(product[0])
    # print(list_product_id)

    # print(table_product_data)
    # Tạo ra một column để gom nhóm các features
    for col_name in col_names:
        table_product_data[col_name] = table_product_data[col_name].fillna('')
    
    def combineFeatures(row):
        return str(row['id']) + str(row['category_id']) + " " + row['name'] + " " + str(row['price'])

    table_product_data["combineFeatures"] = table_product_data.apply(combineFeatures, axis = 1)

    # Tạo ra count matrix cho các features được combined
    cv = CountVectorizer()

    matrix = cv.fit_transform(table_product_data["combineFeatures"])
    
    # Tính sự tương đồng Cosine dựa trên các vector của count matrix
    cosineSimilarity = cosine_similarity(matrix)

    def getIndexById(id):
        i = table_product_data.index
        index = table_product_data["id"] == id
        result = i[index]
        listResult = result.tolist()
        return listResult[0]

    # print(getIndexById(39))

    def getProductName(index):
        return table_product_data[table_product_data.index == index]["name"].values[0]

    recommend_list = []
    # List tương đồng cosine cho các movies của input movie
    for Id in list_product_id:
        similar_products = list(enumerate(cosineSimilarity[getIndexById(Id)]))
        sorted_similar_products = sorted(similar_products, key = lambda x: x[1], reverse = True)
        # print(sorted_similar_products)
        i = 0
        for product in sorted_similar_products:
            if (getProductName(product[0]) != getProductName(getIndexById(Id))):
                # print(getProductName(product[0]))
                # if (len(recommend_list) > 100):
                #     break
                pros_query_string = "select p.id, p.name, p.image, p.avg_rating, t.price from products p, types t where t.product_id = p.id and p.id = " + str(Id) + " group by p.id"
                cursor.execute(pros_query_string)
                data = cursor.fetchall()
                
                print(data)

                row_headers = [x[0] for x in cursor.description]

                json_recommend_list = []

                for product in data: 
                    json_recommend_list.append(dict(zip(row_headers, product)))

                recommend_list += json_recommend_list

                i = i + 1
                if i > 4:
                    break

    print(recommend_list)
    
    cursor.close()

    return jsonify({'wishlist': recommend_list})

app.run(host='localhost', port=8081)
