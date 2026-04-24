 Flask REST API (Lab 3)
 
 Описание

Это REST API на Flask с авторизацией через JWT, cookies и PostgreSQL.
Реализованы:

регистрация и логин пользователей
защита маршрутов через middleware
работа с задачами (CRUD)
хэширование паролей
refresh/access токены
soft delete
 Технологии
Python 3.12
Flask
SQLAlchemy
Alembic (Flask-Migrate)
PostgreSQL
Docker / Docker Compose
JWT (PyJWT)

 Запуск проекта
1. Очистка (если нужно)
docker-compose down -v
2. Запуск
docker-compose up --build
3. Миграции
docker exec -it <container_name> flask db upgrade
4. Проверка
http://localhost:4200
 Авторизация

Используется:

JWT (access + refresh)
cookies
 API Endpoints
 Регистрация
 
## Авторизация через Yandex ID

В проекте реализована авторизация через внешний OAuth2-провайдер **Yandex ID**.  
Используется поток **Authorization Code Grant**.

### Настройка приложения в Yandex OAuth

Для работы входа через Яндекс необходимо создать приложение в кабинете Yandex ID OAuth:

1. Перейти в консоль Yandex OAuth.
2. Создать приложение типа **«Для авторизации пользователей»**.
3. В качестве платформы выбрать **«Веб-сервисы»**.
4. Указать Redirect URI:

```text
http://localhost:4200/auth/oauth/yandex/callback

POST

/auth/register
{
  "email": "test@mail.com",
  "password": "12345678"
}
 Логин

POST

/auth/login

 сохраняет cookies:

access_token
refresh_token
 Кто я

GET

/auth/whoami
 Logout

POST

/auth/logout
 Задачи
 Создать задачу

POST

/tasks
{
  "title": "Task 1",
  "description": "Demo",
  "status": "new"
}
 Получить список задач

GET

/tasks?page=1&limit=10
 Удалить задачу

DELETE

/tasks/{task_id}

 soft delete

 Безопасность
Хэширование

Пароли не хранятся в открытом виде:

используется salt
SHA-256
JWT
access token — короткий (15 мин)
refresh token — длинный (7 дней)
Middleware

Проверяет:

наличие access_token в cookies
валидность JWT
существование пользователя
 Особенности
soft delete через deleted_at
пагинация задач
разделение логики:
routes
services
models
 Тестирование (Postman)

Порядок:

/auth/register

/auth/login

/auth/whoami

/tasks

/tasks?page=1&limit=10
