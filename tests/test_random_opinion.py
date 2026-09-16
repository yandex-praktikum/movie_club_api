"""Проверки функции random_opinion."""

import inspect

import pytest

from opinions_app import views


def test_random_opinion_has_no_arguments():
    """Функция не принимает аргументы."""
    assert not inspect.signature(views.random_opinion).parameters, (
        'Убедитесь, что random_opinion() не принимает аргументы.'
    )


def test_random_opinion_empty(app):
    """Для пустой базы функция возвращает None."""
    assert views.random_opinion() is None, (
        'Убедитесь, что random_opinion() возвращает None для пустой базы.'
    )


def test_random_opinion_single(make_opinion):
    """Если мнение одно, функция возвращает его."""
    opinion = make_opinion()
    assert views.random_opinion().id == opinion.id, (
        'Убедитесь, что random_opinion() возвращает единственное мнение в '
        'базе.'
    )


@pytest.mark.parametrize('offset', [0, 1, 2])
def test_random_opinion_uses_random_offset(make_opinion, monkeypatch, offset):
    """Случайная позиция определяет, какое мнение вернётся."""
    opinions = [make_opinion() for _ in range(3)]

    def choose_offset(count):
        """Проверяет число мнений и задаёт результат случайного выбора."""
        assert count == len(opinions), (
            'Убедитесь, что случайный выбор учитывает все мнения в базе.'
        )
        return offset

    monkeypatch.setattr(views, 'randrange', choose_offset)
    assert views.random_opinion().id == opinions[offset].id, (
        'Убедитесь, что random_opinion() возвращает мнение на выбранной '
        f'позиции {offset}.'
    )
