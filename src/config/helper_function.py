def json_transform(cursor):
    row_headers = [x[0] for x in cursor.description]
    data = cursor.fetchall()

    json_data = []

    for result in data:
        json_data.append(dict(zip(row_headers, result))) 
    
    return json_data

def getIndexById(id, table_product_data):
    i = table_product_data.index
    index = table_product_data["id"] == id
    result = i[index]
    listResult = result.tolist()
    return listResult[0]


def getProductName(index, table_product_data):
    return table_product_data[table_product_data.index == index]["name"].values[0]

def getIdByIndex(index, table_product_data):
    return table_product_data[table_product_data.index == index]["id"].values[0]