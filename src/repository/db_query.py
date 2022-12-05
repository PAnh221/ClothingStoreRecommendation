def getall_product_query_string(): 
    return "select p.id, category_id, name, t.price from products p, types t where p.id = t.product_id group by p.id"

def getall_wishlist_query_string(user_id): 
    return "select p.id ,p.category_id, p.name, w.price from wishlists w, products p where w.product_id = p.id and w.user_id=" + user_id

def  get_pros_query_string(pro_id):
    return "select p.id, p.name, p.image, p.avg_rating, t.price from products p, types t where t.product_id = p.id and p.id = " + \
            str(pro_id) + " group by p.id"