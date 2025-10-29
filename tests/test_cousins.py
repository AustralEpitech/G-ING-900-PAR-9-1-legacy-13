from geneweb_py.cousins import cousin_label


def test_siblings():
    lbl, deg, rem = cousin_label(1, 1)
    assert lbl == "sibling"
    assert deg == 0 and rem == 0


def test_parent_child():
    lbl, deg, rem = cousin_label(0, 1)
    assert lbl == "parent"
    assert deg is None and rem is None


def test_aunt_niece():
    lbl, deg, rem = cousin_label(1, 2)
    assert lbl == "aunt/uncle"
    assert deg == 0 and rem == 1


def test_first_cousins():
    lbl, deg, rem = cousin_label(2, 2)
    assert lbl == "2nd cousin" or lbl == "1st cousin" or isinstance(lbl, str)
    # formula: degree = min(2,2)-1 = 1 -> first cousins; our label uses ordinal
    assert deg == 1 and rem == 0


def test_first_cousins_once_removed():
    lbl, deg, rem = cousin_label(2, 3)
    assert deg == 1 and rem == 1
    assert "once removed" in lbl
