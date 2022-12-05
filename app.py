import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask, jsonify, render_template, request
from flask_mysqldb import MySQL
from tabulate import tabulate

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'clothing_store'

mysql = MySQL(app)


@app.route('/recommend/<userId>', methods=['GET'])
def recommend(userId):
    # query
    getAllProduct_query_string = "select p.id, category_id, name, t.price from products p, types t where p.id = t.product_id group by p.id"

    getAllWishList_query_string = "select p.id ,p.category_id, p.name, w.price from wishlists w, products p where w.product_id = p.id and w.user_id=" + userId

    cursor = mysql.connection.cursor()

    # query all products in DB
    cursor.execute(getAllProduct_query_string)

    # turn query data into table
    row_headers = [x[0] for x in cursor.description]
    data = cursor.fetchall()
    json_data = []
    for result in data:
        json_data.append(dict(zip(row_headers, result)))

    col_names = ["id", "category_id", "name", "price"]

    table_product_data = pd.DataFrame(data=json_data)

    # get all product id in wishlist
    cursor.execute(getAllWishList_query_string)
    data = cursor.fetchall()

    # array contains all productId in wishlist
    listProductId = []
    for product in data:
        listProductId.append(product[0])
    # print(listProductId)

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

    recommendList = []
    # List tương đồng cosine cho các movies của input movie
    for Id in listProductId:
        similarProducts = list(enumerate(cosineSimilarity[getIndexById(Id)]))
        sortedSimilarProduct = sorted(similarProducts, key = lambda x: x[1], reverse = True)
        # print(sortedSimilarProduct)
        i = 0
        for product in sortedSimilarProduct:
            if (getProductName(product[0]) != getProductName(getIndexById(Id))):
                # print(getProductName(product[0]))
                # if (len(recommendList) > 100):
                #     break
                getProductById_query_string = "select p.id, p.name, p.image, p.avg_rating, t.price from products p, types t where t.product_id = p.id and p.id=" + Id + "group by p.id"
                cursor.execute(getAllProduct_query_string)
                data = cursor.fetchall()
                print(data)

                recommendList.append(getProductName(product[0]))
                i = i + 1
                if i > 4:
                    break
    


    # print(recommendList)

    cursor.close()

    return jsonify({'wishlist': json_data})

app.run(host='localhost', port=8081)
