"""Проверки API: ответы, ошибки и изменения в базе."""

import pytest

from opinions_app import db
from opinions_app.models import Opinion


def serialized(app, opinion):
    """Готовит словарь мнения в формате JSON приложения."""
    return app.json.loads(app.json.dumps(opinion.to_dict()))


def test_get_empty_list(client):
    """Если база пуста, API возвращает пустой список и код 200."""
    response = client.get('/api/opinions/')
    assert response.status_code == 200, (
        'Убедитесь, что GET /api/opinions/ возвращает код 200.'
    )
    assert response.json == {'opinions': []}, (
        'Убедитесь, что для пустой базы API возвращает словарь с пустым '
        'списком opinions.'
    )


def test_get_all_opinions(app, client, make_opinion):
    """API возвращает все мнения со всеми полями."""
    opinions = [make_opinion(), make_opinion(title='Arrival')]
    response = client.get('/api/opinions/')
    assert response.status_code == 200, (
        'Убедитесь, что GET /api/opinions/ возвращает код 200.'
    )
    assert sorted(response.json['opinions'], key=lambda item: item['id']) == [
        serialized(app, opinion) for opinion in opinions
    ], (
        'Убедитесь, что opinions содержит все мнения со всеми полями.'
    )


def test_filter_title(client, make_opinion):
    """Фильтр по названию не учитывает регистр букв."""
    for name in ('Interstellar', 'Interstellar', 'Arrival'):
        make_opinion(title=name)
    for title, count in [
        ('INTERSTELLAR', 2), ('interstellar', 2), ('Arrival', 1),
        ('missing', 0), ('', 3),
    ]:
        response = client.get('/api/opinions/', query_string={'title': title})
        assert response.status_code == 200, (
            f'Убедитесь, что запрос с фильтром title={title!r} возвращает '
            'код 200.'
        )
        opinions = response.json['opinions']
        assert len(opinions) == count, (
            f'Убедитесь, что фильтр title={title!r} возвращает {count} мнений.'
        )
        assert (
            all(title.lower() in item['title'].lower() for item in opinions)
        ), (
            'Убедитесь, что фильтр title не учитывает регистр и не '
            'возвращает лишние мнения.'
        )


@pytest.mark.parametrize('extra', [
    {}, {'source': 'https://example.com', 'added_by': 'Alice'},
])
def test_create_opinion(app, client, extra):
    """POST сохраняет мнение и возвращает его с кодом 201."""
    data = {'title': 'Фильм', 'text': 'Мнение о фильме', **extra}
    response = client.post('/api/opinions/', json=data)
    assert response.status_code == 201, (
        'Убедитесь, что POST /api/opinions/ возвращает код 201.'
    )
    db.session.expire_all()
    opinion = Opinion.query.one()
    assert response.json == {'opinion': serialized(app, opinion)}, (
        'Убедитесь, что POST возвращает созданное мнение под ключом opinion.'
    )
    for field, value in data.items():
        assert getattr(opinion, field) == value, (
            f'Убедитесь, что POST сохраняет переданное значение поля {field}.'
        )
    assert opinion.timestamp is not None, (
        'Убедитесь, что у созданного мнения заполнен timestamp.'
    )


def test_create_missing_required_fields(client):
    """Без title или text API возвращает ошибку и не создаёт мнение."""
    for data in [{}, {'title': 'Movie'}, {'text': 'Review'}]:
        response = client.post('/api/opinions/', json=data)
        assert response.status_code == 400, (
            'Убедитесь, что POST без title или text возвращает код 400. '
            f'Данные: {data!r}.'
        )
        assert response.json == {'error': 'Поля title и text обязательны'}, (
            'Убедитесь, что ошибка содержит текст «Поля title и text '
            'обязательны».'
        )
        assert Opinion.query.count() == 0, (
            'Убедитесь, что запрос без обязательных полей не создаёт мнение.'
        )


def test_create_json_null(client):
    """Если тело JSON равно null, API возвращает ошибку."""
    response = client.post(
        '/api/opinions/', data='null', content_type='application/json',
    )
    assert response.status_code == 400, (
        'Убедитесь, что POST с JSON null возвращает код 400.'
    )
    assert response.json == {'error': 'Поля title и text обязательны'}, (
        'Убедитесь, что для JSON null возвращается ошибка «Поля title и '
        'text обязательны».'
    )
    assert Opinion.query.count() == 0, (
        'Убедитесь, что POST с JSON null не создаёт мнение.'
    )


