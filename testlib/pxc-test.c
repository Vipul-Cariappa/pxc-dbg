#include "pxc-test.h"
#include <Python.h>
#include <stdio.h>

static PyMethodDef pxctestMethods[] = {
    {"print_stdout", print_stdout, METH_VARARGS, "Prints."},
    {NULL, NULL, 0, NULL},
};

static struct PyModuleDef pxctestModule = {
    PyModuleDef_HEAD_INIT,
    "pxctest",
    "Python C Extension Module to test pxc-dbg",
    -1,
    pxctestMethods,
};

PyMODINIT_FUNC PyInit_pxctest(void) {
    return PyModule_Create(&pxctestModule);
}

static PyObject *print_stdout(PyObject *self, PyObject *args) {
    const char *command;
    int sts;

    if (!PyArg_ParseTuple(args, "s", &command))
        return NULL;
    sts = fprintf(stdout, "%s\n", command);
    return PyLong_FromLong(sts);
}
