from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter
from django.urls import path

from .views import IngredientViewSet, RecipesViewSet, TagViewSet, CustomUserViewSet

app_name = 'api'

router = DefaultRouter()
#router.register(r'users', CustomUserViewSet, basename='users')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'recipes', RecipesViewSet, basename='recipes')
router.register(r'users', CustomUserViewSet, basename='users')

urlpatterns = [    
    url('', include(router.urls)), ]

# urlpatterns += router.urls