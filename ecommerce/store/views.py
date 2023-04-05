from django.shortcuts import render
from django.http import JsonResponse
import json
import datetime
from django.db.models import Q
from .models import *

# Create your views here.



def store(request):
    
    if request.user.is_authenticated:
        customer = request.user.customer
        orders = Order.objects.filter(customer=customer, complete=False)

        if orders.exists():
            order = orders.first()
            items = order.orderitem_set.all()
            cartItems = order.get_cart_items
        else:
            items = []
            order = {'get_cart_total': 0, 'get_cart_items': 0, 'shipping': False}
            cartItems = order['get_cart_items']

    else:
        items = []
        order = {'get_cart_total': 0, 'get_cart_items': 0}
        cartItems = order['get_cart_items']

    products = Product.objects.all()
    context = {'products': products, 'cartItems': cartItems}
    return render(request, 'store/store.html', context)


from django.shortcuts import render
from store.models import Product, Order, OrderItem
from django.db.models import Q

def cart(request):
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        cart = json.loads(request.COOKIES.get('cart', '{}'))

        items = []
        order = {'get_cart_total': 0, 'get_cart_items': 0}
        cartItems = order['get_cart_items']

        product_ids = [int(pid) for pid in cart.keys()]

        # Use Q objects to filter products in cart
        products = Product.objects.filter(Q(id__in=product_ids))

        for product in products:
            
            try:

                quantity = cart[str(product.id)]['quantity']
                total = (product.price * quantity)
                order['get_cart_total'] += total
                order['get_cart_items'] += quantity
                item = {
                    'product': {
                        'id': product.id,
                        'name': product.name,
                        'price': product.price,
                        'imageURL': product.imageURL,
                    },
                    'quantity': quantity,
                    'get_total': total,
                }
                items.append(item)

                if product.digital == False:
                    order['shipping'] == True

            except:
                pass
        


        cartItems = order['get_cart_items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/cart.html', context)




def checkout(request):
    if request.user.is_authenticated:
        customer = request.user.customer
        orders = Order.objects.filter(customer=customer, complete=False)
        if orders.exists():
            order = orders.first()
            items = order.orderitem_set.all()
            cartItems = order.get_cart_items
        else:
            items = []
            order = {'get_cart_total': 0, 'get_cart_items': 0, 'shipping': False}
            cartItems = order['get_cart_items']
    else:
        items = []
        order = {'get_cart_total': 0, 'get_cart_items': 0}
        cartItems = order['get_cart_items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}   
    return render(request, 'store/checkout.html', context)

def updateItem(request):
    data=json.loads(request.body)
    productId = data['productId']
    action = data['action']

    print('Action:', action)
    print('productId:', productId)

    customer = request.user.customer
    product = Product.objects.get(id=productId)

    # Ensure there is only one order for the current customer that is not complete
    order = Order.objects.filter(Q(customer=customer) & Q(complete=False)).first()
    if not order:
        order = Order.objects.create(customer=customer, complete=False)

    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)
    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()    

    return JsonResponse('Item was added', safe=False)

#from django.views.decorators.csrf import csrf_exempt
#@csrf_exempt

def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        # Retrieve an incomplete order associated with the customer or create a new one
        order = Order.objects.filter(Q(customer=customer) & Q(complete=False)).first()
        if not order:
            order = Order.objects.create(customer=customer, transaction_id=transaction_id)
        total = float(data['form']['total'])

        if total == order.get_cart_total:
            order.complete = True
            order.save()

            if data.get('shipping'):
                ShippingAddress.objects.create(
                    customer=customer,
                    order=order,
                    address=data['shipping']['address'],
                    city=data['shipping']['city'],
                    state=data['shipping']['state'],
                    zipcode=data['shipping']['zipcode'],
                )
            return JsonResponse('Payment complete!', safe=False)
        else:
            return JsonResponse('Payment failed!', safe=False)
    else:
        print('User is not logged in...')
        return JsonResponse('User is not logged in!', safe=False)


