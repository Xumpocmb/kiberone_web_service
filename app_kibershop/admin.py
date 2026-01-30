from django.contrib import admin

from app_kibershop.models import Category, Product, OrderItem, Order, Cart, OrderAvailabilitySettings, RunningLine


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "in_stock", "quantity_in_stock", "category")
    search_fields = ("name",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ["product", "quantity"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    list_display = ["__str__"]
    # search_fields = ['user__phone_number']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    model = Cart


@admin.register(OrderAvailabilitySettings)
class OrderAvailabilitySettingsAdmin(admin.ModelAdmin):
    list_display = ("is_available", "unavailable_message")
    list_editable = ("is_available",)
    list_display_links = ("unavailable_message",)
    fields = ("is_available", "unavailable_message")


@admin.register(RunningLine)
class RunningLineAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('is_active',)
    search_fields = ('text',)
    list_per_page = 20

    def has_add_permission(self, request):
        # Allow only one instance of RunningLine
        count = RunningLine.objects.count()
        if count == 0:
            return True
        return False
