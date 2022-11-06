# Социальная сеть для любителей Кулинарии: Foodgram
***
## Описание
«Продуктовый помощник» (Проект Яндекс.Практикум) Сайт является - базой кулинарных рецептов. Пользователи могут создавать свои рецепты, читать рецепты других пользователей, подписываться на интересных авторов, добавлять лучшие рецепты в избранное, а также создавать список покупок и загружать его в txt формате. Также присутствует файл docker-compose, позволяющий , быстро развернуть контейнер базы данных (PostgreSQL), контейнер проекта django + gunicorn и контейнер nginx
**
## Kак запустить
git clone https://github.com/AndreyST98/foodgram-project-react.git Для добавления файла .env с настройками базы данных на сервер необходимо:
### Установить соединение с сервером по протоколу ssh:
ssh username@xx.xxx.xxx.xxx Где username - имя пользователя, под которым будет выполнено подключение к серверу.

xx.xxx.xxx.xxx - IP-адрес сервера или доменное имя.

Например:

ssh server@178.154.221.180

Доступ в админку:

admin@admin.com
пароль: admin

## В папке infra проекта создать файл .env.
**
DB_ENGINE=django.db.backends.postgresql
**
DB_NAME=postgres
**
POSTGRES_USER=<имя пользователя>
**
POSTGRES_PASSWORD=<пароль>
**
DB_HOST=db
**
DB_PORT=5432
**
SECRET_KEY=<SECRET_KEY_Django>
**

## Перейти в папку infra, создать и применить миграции, собрать статику, создать суперпользователя:
**
docker-compose up -d --build
**
docker-compose exec backend python manage.py makemigrations --noinput
**
docker-compose exec backend python manage.py migrate --noinput
**
docker-compose exec backend python manage.py collectstatic --no-input
**
docker-compose exec backend python manage.py createsuperuser
**

### Об авторе
Степанюк Андрей, github.com/AndreyST98
