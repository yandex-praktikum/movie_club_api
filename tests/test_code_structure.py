"""Базовые проверки файлов проекта, настроек и обработчиков API."""

import os
import subprocess
import sys
from pathlib import Path

import opinions_app


ROOT = Path(opinions_app.__file__).resolve().parents[1]


def test_required_files_exist():
    """В проекте есть основные файлы приложения."""
    for filename in [
        'settings.py',
        'opinions_app/__init__.py',
        'opinions_app/models.py',
        'opinions_app/views.py',
        'opinions_app/api_views.py',
    ]:
        assert (ROOT / filename).is_file(), (
            f'Не найден обязательный файл проекта: {filename}.'
        )


def test_settings_use_environment_variables():
    """Настройки берут адрес базы и секретный ключ из окружения."""
    environment = os.environ.copy()
    environment.update(
        DATABASE_URI='sqlite:///:memory:', SECRET_KEY='configuration-test-key',
    )
    result = subprocess.run(
        [sys.executable, '-c',
         'from settings import Config; '
         'assert Config.SQLALCHEMY_DATABASE_URI == "sqlite:///:memory:", '
         '"Убедитесь, что адрес базы берётся из DATABASE_URI"; '
         'assert Config.SECRET_KEY == "configuration-test-key", '
         '"Убедитесь, что ключ берётся из SECRET_KEY"'],
        cwd=ROOT, env=environment, capture_output=True, text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        'Убедитесь, что Config берёт адрес базы из DATABASE_URI, а ключ из '
        f'SECRET_KEY. Ошибка: {result.stderr}'
    )


def test_dotenv_is_ignored():
    """Файл .env указан в .gitignore."""
    path = ROOT / '.gitignore'
    assert path.is_file(), 'Не найден файл .gitignore в корне проекта.'
    lines = path.read_text(encoding='utf-8').splitlines()
    assert '.env' in {line.strip() for line in lines}, (
        'Убедитесь, что .env добавлен в .gitignore.'
    )


def test_api_routes(app):
    """Пути и имена маршрутов сохранены, обработчики лежат в api_views."""
    for path, method, endpoint in [
        ('/api/opinions/', 'GET', 'get_opinions'),
        ('/api/opinions/', 'POST', 'add_opinion'),
        ('/api/opinions/<int:id>/', 'GET', 'get_opinion'),
        ('/api/opinions/<int:id>/', 'PATCH', 'update_opinion'),
        ('/api/opinions/<int:id>/', 'DELETE', 'delete_opinion'),
        ('/api/opinions/random/', 'GET', 'get_random_opinion'),
    ]:
        rules = [rule for rule in app.url_map.iter_rules()
                 if rule.endpoint == endpoint]
        assert (
            any(rule.rule == path and method in rule.methods for rule in rules)
        ), (
            f'Не найден маршрут {method} {path} с именем {endpoint}.'
        )
        assert (
            app.view_functions[endpoint].__module__ == 'opinions_app.api_views'
        ), (
            f'Убедитесь, что обработчик {endpoint} находится в api_views.py.'
        )
