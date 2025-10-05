# Business Management System

## Запуск

Создайте `.env` файл и скопируйте в него содержимое `.env.example` (при необходимости измените содержимое).
Все сервисы обернуты в docker и запускаются через команды Makefile.

```bash
make up                 # запуск всех контейнеров
make watch              # запуск в режиме разработки с синхронизацией файлов
make stop               # остановка контейнеров
make rm                 # удаление контейнеров
make clear              # полная очистка проекта (используйте после завершения)
```

## API

По умолчанию приложение запускается на 8000 порту.

```bash
127.0.0.1:8000/api/docs                  # документация openapi
127.0.0.1:8000/api/auth/register         # зарегистрировать пользователя
127.0.0.1:8000/api/auth/login            # получить токен
127.0.0.1:8000/api/auth/logout           # добавить токен в черный список
127.0.0.1:8000/api/teams                 # управление командами
127.0.0.1:8000/api/teams/{team_id}/tasks                    # управление задачами
127.0.0.1:8000/api/teams/{team_id}/meetings                 # управление собраниями
127.0.0.1:8000/api/teams/{team_id}/calendar                 # календарь команды
127.0.0.1:8000/api/teams/{team_id}/tasks/{task_id}/comments # управление комментариями
```

Полный набор конечных точек api можно посмотреть через документацию openapi.

Все методы имеют подробную документацию для ознакомления.

Большинство конечных точек требуют заголовок авторизации в который необходимо подставить токен пользователя полученный через соответсвующий метод. После получения токена на странице документации воспользуйтесь кнопкой Authorize для автоматического добавления заголовка в запросы.

## Примеры запросов

**Регистрация**
```bash
# Запрос
curl -X 'POST' \
  'http://127.0.0.1:8000/api/auth/register' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "string",
  "email": "user@example.com",
  "password": "string",
  "first_name": "string",
  "last_name": "string"
}'

# Ответ
{
  "success": true,
  "detail": "The user has been successfully created",
  "user_id": 1
}
```

**Логин**
```bash
# Запрос
curl -X 'POST' \
  'http://127.0.0.1:8000/api/auth/login' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "email": "user@example.com",
  "password": "string"
}'

# Ответ
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "token_type": "bearer"
}
```

**Создание команды**
```bash
# Запрос
curl -X 'POST' \
  'http://127.0.0.1:8000/api/teams/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6...' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "string"
}'

# Ответ
{
  "success": true,
  "detail": "The team has been successfully created",
  "team_id": 1
}
```

## Роли и права

Пользователь в команде может быть представлен тремя ролями: пользователь, менеджер и админ. Когда пользователь создает команду, он автоматически назначается администратором этой команды.

- **Пользователь** может просматривать информацию в команде и оставлять комментарии к задачам. Пользователей можно назначать на задачи или встречи.
- **Менеджер** может создавать задачи и встречи, а так же редактировать их.
- **Админ** имеет все права менеджера, но так же может управлять участниками команды.


**Обозначения ролей в для API**
```bash
"u" # Пользователь
"m" # Менеджер
"a" # Админ
```

**Пример запроса на добавление пользователя в команду или назначение роли**
```bash
# Запрос
curl -X 'POST' \
  'http://127.0.0.1:8000/api/teams/1/users' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6...' \
  -H 'Content-Type: application/json' \
  -d '{
  "user_id": 1,
  "role": "u"
}'

# Ответ
{
  "success": true,
  "detail": "The user has been successfully added to the team"
}
```

## Админ-панель

Для реализации админ-панели используется инструмент SQLAdmin. Для входа в админ-панель используйте значения переменных окружения ADMIN_NAME и ADMIN_PASS (по умолчанию admin / admin)

```bash
127.0.0.1:8000/admin    # доступ к админ-панели
```

## Тесты

Команды для тестов.

```bash
make build-test         # собрать образы для тестов
make run-test           # запустить тесты
make clear-test         # полностью очистить образы для тестов
```

## Миграции

Для миграций используется Alembic. Существующие миграции применяются автоматически при развертывании приложения. Миграции хранятся в директории `src/app/migrations/versions`.

```bash
make makemigration name="migration name"    # создание миграции
```

## Frontend

```bash
127.0.0.1:8000/                   # Главная страница
127.0.0.1:8000/register/          # Регистрация
127.0.0.1:8000/login/             # Вход
127.0.0.1:8000/profile/           # Профиль
127.0.0.1:8000/teams/{team_id}/   # Команда
127.0.0.1:8000/teams/{team_id}/tasks/{task_id}/         # Задача и комментарии
127.0.0.1:8000/teams/{team_id}/meetings/{meeting_id}/   # Обновление встречи (для менеджеров)
127.0.0.1:8000/teams/{team_id}/calendar/                # Календарь
```
