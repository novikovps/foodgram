# Foodgram (Учебный проект)

Foodgram - «Продуктовый помощник» - это онлайн-сервис, на котором пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.


## Технологии, используемые в backend
В backend проекта используются следующие технологии и фреймворки:
- [Python] 3.10.12
- [Django] 3.2
- [Django DRF] 3.12.4
- [Gunicorn] 20.1.0
- [Nginx] 1.21.3
- [PostgreSQL] 13.0
- а так же ряд дополнительных библиотек для django (подробнее в файле backend/requirements.txt).


## Установка
> Порядок установки приведён для ОС `Ubuntu 22.04 LTS`.

Предварительно рекомендуется установить обновления:
```sh
sudo apt update && sudo apt upgrade -y
```
Добавьте официальный репозиторий docker:
```sh
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```
Установите docker:
```sh
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
```
Установите git:
```sh
sudo apt install git -y
```
Клонируйте репозиторий:
```sh
git clone https://github.com/novikovps/foodgram.git
```
Перейдите в директорию infra и создайте файл .env с параметрами настроек (пример заполенния приведён в файле .env.example):
```sh
cd foodgram/infra/
nano .env
```
Указав параметры в .env, запустите контейнеры командой:
```sh
sudo docker compose up -d
```
## Первичная настройка

После запуска контейнеров необходимо выполнить миграции
```sh
sudo docker compose exec backend python manage.py migrate
```
создать суперпользователя и собрать статику
```sh
sudo docker compose exec backend python manage.py createsuperuser
sudo docker compose exec backend python manage.py collectstatic
```
импортировать теги и ингридиенты (опционально, но рекомендуется)
```sh
sudo docker compose exec backend python manage.py import_tags
sudo docker compose exec backend python manage.py import_ingredients
```
На этом установка и настройка завершены.

[Python]: <https://www.python.org>
[Django]: <https://www.djangoproject.com>
[Django DRF]: <https://www.django-rest-framework.org>
[Gunicorn]: <https://gunicorn.org>
[Nginx]: <https://www.nginx.com>
[PostgreSQL]: <https://www.postgresql.org>
