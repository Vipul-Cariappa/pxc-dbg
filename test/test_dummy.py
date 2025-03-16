import pxctest


def test_dummy():
    test_string = "Hello World"
    assert pxctest.print_stdout(test_string) == len(test_string) + 1
