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
    # if request.method == 'GET':
    #     return "Login via the login Form"

    # query
    getAllProduct_query_string = "select p.id, category_id, name, t.price from products p, types t where p.id = t.product_id group by p.id"

    getAllWishList_query_string = "select p.id ,p.category_id, p.name, w.price from wishlists w, products p where w.id = p.id and w.user_id=" + userId

    cursor = mysql.connection.cursor()

    # query all products in DB
    cursor.execute(getAllProduct_query_string)

    # turn query data into table
    row_headers = [x[0] for x in cursor.description]
    data = cursor.fetchall()
    json_data = []
    for result in data:
        json_data.append(dict(zip(row_headers, result)))
    cursor.close()

    col_names = ["id", "category_id", "name", "price"]

    # print(tabulate(data, headers=col_names))
    # table_product_data = tabulate(data, headers=col_names)



    table_product_data = pd.DataFrame(data=json_data)

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

    # similarityFrame = pd.DataFrame(cosineSimilarity)

    # get index in table
    def getIndexById(id):
        i = table_product_data.index
        index = table_product_data["id"] == id
        result = i[index]
        listResult = result.tolist()
        
        return listResult[0]

    # print(getIndexById(39))

    def getProductName(index):
        return table_product_data[table_product_data.index == index]["name"].values[0]
    
    # List tương đồng cosine cho các movies của input movie
    similarProducts = list(enumerate(cosineSimilarity[getIndexById(39)]))

    listId = [12, 13, 14, 15]

    finalList = pd.DataFrame()

    for Id in listId:
        finalList = pd.concat([finalList, pd.DataFrame(enumerate(cosineSimilarity[getIndexById(Id)]))], ignore_index=True, axis = 1)

    print(finalList)
    # Sort movie, lấy giá trị thứ 2 của vector
    # e.g: Ta muốn chọn tương đồng cho movie A có cosine = 1, movie B có cosine = 0.7, movie C có cosine = 0.4
    # Ta có mảng vector[(0, 1), (1, 0.7), (2, 0.4)]
    # Ta cần lấy giá trị cosine tức giá trị thứ 2 của vector để so sánh tương đồng, nên
    # chọn x[1]
    sortedSimilarProduct = sorted(similarProducts, key = lambda x: x[1], reverse = True)

    print("Recommend for you:")
    print(finalList.head(10).sum(axis = 1).sort_values(ascending = False))


    return jsonify({'wishlist': json_data})


app.run(host='localhost', port=8081)
