from django.conf import settings
from django.db.models import Sum
from django.http import HttpResponse
from djoser.views import UserViewSet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import mixins, response, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)

import api.serializers as serializers
from api.permissions import IsOwnerOrReadOnly
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription, User

FONT_FILE = (settings.BASE_DIR).joinpath(r"data/fonts/FreeSans.ttf")


class ListCreateDeleteViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    pass


class ListCreateRetrieveDeleteViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    pass


#
# Users app
#


class CustomUserViewSet(UserViewSet):
    "Viewset для модели User."

    @action(
        methods=["get"],
        detail=False,
        url_path="subscriptions",
        serializer_class=serializers.SubscriptionsRepresentSerializer,
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def subscriptions(self, request):
        "Endpoint получения списка подписок."

        user = self.request.user
        recipes_limit = self.request.GET.get("recipes_limit")
        queryset = User.objects.filter(
            id__in=Subscription.objects.filter(subscriber=user.id).values(
                "author_id",
            )
        )
        context = super().get_serializer_context()
        context.update({"recipes_limit": recipes_limit})
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, context=context, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, context=context, many=True)
        return response.Response(serializer.data)

    @action(
        methods=["post", "delete"],
        detail=True,
        url_path="subscribe",
        serializer_class=serializers.SubscriptionSerializer,
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def subscribe(self, request, *args, **kwargs):
        "Endpoint создания и удаления подписки."

        author_id = self.kwargs.get("id")
        recipes_limit = self.request.GET.get("recipes_limit")
        author = get_object_or_404(User, pk=author_id)
        if self.request.method == "POST":
            context = super().get_serializer_context()
            context.update({"recipes_limit": recipes_limit})
            serializer = self.get_serializer(
                data={
                    "author": author.id,
                },
                context=context,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(subscriber=self.request.user)
            return response.Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        instance = Subscription.objects.filter(
            subscriber=self.request.user, author=author.id
        )
        if not instance.exists():
            return response.Response(
                data={"detail": "Подписка не существует"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @action(["get"], detail=False)
    def me(self, request, *args, **kwargs):
        "Endpoint получения информации о текущем пользователе."

        user = self.request.user
        if user.is_anonymous:
            return response.Response(
                data={"detail": "Пользователь не авторизован"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        serializer = self.get_serializer(user)
        return response.Response(serializer.data)


#
# Recipes app
#


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    "Viewset для модели Tag."

    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    "Viewset для модели Ingredient."

    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Ingredient.objects.all()

        name = self.request.GET.get("name")
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    "Viewset для модели Recipe."

    queryset = Recipe.objects.all()
    serializer_class = serializers.RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        queryset = Recipe.objects.all()

        tag_list = self.request.GET.getlist("tags")
        if tag_list:
            queryset = queryset.filter(tags__slug__in=tag_list).distinct()

        author = self.request.GET.get("author")
        if author:
            queryset = queryset.filter(author__id=author)

        if self.request.user.is_anonymous:
            return queryset

        if self.request.GET.get("is_favorited"):
            queryset = queryset.filter(favorites__user=self.request.user)

        if self.request.GET.get("is_in_shopping_cart"):
            queryset = queryset.filter(shopping_cart__user=self.request.user)

        return queryset

    def get_permissions(self):
        "Определение разрешений в зависимости от действия."

        if self.action in ("partial_update", "destroy"):
            return (IsOwnerOrReadOnly(),)
        return super().get_permissions()

    def get_serializer_class(self):
        "Определение сериализатора в зависимости от действия."

        if self.action in ("create", "partial_update"):
            return serializers.RecipeCreateSerializer
        return serializers.RecipeSerializer

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    @action(
        methods=["post", "delete"],
        detail=True,
        url_path="favorite",
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def favorite(self, request, *args, **kwargs):
        "Endpoint добавления/удаления рецепта в/из избранного."

        user = self.request.user
        recipe_id = self.kwargs.get("pk")
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        if self.request.method == "POST":
            serializer = serializers.FavoriteSerializer(
                data={
                    "recipe": recipe.id,
                    "user": user.id,
                }
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return response.Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        instance = Favorite.objects.filter(
            user=self.request.user, recipe=recipe.id
        )
        if not instance.exists():
            return response.Response(
                data={"detail": "Рецепт не добавлен в избранное"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["post", "delete"],
        detail=True,
        url_path="shopping_cart",
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def shopping_cart(self, request, *args, **kwargs):
        "Endpoint добавления/удаления рецепта в/из корзины."

        user = self.request.user
        recipe_id = self.kwargs.get("pk")
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        if self.request.method == "POST":
            serializer = serializers.ShoppingCartSerializer(
                data={
                    "recipe": recipe.id,
                    "user": user.id,
                }
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=self.request.user)
            return response.Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        instance = ShoppingCart.objects.filter(
            user=self.request.user, recipe=recipe.id
        )
        if not instance.exists():
            return response.Response(
                data={"detail": "Рецепт не добавлен в корзину"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["get"],
        detail=False,
        url_path="download_shopping_cart",
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        "Endpoint для скачивания списка продуктов из корзины."

        purchases = (
            RecipeIngredient.objects.filter(
                recipe_id__in=ShoppingCart.objects.values("recipe_id")
            )
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(Sum("amount"))
        )
        response = HttpResponse(content_type="application/pdf")
        response[
            "Content-Disposition"
        ] = 'attachment; filename="ShoppingCart.pdf"'
        p = canvas.Canvas(response)
        pdfmetrics.registerFont(TTFont("FreeSans", FONT_FILE))
        pos_y = 800
        for item in purchases:
            result = (
                f'{item["ingredient__name"].capitalize()}'
                f'({item["ingredient__measurement_unit"]}) - '
                f'{item["amount__sum"]}'
            )
            p.setFont("FreeSans", 16)
            pos_y -= 50
            p.drawString(100, pos_y, result)
            if pos_y == 50:
                p.showPage()
                pos_y = 800
        p.showPage()
        p.save()
        return response
