### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone 
```

```
cd movie_club_api
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

```
source venv/bin/activate
```
или для пользователей Windows

```
source venv/Scripts/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Настроить переменные окружения(создать файл .env):
```
FLASK_APP=opinions_app
FLASK_DEBUG=1
DATABASE_URI=sqlite:///db.sqlite3
SECRET_KEY=YOUR_SECRET_KEY
```

Описать модели БД в файле models.py

Инициализировать и применить миграции (создать таблицы в БД):
```
flask db init
flask db migrate -m "initial migration"
flask db upgrade
```

Загрузить начальные данные из CSV:
```
flask load_opinions
```

Запустить проект:

```
flask run
```