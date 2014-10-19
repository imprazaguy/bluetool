#include "bluez_ext.h"
#include <bluetooth/bluetooth.h>
#include <bluetooth/hci.h>
#include <sys/uio.h>

#define acl_flag_pack(pb, bc) ((pb) | ((bc) << 2))

int hci_send_acl(int dd, uint16_t handle, uint8_t pb_flag, uint8_t bc_flag, uint16_t dlen, void *data)
{
    uint8_t type = HCI_ACLDATA_PKT;
    hci_acl_hdr ha;
    struct iovec iv[3];
    int ivn;

    ha.handle = htobs(acl_handle_pack(handle, acl_flag_pack(pb_flag, bc_flag)));
    ha.dlen = htobs(dlen);

    iv[0].iov_base = &type;
    iv[0].iov_len = 1;
    iv[1].iov_base = &ha;
    iv[1].iov_len = HCI_ACL_HDR_SIZE;

    if (dlen == 0) {
        ivn = 2;
    } else {
        iv[2].iov_base = data;
        iv[2].iov_len = dlen;
        ivn = 3;
    }

    while (writev(dd, iv, ivn) < 0) {
        if (errno == EAGAIN || errno == EINTR) {
            continue;
        }
        return -1;
    }
    return 0;
}

static PyObject *
bt_hci_send_acl(PyObject *self, PyObject *args)
{
    PySocketSockObject *socko = NULL;
    uint16_t handle;
    uint8_t pb_flag, bc_flag;
    int err, dlen = 0;
    char *data = NULL;
    int dd = 0;
    
    if (!PyArg_ParseTuple(args, "OHBB|s#", &socko, &handle, &pb_flag, &bc_flag, &data, &dlen)) {
        return NULL;
    }

    dd = socko->sock_fd;

    Py_BEGIN_ALLOW_THREADS
    err = hci_send_acl(dd, handle, pb_flag, bc_flag, dlen, data);
    Py_END_ALLOW_THREADS

    if( err ) return socko->errorhandler();

    return Py_BuildValue("i", err);
}

PyDoc_STRVAR(bt_hci_send_acl_doc, 
"hci_send_acl(sock, handle, pb_flag, bc_flag, data)\n\
\n\
Transmits the specified HCI command to the socket.\n\
    sock    - the btoscket object to use\n\
    handle  - connection handle\n\
    pb_flag - see bluetooth specification\n\
    bc_flag - see bluetooth specification\n\
    data    - ACL data");

#define DECL_BT_METHOD(name, argtype) \
{ #name, (PyCFunction)bt_ ##name, argtype, bt_ ## name ## _doc }

static PyMethodDef bt_methods[] = {
    DECL_BT_METHOD(hci_send_acl, METH_VARARGS),
};

PyDoc_STRVAR(bluez_ext_doc,
"Extension module for bluetooth operations.");

static PyObject *bluez_ext_error;

PyMODINIT_FUNC
init_bluez_ext(void)
{
    PyObject *m = Py_InitModule3("bluez_ext", bt_methods, bluez_ext_doc);
    if (m == NULL) {
        return;
    }

    bluez_ext_error = PyErr_NewException("bluez_ext.error", NULL, NULL);
    if (bluez_ext_error == NULL) {
        return;
    }
    Py_INCREF(bluez_ext_error);
    PyModule_AddObject(m, "error", bluez_ext_error);
}

