from django.urls import include, path
from rest_framework.routers import DefaultRouter

import api.views as views

router = DefaultRouter()
router.register("users", views.CustomUserViewSet)
router.register("tags", views.TagViewSet)
router.register("ingredients", views.IngredientViewSet)
router.register("recipes", views.RecipeViewSet)


urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
]
