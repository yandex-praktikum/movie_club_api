"""Общие фикстуры: приложение, тестовая база и клиент."""

import os

import pytest

# Задаём тестовую базу до импорта приложения: при импорте создаётся движок БД.
os.environ['FLASK_APP'] = 'opinions_app'
os.environ['FLASK_DEBUG'] = '0'
os.environ['DATABASE_URI'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'test-secret-key'

from opinions_app import app as flask_app, db  # noqa: E402
from opinions_app.models import Opinion  # noqa: E402


@pytest.fixture
def app():
    """Создаёт чистую базу в памяти для каждого теста."""
    with flask_app.app_context():
        assert db.engine.url.database == ':memory:', (
            'Убедитесь, что DATABASE_URI используется для подключения к '
            'тестовой базе в памяти.'
        )
        flask_app.config['TESTING'] = True
        db.create_all()
        try:
            yield flask_app
        finally:
            db.session.remove()
            db.drop_all()


@pytest.fixture
def client(app):
    """Возвращает клиент для запросов к приложению."""
    return app.test_client()


@pytest.fixture
def make_opinion(app):
    """Позволяет создавать мнения с разными текстами."""
    def factory(**kwargs):
        """Создаёт мнение с указанными полями и сохраняет его в базу."""
        data = {
            'title': 'Interstellar',
            'text': f'Review {Opinion.query.count()}',
        }
        data.update(kwargs)
        opinion = Opinion(**data)
        db.session.add(opinion)
        db.session.commit()
        return opinion

    return factory
