from dynamo import db

def test_db():
    i1 = db()
    i2 = db()
    i3 = db()
    assert id(i1) == id(i2)
    assert id(i1) == id(i3)
    assert id(i2) == id(i3)
    assert i1 is i2
    assert i1 is i3
    assert i2 is i3
    assert i3 is i2
