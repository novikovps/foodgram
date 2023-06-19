import base64

import webcolors
from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription, User


class Base64ImageField(serializers.ImageField):
    "Класс для декодирования изображения и сохранения в виде файла."

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)
        return super().to_internal_value(data)


class Hex2NameColor(serializers.Field):
    "Класс преобразования цвета в HEX в читаемое имя."

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError("Для этого цвета нет имени")
        return data


#
# Users app
#


class CustomUserSerializer(serializers.ModelSerializer):
    "Сериализатор для модели User."

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        "Функция проверки подписки."

        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(
            subscriber=user, author=obj.id
        ).exists()

    def get_recipes_count(self, obj):
        "Функция подсчёта количества рецептов."
        return obj.recipes.count()


class CustomUserCreateSerializer(UserCreateSerializer):
    "Сериализатор для регистрации пользователя."

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    "Сериализатор для создания  и удаления подписок."

    subscriber = serializers.PrimaryKeyRelatedField(
        read_only=True, default=serializers.CurrentUserDefault()
    )
    author = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )

    class Meta:
        model = Subscription
        fields = ("subscriber", "author")

    def validate(self, data):
        subscriber = self.context.get("request").user
        author = data["author"]
        if subscriber == author:
            raise serializers.ValidationError(
                "Нельзя подписаться на самого себя"
            )
        if Subscription.objects.filter(
            subscriber=subscriber, author=author
        ).exists():
            raise serializers.ValidationError(
                "Вы уже подписаны на этого автора"
            )
        return data

    def to_representation(self, instance):
        return SubscriptionsRepresentSerializer(
            instance=instance.author, context=self.context
        ).data


class SubscriptionsRepresentSerializer(serializers.ModelSerializer):
    "Сериализатор для отображения информации в подписке."

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_recipes(self, obj):
        "Функция ограничения отображаемых рецептов."

        limit = self.context.get("recipes_limit")
        queryset = Recipe.objects.filter(author=obj.id)
        if limit is not None:
            try:
                limit = int(limit)
            except ValueError:
                return SubscriptionsRecipesSerializer(queryset, many=True).data
            queryset = queryset[:limit]
        return SubscriptionsRecipesSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        "Функция подсчёта количества рецептов."

        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        "Функция проверки подписки."

        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(
            subscriber=user, author=obj.id
        ).exists()


#
# Recipes app.
#


class TagSerializer(serializers.ModelSerializer):
    "Сериалиазтор для тегов."

    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    "Сериализатор для ингридиентов."

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientSerializer(serializers.ModelSerializer):
    "Сериализатор для таблицы рецепты-ингредиенты."

    id = serializers.IntegerField(source="ingredient.id", read_only=True)
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeSerializer(serializers.ModelSerializer):
    "Сериалиазтор для рецептов."

    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField(required=True, allow_null=False)
    ingredients = RecipeIngredientSerializer(
        many=True, source="recipe_ingredients", read_only=True
    )
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "name",
            "text",
            "image",
            "ingredients",
            "tags",
            "cooking_time",
            "is_favorited",
            "is_in_shopping_cart",
        )

    def get_is_favorited(self, obj):
        "Функция проверки наличия в избранном."

        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        "Функция проверки наличия в корзине."

        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj.id).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    "Сериализатор для создания и обновления рецептов."

    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    ingredients = RecipeIngredientSerializer(
        many=True, source="ingredient_in_recipes", read_only=True
    )
    tags = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            "author",
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_time",
        )

    def validate(self, data):
        tags = self.initial_data.get("tags")
        ingredients = self.initial_data.get("ingredients")
        ids = [ingredient["id"] for ingredient in ingredients]
        ids_set = set(ids)
        if len(ids) != len(ids_set):
            raise serializers.ValidationError(
                "Ингредиенты должны быть уникальны"
            )
        amounts = [
            int(ingredient["amount"])
            for ingredient in ingredients
            if int(ingredient["amount"]) <= 0
        ]
        if amounts:
            raise serializers.ValidationError(
                "Количество ингредиентов должно быть больше нуля"
            )
        data["tags"] = tags
        data["ingredients"] = ingredients
        return data

    @transaction.atomic()
    def create(self, validated_data):
        ingredients_list = []
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            recipe.tags.add(get_object_or_404(Tag, pk=tag))
        for ingr in ingredients:
            amount = ingr["amount"]
            current_ingredient = get_object_or_404(Ingredient, pk=ingr["id"])
            ingredients_list.append(
                RecipeIngredient(
                    ingredient=current_ingredient, amount=amount, recipe=recipe
                )
            )
        RecipeIngredient.objects.bulk_create(ingredients_list)
        return recipe

    @transaction.atomic()
    def update(self, instance, validated_data):
        RecipeIngredient.objects.filter(recipe=instance).delete()
        ingredients_list = []
        ingredients = validated_data.pop("ingredients")
        for ingr in ingredients:
            amount = ingr["amount"]
            current_ingredient = get_object_or_404(Ingredient, pk=ingr["id"])
            ingredients_list.append(
                RecipeIngredient(
                    ingredient=current_ingredient,
                    amount=amount,
                    recipe=instance,
                )
            )
        RecipeIngredient.objects.bulk_create(ingredients_list)
        return super().update(instance, validated_data)

    def get_is_favorited(self, obj):
        "Функция проверки наличия в избранном."

        user = self.context.get("request").user
        return Favorite.objects.filter(user=user, recipe=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        "Функция проверки наличия в корзине."

        user = self.context.get("request").user
        return ShoppingCart.objects.filter(user=user, recipe=obj.id).exists()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["ingredients"] = self.initial_data["ingredients"]
        return representation


class SubscriptionsRecipesSerializer(serializers.ModelSerializer):
    "Сериализатор для отображения рецептов в подписке."

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class FavoriteSerializer(serializers.ModelSerializer):
    "Сериализатор для избранного."

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    name = serializers.CharField(read_only=True, source="recipe.name")
    cooking_time = serializers.IntegerField(
        read_only=True, source="recipe.cooking_time"
    )
    image = serializers.ImageField(read_only=True, source="recipe.image")

    class Meta:
        model = Favorite
        fields = ("recipe", "user", "name", "cooking_time", "image")

    def validate(self, data):
        user = data["user"]
        recipe = data["recipe"]
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                "Вы уже добавили этот рецепт в избранное"
            )
        return data


class ShoppingCartSerializer(serializers.ModelSerializer):
    "Сериализатор для корзины."

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    name = serializers.CharField(read_only=True, source="recipe.name")
    cooking_time = serializers.IntegerField(
        read_only=True, source="recipe.cooking_time"
    )
    image = serializers.ImageField(read_only=True, source="recipe.image")

    class Meta:
        model = ShoppingCart
        fields = ("recipe", "user", "name", "cooking_time", "image")

    def validate(self, data):
        user = data["user"]
        recipe = data["recipe"]
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                "Вы уже добавили этот рецепт в корзину"
            )
        return data
