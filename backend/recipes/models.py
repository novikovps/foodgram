from colorfield.fields import ColorField
from django.core.exceptions import ValidationError
from django.db import models

from users.models import User


def validate_gt_zero(value):
    if value <= 0:
        raise ValidationError(
            "Значение не должно быть меньше или равно нулю",
        )


class Tag(models.Model):

    name = models.CharField(
        max_length=200,
        verbose_name="Название",
        unique=True,
    )
    color = ColorField(default="#FF0000")
    slug = models.SlugField(
        max_length=200,
        verbose_name="Slug",
        unique=True,
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Ingredient(models.Model):

    name = models.CharField(
        max_length=200,
        verbose_name="Название",
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name="Единицы измерения",
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="unique_ingredient",
            )
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор",
    )
    name = models.CharField(
        max_length=200,
        verbose_name="Название",
    )
    text = models.TextField(
        verbose_name="Описание",
    )
    image = models.ImageField(
        upload_to="recipes/images/",
        verbose_name="Картинка",
    )
    ingredients = models.ManyToManyField(
        Ingredient, through="RecipeIngredient", verbose_name="Ингридиенты"
    )
    tags = models.ManyToManyField(Tag, verbose_name="Теги")
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления", validators=[validate_gt_zero]
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата публикации",
    )

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        related_name="recipe_ingredients",
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        related_name="ingredient_in_recipes",
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество", validators=[validate_gt_zero]
    )

    class Meta:
        verbose_name = "Ингридиенты в рецептах"
        verbose_name_plural = "Ингридиенты в рецептах"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipeingredient",
            ),
        ]

    def __str__(self):
        return f"{self.recipe} {self.ingredient}"


class Favorite(models.Model):

    user = models.ForeignKey(
        User, related_name="favorites", on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe, related_name="favorites", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_favorite",
            )
        ]

    def __str__(self):
        return f"{self.user} {self.recipe}"


class ShoppingCart(models.Model):

    user = models.ForeignKey(
        User, related_name="shopping_cart", on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe, related_name="shopping_cart", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Список покупок"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_shoppingcart",
            )
        ]
