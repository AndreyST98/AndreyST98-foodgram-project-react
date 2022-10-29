from django.conf import settings
from django.core import validators
from django.db import models

from user.models import CustomUser

User = CustomUser


class Tag(models.Model):
    BLUE = '#0000FF'
    ORANGE = '#FFA500'
    GREEN = '#008000'
    PURPLE = '#800080'
    YELLOW = '#FFFF00'

    COLOR_CHOICES = [
        (BLUE, 'Синий'),
        (ORANGE, 'Оранжевый'),
        (GREEN, 'Зеленый'),
        (PURPLE, 'Фиолетовый'),
        (YELLOW, 'Желтый'),
    ]
    name = models.CharField(max_length=100, unique=True,
                            verbose_name='Название')
    color = models.CharField(max_length=7, choices=COLOR_CHOICES,
                             verbose_name='Цвет', unique=True,)
    slug = models.SlugField(verbose_name='Ссылка', unique=True,
                            help_text='Ссылка тега')

    class Meta:
        ordering = ['-id']
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return f'{self.name}, {self.slug}'


class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True,
                            verbose_name='Ингредиент')
    measurement_unit = models.CharField(max_length=50,
                                        verbose_name='Единицы измерения')

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(fields=['name', 'measurement_unit'],
                                    name='unique ingredient')
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    tags = models.ManyToManyField(Tag, related_name='recipes',
                                  verbose_name='Ссылка')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
    )
    ingredients = models.ManyToManyField(Ingredient,
                                         through='IngredientAmount')
    name = models.CharField(max_length=100, verbose_name='Название рецепта')
    image = models.ImageField(
        'Картинка',
        upload_to='media/',
        blank=True, null=True,
    )
    text = models.TextField(verbose_name='Описание рецепта')
    cooking_time = models.PositiveSmallIntegerField(
            verbose_name='Время приготовления')
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True,
                                    db_index=True)

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'{self.name}'


class IngredientAmount(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Название рецепта',
        related_name='ingredients_in_recipe'
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, null=True,
        related_name='ingredients_in_recipe', verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        default=1, validators=[validators.MinValueValidator(1)],
        verbose_name='Количество ингредиентов'
    )

    class Meta:
        verbose_name = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient')]

    def __str__(self):
        return (f"{self.ingredient.name}"
                f"{self.amount}{self.ingredient.measurement_unit}")


class Favorite(models.Model):
    """ Модель для Избранного. """
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='user')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='favorite_recipe')

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe')]


class ShopList(models.Model):
    """ Модель для Листа Покупок. """

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='cart_recipe')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='cart_recipe')

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_customer_recipe')]


class Follow(models.Model):
    """ Модель для Подписок. """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='follower',
                             verbose_name='Подписчик',)
    following = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  on_delete=models.CASCADE,
                                  related_name='following',
                                  verbose_name='Автор',)

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_following')]

    def __str__(self):
        return f'{self.user} подписался на {self.following}'