from django.db import models
from app_kiberclub.models import Client


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    objects = models.Manager()

    class Meta:
        db_table = "Category"
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория", blank=True, null=True)
    name = models.CharField(max_length=255, verbose_name="Название")
    price = models.IntegerField(verbose_name="Цена")
    image = models.ImageField(upload_to="item_images/", verbose_name="Изображение", blank=True, null=True)
    quantity_in_stock = models.PositiveSmallIntegerField(default=1, verbose_name="Количество на складе")
    in_stock = models.BooleanField(default=True, verbose_name="В наличии")
    objects = models.Manager()

    class Meta:
        db_table = "Product"
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"

    def __str__(self):
        return self.name


class CartQuerySet(models.QuerySet):
    def total_quantity(self):
        return sum(item.quantity for item in self)

    def total_sum(self):
        return sum(item.cart_item_price() for item in self)


class Cart(models.Model):
    user = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="cart", verbose_name="Пользователь")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    quantity = models.PositiveSmallIntegerField(default=1, verbose_name="Количество", blank=True, null=True)
    objects = CartQuerySet.as_manager()

    class Meta:
        db_table = "Cart"
        verbose_name = "Корзина"
        verbose_name_plural = "Корзина"

    def __str__(self):
        return f"Корзина: {self.user.name} | Продукт: {self.product.name}"

    def cart_item_price(self):
        return self.product.price * self.quantity

    def item_quantity(self):
        return self.quantity


class Order(models.Model):
    user = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name="Пользователь")
    objects = models.Manager()

    class Meta:
        db_table = "Order"
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ: {self.id} | Клиент: {self.user.name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name="Заказ")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    quantity = models.PositiveSmallIntegerField(default=1, verbose_name="Количество")
    models.PositiveSmallIntegerField(default=1, verbose_name="Количество")
    objects = models.Manager()

    class Meta:
        db_table = "OrderItem"
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self):
        return f"Заказ: {self.id} | Продукт: {self.product.name}"


class OrderAvailabilitySettings(models.Model):
    """Модель для настройки доступности заказов"""

    is_available = models.BooleanField(default=True, verbose_name="Заказы доступны")
    unavailable_message = models.TextField(default="Заказы временно недоступны. Приносим свои извинения.", verbose_name="Сообщение при недоступности заказов")
    objects = models.Manager()

    class Meta:
        db_table = "OrderAvailabilitySettings"
        verbose_name = "Настройка доступности заказов"
        verbose_name_plural = "Настройки доступности заказов"

    def __str__(self):
        return f'Настройки доступности заказов: {"Доступны" if self.is_available else "Недоступны"}'
