from django_filters import rest_framework as filters

from recipes.models import Recipe


class RecipeFilter(filters.FilterSet):
    "Filterset для фильтрации по тегу."

    tags = filters.AllValuesMultipleFilter(field_name="tags__slug")

    class Meta:
        model = Recipe
        fields = [
            "tags",
        ]
