from entity_management.models import Product
from customer_profile.models import Customer
from django.db.models import (
    Model,
    ForeignKey,
    PROTECT,
    CASCADE,
    PositiveIntegerField,
    DateTimeField,
    CharField,
    FloatField
)


class Order(Model):
    ORDER_STATUSES = (
        ('P', 'Pending'),
        ('A', 'Processing'),
        ('S', 'Shipped'),
        ('C', 'Cancelled')
    )

    date_ordered = DateTimeField(auto_now=True)
    customer = ForeignKey(Customer, on_delete=CASCADE)
    status = CharField(max_length=2, choices=ORDER_STATUSES, default='P')

    @staticmethod
    def print_orders_containing_product(product):
        orders = [order for order in Order.objects.all() if order.has_product(product)]
        for order in orders:
            print(f"Order #{order.id}")
            for line_item in order.orderlineitems_set.all():
                print(line_item.product.name)
            print()

    @property
    def total_price(self):
        order_items = self.orderlineitems_set.all()
        total_price = 0.00
        for order_item in order_items:
            total_price += float(order_item.line_price)
        return total_price

    def has_products(self, *products):
        for product in products:
            if not self.has_product(product):
                return False
        return True

    def has_product(self, product):
        order_items = self.orderlineitems_set.all()
        for order_item in order_items:
            if order_item.product == product:
                return True
        return False


class OrderLineItems(Model):
    # TODO: Prevent product deletion when ordered
    product = ForeignKey(Product, on_delete=PROTECT)
    quantity = PositiveIntegerField()
    parent_order = ForeignKey(Order, on_delete=CASCADE)

    @property
    def line_price(self):
        date_ordered = self.parent_order.date_ordered
        price = self.product.price_for_date(date=date_ordered)
        return float(price) * float(self.quantity)

class ProductAssociation(Model):
    root_product = ForeignKey(Product, on_delete=PROTECT, related_name="root_product")
    associated_product = ForeignKey(Product, on_delete=PROTECT,related_name="associated_product")
    probability = FloatField()

    def __str__(self):
        return f"{self.root_product.name} to {self.associated_product.name} - {self.probability}"