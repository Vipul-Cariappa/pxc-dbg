#include "pxc.h"
#include "longobject.h"
#include <Python.h>


static PyMethodDef pxcExtensionMethods[] = {
    {"resolve_location", resolve_location, METH_VARARGS,
     "Resolve address of C function"},
    {NULL, NULL, 0, NULL},
};

static struct PyModuleDef pxcExtensionModule = {
    PyModuleDef_HEAD_INIT,
    "pxc_extension",
    "Python C Extension Helper Module for pxc",
    -1,
    pxcExtensionMethods,
};

PyMODINIT_FUNC PyInit_pxc_extension(void) {
    return PyModule_Create(&pxcExtensionModule);
}

static PyObject *resolve_location(PyObject *self, PyObject *args) {
    const char *name;
    const PyObject *func;

    if (!PyArg_ParseTuple(args, "sO", &name, &func))
        return NULL;

    int flags = PyCFunction_GET_FLAGS(func);
    if (!(flags & METH_VARARGS)) {
        Py_ssize_t offset = Py_TYPE(func)->tp_vectorcall_offset;
        if (offset <= 0)
            return PyLong_FromLong(0);

        void *func_addr = NULL;
        memcpy(&func_addr, (char *)func + offset, sizeof(func_addr));
        return PyLong_FromVoidPtr(func_addr);
    }

    PyCFunction meth = PyCFunction_GET_FUNCTION(func);
    return PyLong_FromVoidPtr(meth);
}
