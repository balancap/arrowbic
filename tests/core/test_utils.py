import immutables

from arrowbic.core.utils import as_immutable, first_valid_item_in_iterable


def test__first_valid_item_in_iterable__list__proper_result() -> None:
    values = [None, 3, 2, None, 3]
    num, item, it = first_valid_item_in_iterable(values)
    assert num == 1
    assert item == 3
    assert it is values


def test__first_valid_item_in_iterable__iterator__proper_result() -> None:
    values = [None, 3, 2, None, 3]
    num, item, it = first_valid_item_in_iterable(iter(values))
    assert num == 1
    assert item == 3
    assert list(it) == values


def test__first_valid_item_in_iterable__none_iterator() -> None:
    values = [None, None, None]
    num, item, it = first_valid_item_in_iterable(iter(values))
    assert num == 3
    assert item is None
    assert it == values


def test__as_immutable__base_types() -> None:
    assert as_immutable(123) == 123
    assert as_immutable(12.3) == 12.3
    assert as_immutable("123") == "123"
    assert as_immutable(b"123") == b"123"
    assert as_immutable(None) is None


def test__as_immutable__list_input() -> None:
    assert as_immutable([1, 2, 3]) == (1, 2, 3)
    assert as_immutable((1, 2, 3)) == (1, 2, 3)


def test__as_immutable__dict_input() -> None:
    assert as_immutable({1: "1", 2: "2"}) == immutables.Map({1: "1", 2: "2"})
