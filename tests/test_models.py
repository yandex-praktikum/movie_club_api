"""Проверки полей и методов модели Opinion."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.exc import IntegrityError

from opinions_app import db
from opinions_app.models import Opinion


def test_model_schema():
    """Поля модели имеют нужные типы, длины и ограничения."""
    assert issubclass(Opinion, db.Model), (
        'Убедитесь, что Opinion наследуется от db.Model.'
    )
    columns = Opinion.__table__.columns
    for name in ('id', 'title', 'text', 'source', 'timestamp', 'added_by'):
        assert name in columns, f'Не найдено поле {name} в модели Opinion.'
    assert isinstance(columns.id.type, Integer), (
        'Убедитесь, что поле id имеет тип Integer.'
    )
    assert columns.id.primary_key, (
        'Убедитесь, что поле id является первичным ключом.'
    )
    for name, length, nullable in (
        ('title', 128, False), ('source', 256, True), ('added_by', 64, True),
    ):
        column = columns[name]
        assert isinstance(column.type, String), (
            f'Убедитесь, что поле {name} имеет тип String.'
        )
        assert column.type.length == length, (
            f'Убедитесь, что длина поля {name} равна {length}.'
        )
        assert column.nullable is nullable, (
            f'Убедитесь, что для поля {name} указано nullable={nullable}.'
        )
    assert isinstance(columns.text.type, Text), (
        'Убедитесь, что поле text имеет тип Text.'
    )
    assert columns.text.nullable is False, (
        'Убедитесь, что для поля text указано nullable=False.'
    )
    assert columns.text.unique, (
        'Убедитесь, что поле text уникально: unique=True.'
    )
    assert isinstance(columns.timestamp.type, DateTime), (
        'Убедитесь, что поле timestamp имеет тип DateTime.'
    )
    assert columns.timestamp.index, (
        'Убедитесь, что для поля timestamp задан индекс.'
    )
    assert columns.timestamp.default is not None, (
        'Убедитесь, что у timestamp задано значение по умолчанию.'
    )
    assert callable(columns.timestamp.default.arg), (
        'Убедитесь, что значение timestamp по умолчанию вычисляется функцией.'
    )


def test_timestamp_defaults_to_current_utc(make_opinion):
    """При сохранении мнения ставится текущее время UTC."""
    before = datetime.now(UTC)
    opinion = make_opinion()
    after = datetime.now(UTC)
    actual = opinion.timestamp
    assert isinstance(actual, datetime), (
        'Убедитесь, что timestamp заполняется датой и временем.'
    )
    if actual.tzinfo is None:
        actual = actual.replace(tzinfo=UTC)
    assert before - timedelta(seconds=1) <= actual <= after, (
        'Убедитесь, что timestamp получает текущее время UTC при сохранении.'
    )


def test_required_columns_reject_null(app):
    """База не принимает None в обязательных полях."""
    for field in ['title', 'text']:
        data = {'title': 'Movie', 'text': 'Review', field: None}
        db.session.add(Opinion(**data))
        rejected = False
        try:
            db.session.commit()
        except IntegrityError:
            rejected = True
        finally:
            db.session.rollback()
        assert rejected, (
            f'Убедитесь, что поле {field} не допускает None: nullable=False.'
        )


def test_text_is_unique(make_opinion):
    """Нельзя сохранить два мнения с одинаковым текстом."""
    make_opinion(text='Same review')
    rejected = False
    try:
        make_opinion(text='Same review')
    except IntegrityError:
        rejected = True
    finally:
        db.session.rollback()
    assert rejected, 'Убедитесь, что поле text уникально: unique=True.'


def test_optional_fields_default_to_none(make_opinion):
    """Необязательные поля можно не заполнять."""
    opinion = make_opinion()
    assert opinion.source is None, (
        'Убедитесь, что source можно не заполнять.'
    )
    assert opinion.added_by is None, (
        'Убедитесь, что added_by можно не заполнять.'
    )


def test_to_dict():
    """Метод to_dict возвращает все поля и их значения."""
    data = dict(
        id=42, title='Movie', text='Review', source='https://example.com',
        timestamp=datetime(2026, 1, 1, tzinfo=UTC), added_by='Alice',
    )
    assert Opinion(**data).to_dict() == data, (
        'Убедитесь, что to_dict() возвращает все поля Opinion с правильными '
        'значениями.'
    )


def test_from_dict_updates_only_supplied_field():
    """Метод from_dict меняет только переданное поле."""
    for field in ['title', 'text', 'source', 'added_by']:
        opinion = Opinion(
            title='Movie', text='Review', source='Source', added_by='A',
        )
        expected = opinion.to_dict()
        expected[field] = 'Updated'
        opinion.from_dict({field: 'Updated'})
        assert opinion.to_dict() == expected, (
            'Убедитесь, что from_dict() меняет только переданное поле '
            f'{field}.'
        )


def test_from_dict_ignores_protected_and_unknown_fields():
    """Метод from_dict не меняет id, время и неизвестные поля."""
    opinion = Opinion(
        id=42, title='Movie', text='Review', timestamp=datetime.now(UTC),
    )
    expected = opinion.to_dict()
    opinion.from_dict({'id': 99, 'timestamp': 'invalid', 'unknown': 'value'})
    opinion.from_dict({})
    assert opinion.to_dict() == expected, (
        'Убедитесь, что from_dict() не меняет id, timestamp и поля, '
        'отсутствующие в данных.'
    )
    assert not hasattr(opinion, 'unknown'), (
        'Убедитесь, что from_dict() игнорирует неизвестные поля.'
    )


def test_from_dict_clears_optional_fields():
    """Значение None очищает необязательные поля."""
    opinion = Opinion(source='Source', added_by='Alice')
    opinion.from_dict({'source': None, 'added_by': None})
    assert opinion.source is None, (
        'Убедитесь, что from_dict() позволяет очистить source значением None.'
    )
    assert opinion.added_by is None, (
        'Убедитесь, что from_dict() позволяет очистить added_by значением '
        'None.'
    )
