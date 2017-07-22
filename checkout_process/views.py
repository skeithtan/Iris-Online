import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import Http404, redirect
from django.shortcuts import render
from django.views import View

from IrisOnline.contexts import make_context
from IrisOnline.decorators import customer_required
from order_management.models import *


class LineItem():
    def __init__(self, product, quantity):
        self.product = product
        self.quantity = quantity

    def line_price(self):

        # TODO: Replace current_price
        return self.product.current_price * self.quantity


class CartView(View):
    @staticmethod
    @login_required
    @customer_required
    def get(request):
        line_items = []

        total_price = 0.00

        for product_id, quantity in request.session["cart"].items():
            product = Product.objects.get(id=product_id)
            line_items.append(LineItem(product, quantity=quantity))
            total_price += float(product.current_price) * float(quantity)

        context = make_context(request)
        context.update({
            "total_price": total_price,
            "line_items": line_items
        })
        return render(request, 'cart.html', context)

    @staticmethod
    @login_required
    @customer_required
    def delete(request):
        json_data = json.loads(request.body)
        try:
            product_id = json_data['product_id']
            del request.session['cart'][str(product_id)]
        except:
            return HttpResponseBadRequest() # Product ID Not Found

        request.session.modified = True
        return HttpResponse(200)

    @staticmethod
    @login_required
    @customer_required
    def post(request):

        try:
            json_data = json.loads(request.body)
            product_id = json_data['product_id']
            quantity = int(json_data['quantity'])
        except:
            raise Http404('Invalid JSON')

        try:
            Product.objects.get(id=product_id)
        except:
            raise Http404('Product not found')

        if quantity <= 0:
            if str(product_id) in request.session["cart"]:
                del request.session["cart"][str(product_id)]
        else:
            request.session["cart"][product_id] = quantity

        request.session.modified = True
        return HttpResponse(200)


def has_quantity_errors(line_items):
    for line_item in line_items:
        if line_item.product.quantity < line_item.quantity:
            return True

    return False


def has_dead_product_errors(line_items):
    for line_item in line_items:
        if not line_item.product.is_active:
            return True

    return False


def get_line_items(cart):
    line_items = []
    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        line_items.append(LineItem(product, quantity=quantity))

    return line_items


class CheckoutView(View):
    @staticmethod
    @login_required
    @customer_required
    def get(request):
        user = request.user
        customer = Customer.objects.get(user=user)
        line_items = get_line_items(cart=request.session["cart"])

        if len(line_items) == 0:
            return redirect("/")

        total_price = 0.00
        quantity_errors = []
        out_of_stock_errors = []
        dead_products = []
        for line_item in line_items:

            # Check if product is activated
            if not line_item.product.is_active:
                dead_products.append(line_item.product)
                del request.session["cart"][line_item.product.id]
                line_items.remove(line_item)
                continue

            # Check if product is in stock
            if line_item.product.quantity == 0:
                out_of_stock_errors.append(line_item.product)
                del request.session["cart"][str(line_item.product.id)]
                request.session.modified = True
                line_items.remove(line_item)

            # Check if inventory can support cart quantity
            if line_item.product.quantity < line_item.quantity:
                quantity_errors.append(line_item.product)
                line_item.quantity = line_item.product.quantity

                request.session["cart"][line_item.product.id] = line_item.quantity

            total_price += float(line_item.product.current_price) * float(line_item.quantity)

        if quantity_errors:
            request.session.modified = True

        context = make_context(request)

        context.update({
            "total_price": total_price,
            "line_items": line_items,
            "customer": customer,
            "out_of_stock_errors": out_of_stock_errors,
            "quantity_errors": quantity_errors,
            "dead_products": dead_products
        })

        return render(request, 'checkout.html', context)

    @staticmethod
    @login_required
    @customer_required
    def post(request):
        line_items = get_line_items(request.session["cart"])
        if has_quantity_errors(line_items) or has_dead_product_errors(line_items):
            return redirect("/checkout/review/")

        request.session["approved_cart"] = True
        request.session.modified = True
        return redirect("/checkout/purchase-complete/")


class PurchaseView(View):
    @staticmethod
    @login_required
    @customer_required
    def get(request):

        if "approved_cart" not in request.session or not request.session["approved_cart"]:
            return redirect("/checkout/cart/")

        cart = request.session["cart"]
        customer = Customer.objects.get(user=request.user)
        order = Order.objects.create(customer=customer)

        for product_id, quantity in cart.items():

            # Deduct from inventory
            product = Product.objects.get(id=product_id)
            product.quantity -= quantity
            product.save()

            # Add quantity to order
            OrderLineItems.objects.create(
                product=Product.objects.get(id=product_id),
                quantity=quantity,
                parent_order=order
            )

        request.session["cart"] = {}  # Empty cart
        request.session["approved_cart"] = False
        request.session.modified = True
        context = make_context(request)
        context["total_price"] = order.total_price

        return render(request, 'purchase.html', context)
