from arrowbic.core.utils import first_valid_item_in_iterable


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
