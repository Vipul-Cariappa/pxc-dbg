import pxctest


def test_dummy():
    test_string = "Hello World"
    assert pxctest.print_stdout(test_string) == len(test_string) + 1
    assert pxctest.print_stdout("") == 1
    c = pxctest.Custom(
        19
    )  # FIXME: __init__; Look at https://discuss.python.org/t/92391
    assert c.getn() == 19


if __name__ == "__main__":
    test_dummy()