def test_get_opinion(app, client, make_opinion):
    """GET по id возвращает нужное мнение."""
    opinion = make_opinion()
    make_opinion()
    response = client.get(f'/api/opinions/{opinion.id}/')
    assert response.status_code == 200, (
        'Убедитесь, что GET существующего мнения возвращает код 200.'
    )
    assert response.json == {'opinion': serialized(app, opinion)}, (
        'Убедитесь, что GET возвращает нужное мнение под ключом opinion.'
    )


def test_missing_opinion(client):
    """Для несуществующего id API возвращает ошибку 404."""
    for method in ['get', 'patch', 'delete']:
        response = getattr(client, method)(
            '/api/opinions/999/', json={'title': 'New'},
        )
        assert response.status_code == 404, (
            f'Убедитесь, что {method.upper()} для отсутствующего мнения '
            'возвращает код 404.'
        )
        assert response.json == {'error': 'Мнение не найдено'}, (
            f'Убедитесь, что {method.upper()} возвращает ошибку «Мнение не '
            'найдено».'
        )


@pytest.mark.parametrize('data', [
    {'title': 'New'}, {'text': 'New review'}, {'source': 'New source'},
    {'added_by': 'Bob'}, {'source': None, 'added_by': None}, {},
    {'title': 'New', 'text': 'New review', 'source': 'URL', 'added_by': 'Bob'},
    {'id': 999, 'timestamp': 'invalid', 'unknown': 'ignored'},
])
def test_patch_opinion(app, client, make_opinion, data):
    """PATCH меняет только переданные разрешённые поля."""
    opinion = make_opinion(source='Original source', added_by='Alice')
    other = make_opinion()
    other_before = other.to_dict()
    expected = opinion.to_dict()
    expected.update({key: value for key, value in data.items()
                     if key in ('title', 'text', 'source', 'added_by')})
    response = client.patch(f'/api/opinions/{opinion.id}/', json=data)
    assert response.status_code == 200, (
        'Убедитесь, что PATCH существующего мнения возвращает код 200. '
        f'Данные: {data!r}.'
    )
    db.session.expire_all()
    assert opinion.to_dict() == expected, (
        'Убедитесь, что PATCH меняет только переданные разрешённые поля. '
        f'Данные: {data!r}.'
    )
    assert other.to_dict() == other_before, (
        'Убедитесь, что PATCH не изменяет другое мнение.'
    )
    assert response.json == {'opinion': serialized(app, opinion)}, (
        'Убедитесь, что PATCH возвращает обновлённое мнение под ключом '
        'opinion.'
    )


def test_delete_opinion(client, make_opinion):
    """DELETE удаляет нужное мнение и возвращает пустое тело."""
    opinion_id = make_opinion().id
    other_id = make_opinion().id
    response = client.delete(f'/api/opinions/{opinion_id}/')
    assert response.status_code == 204, (
        'Убедитесь, что DELETE существующего мнения возвращает код 204.'
    )
    assert response.data == b'', (
        'Убедитесь, что DELETE возвращает пустое тело ответа.'
    )
    db.session.expire_all()
    assert db.session.get(Opinion, opinion_id) is None, (
        'Убедитесь, что DELETE удаляет мнение из базы.'
    )
    assert db.session.get(Opinion, other_id) is not None, (
        'Убедитесь, что DELETE не удаляет другие мнения.'
    )
    assert client.get(f'/api/opinions/{opinion_id}/').status_code == 404, (
        'Убедитесь, что удалённое мнение больше недоступно по GET.'
    )


def test_random_empty(client):
    """Если база пуста, API случайного мнения возвращает ошибку 404."""
    response = client.get('/api/opinions/random/')
    assert response.status_code == 404, (
        'Убедитесь, что случайное мнение для пустой базы возвращает код 404.'
    )
    assert response.json == {'error': 'В базе нет мнений'}, (
        'Убедитесь, что ошибка содержит текст «В базе нет мнений».'
    )


def test_random_single(app, client, make_opinion):
    """Если мнение одно, API случайного мнения возвращает его."""
    opinion = make_opinion()
    response = client.get('/api/opinions/random/')
    assert response.status_code == 200, (
        'Убедитесь, что GET /api/opinions/random/ возвращает код 200.'
    )
    assert response.json == {'opinion': serialized(app, opinion)}, (
        'Убедитесь, что API возвращает единственное мнение под ключом opinion.'
    )
