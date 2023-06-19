from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


class TagAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "name",
        "color",
        "slug",
    )
    fields = (
        "name",
        "color",
        "slug",
    )


class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "name",
        "measurement_unit",
    )
    fields = (
        "name",
        "measurement_unit",
    )
    list_filter = ("name",)


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "author",
        "name",
    )
    fields = ("author", "name", "text", "image", "tags", "cooking_time")
    list_filter = ("author", "name", "tags")


class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ("pk", "recipe", "ingredient", "amount")
    fields = ("recipe", "ingredient", "amount")


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "recipe")
    fields = ("user", "recipe")
    list_filter = ("user", "recipe")


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "recipe")
    fields = ("user", "recipe")
    list_filter = ("user", "recipe")


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
