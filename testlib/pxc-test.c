#include "pxc-test.h"
#include <Python.h>
#include <stddef.h>
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

typedef struct {
    PyObject_HEAD int n;
} CustomObject;

static int Custom_init(CustomObject *self, PyObject *args, PyObject *kwds) {
    int d = 0;
    if (!PyArg_ParseTuple(args, "i", &d))
        return 1;
    self->n = d;
    return 0;
}

static PyObject *Custom_getn(CustomObject *self, PyObject *Py_UNUSED(ignored)) {
    return PyLong_FromLong(self->n);
}

static PyMemberDef Custom_members[] = {
    {"n", Py_T_INT, offsetof(CustomObject, n), 0, "The n integer"},
    {NULL} /* Sentinel */
};

static PyMethodDef Custom_methods[] = {
    {"getn", (PyCFunction)Custom_getn, METH_NOARGS, "returns n"},
    {NULL} /* Sentinel */
};

static PyTypeObject CustomType = {
    .ob_base = PyVarObject_HEAD_INIT(NULL, 0).tp_name = "pxctest.Custom",
    .tp_doc = PyDoc_STR("Custom objects"),
    .tp_basicsize = sizeof(CustomObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = PyType_GenericNew,
    .tp_init = (initproc)Custom_init,
    .tp_members = Custom_members,
    .tp_methods = Custom_methods,
};

PyMODINIT_FUNC PyInit_pxctest(void) {
    PyObject *m;
    if (PyType_Ready(&CustomType) < 0)
        return NULL;

    m = PyModule_Create(&pxctestModule);
    if (m == NULL)
        return NULL;

    if (PyModule_AddObjectRef(m, "Custom", (PyObject *)&CustomType) < 0) {
        Py_DECREF(m);
        return NULL;
    }
    return m;
}

static PyObject *print_stdout(PyObject *self, PyObject *args) {
    const char *command;
    int sts;

    if (!PyArg_ParseTuple(args, "s", &command))
        return NULL;
    sts = fprintf(stdout, "%s\n", command);
    return PyLong_FromLong(sts);
}
