import sys
import pathlib
from tempfile import NamedTemporaryFile
import pytest

# הוספת הנתיב של It1_interfaces לנתיב החיפוש
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent / "It1_interfaces"))
from Moves import Moves



@pytest.fixture
def sample_moves_file():
    # יוצרים קובץ זמני עם תנועות לדוגמה
    with NamedTemporaryFile('w+', delete=False) as f:
        f.write("1,0\n")
        f.write("0,1\n")
        f.write("-1,0\n")
        f.write("0,-1\n")
        f.flush()
        yield pathlib.Path(f.name)


def test_moves_loading(sample_moves_file):
    m = Moves(sample_moves_file, (8, 8))
    assert m.moves == [(1, 0), (0, 1), (-1, 0), (0, -1)]


def test_get_moves_center(sample_moves_file):
    m = Moves(sample_moves_file, (8, 8))
    result = m.get_moves(4, 4)
    expected = [(5, 4), (4, 5), (3, 4), (4, 3)]
    assert sorted(result) == sorted(expected)


def test_get_moves_edge(sample_moves_file):
    m = Moves(sample_moves_file, (8, 8))
    result = m.get_moves(0, 0)
    expected = [(1, 0), (0, 1)]
    assert sorted(result) == sorted(expected)


def test_get_moves_out_of_bounds(sample_moves_file):
    m = Moves(sample_moves_file, (2, 2))
    result = m.get_moves(0, 0)
    # רק תנועות שמובילות לתוך (2x2) לוח ייחשבו חוקיות
    expected = [(1, 0), (0, 1)]
    assert sorted(result) == sorted(expected)
