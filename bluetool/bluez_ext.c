#include <Python.h>

typedef struct {
    uint16_t handle;
    uint16_t dlen;
} __attribute__((packed)) hci_acl_hdr;
#define HCI_ACL_HDR_SIZE 4

int hci_send_acl(int dd, uint16_t hdl, uint8_t pb_flag, uint8_t bc_flag, uint16_t dlen, void *data)
{
    uint8_t type = HCI_ACLDATA_PKT;
    hci_acl_hdr ha;
    struct iovec iv[3];
    int ivn;

    ha.handle = htobs(acl_data_hdl_pack(hdl, pb_flag, bc_flag));
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
bt_hci_send_cmd(PyObject *self, PyObject *args)
{
    PySocketSockObject *socko = NULL;
    int err, plen = 0;
    uint16_t ogf, ocf;
    char *param = NULL;
    int dd = 0;
    
    if ( !PyArg_ParseTuple(args, "OHH|s#", &socko, &ogf, &ocf, &param, &plen)) {
        return NULL;
    }

    dd = socko->sock_fd;

    Py_BEGIN_ALLOW_THREADS
    err = hci_send_cmd(dd, ogf, ocf, plen, (void*)param);
    Py_END_ALLOW_THREADS

    if( err ) return socko->errorhandler();

    return Py_BuildValue("i", err);
}

PyDoc_STRVAR(bt_hci_send_cmd_doc, 
"hci_send_command(sock, ogf, ocf, params)\n\
\n\
Transmits the specified HCI command to the socket.\n\
    sock     - the btoscket object to use\n\
    ogf, pcf - see bluetooth specification\n\
    params   - packed command parameters (use the struct module to do this)");

#define DECL_BT_METHOD(name, argtype) \
{ #name, (PyCFunction)bt_ ##name, argtype, bt_ ## name ## _doc }

static PyMethodDef bt_methods[] = {
    DECL_BT_METHOD(hci_send_cmd, METH_VARARGS),
}

static PyObject *bluez_ext_error;

PyMODINIT_FUNC
init_bluez_ext(void)
{
    PyObject *m = Py_InitModule("bluez_ext", bt_methods);
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
