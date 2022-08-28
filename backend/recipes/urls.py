from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from .views import TagViewSet, IngredientViewSet, RecipesViewSet

app_name = 'api'

router = DefaultRouter()
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'recipes', RecipesViewSet, basename='recipes')

urlpatterns = [url('', include(router.urls)), ]
