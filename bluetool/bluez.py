"""BlueZ adaptation module.

Add missing command/event definitions in pybluez.

Reference:
http://git.kernel.org/cgit/bluetooth/bluez.git/plain/lib/hci.h
https://pybluez.googlecode.com/svn/trunk/bluez/btmodule.c
"""
from bluetooth._bluetooth import *

#OGF_LINK_CTL = 0x01
#OCF_INQUIRY = 0x0001
#OCF_INQUIRY_CANCEL = 0x0002
#OCF_PERIODIC_INQUIRY = 0x0003
#OCF_EXIT_PERIODIC_INQUIRY = 0x0004
#OCF_CREATE_CONN = 0x0005
#OCF_DISCONNECT = 0x0006
#OCF_ADD_SCO = 0x0007
OCF_CREATE_CONN_CANCEL = 0x0008
#OCF_ACCEPT_CONN_REQ = 0x0009
#OCF_REJECT_CONN_REQ = 0x000A
#OCF_LINK_KEY_REPLY = 0x000B
#OCF_LINK_KEY_NEG_REPLY = 0x000C
#OCF_PIN_CODE_REPLY = 0x000D
#OCF_PIN_CODE_NEG_REPLY = 0x000E
#OCF_SET_CONN_PTYPE = 0x000F
#OCF_AUTH_REQUESTED = 0x0011
#OCF_SET_CONN_ENCRYPT = 0x0013
OCF_CHANGE_CONN_LINK_KEY = 0x0015
OCF_MASTER_LINK_KEY = 0x0017
#OCF_REMOTE_NAME_REQ = 0x0019
OCF_REMOTE_NAME_REQ_CANCEL = 0x001A
#OCF_READ_REMOTE_FEATURES = 0x001B
OCF_READ_REMOTE_EXT_FEATURES = 0x001C
#OCF_READ_REMOTE_VERSION = 0x001D
#OCF_READ_CLOCK_OFFSET = 0x001F
OCF_READ_LMP_HANDLE = 0x0020
OCF_SETUP_SYNC_CONN = 0x0028
OCF_ACCEPT_SYNC_CONN_REQ = 0x0029
OCF_REJECT_SYNC_CONN_REQ = 0x002A
OCF_IO_CAPABILITY_REPLY = 0x002B
OCF_USER_CONFIRM_REPLY = 0x002C
OCF_USER_CONFIRM_NEG_REPLY = 0x002D
OCF_USER_PASSKEY_REPLY = 0x002E
OCF_USER_PASSKEY_NEG_REPLY = 0x002F
OCF_REMOTE_OOB_DATA_REPLY = 0x0030
OCF_REMOTE_OOB_DATA_NEG_REPLY = 0x0033
OCF_IO_CAPABILITY_NEG_REPLY = 0x0034
OCF_CREATE_PHYSICAL_LINK = 0x0035
OCF_ACCEPT_PHYSICAL_LINK = 0x0036
OCF_DISCONNECT_PHYSICAL_LINK = 0x0037
OCF_CREATE_LOGICAL_LINK = 0x0038
OCF_ACCEPT_LOGICAL_LINK = 0x0039
OCF_DISCONNECT_LOGICAL_LINK = 0x003A
OCF_LOGICAL_LINK_CANCEL = 0x003B
OCF_FLOW_SPEC_MODIFY = 0x003C

#OGF_LINK_POLICY = 0x02
#OCF_HOLD_MODE = 0x0001
#OCF_SNIFF_MODE = 0x0003
#OCF_EXIT_SNIFF_MODE = 0x0004
#OCF_PARK_MODE = 0x0005
#OCF_EXIT_PARK_MODE = 0x0006
#OCF_QOS_SETUP = 0x0007
#OCF_ROLE_DISCOVERY = 0x0009
#OCF_SWITCH_ROLE = 0x000B
#OCF_READ_LINK_POLICY = 0x000C
#OCF_WRITE_LINK_POLICY = 0x000D
OCF_READ_DEFAULT_LINK_POLICY = 0x000E
OCF_WRITE_DEFAULT_LINK_POLICY = 0x000F
OCF_FLOW_SPECIFICATION = 0x0010
OCF_SNIFF_SUBRATING = 0x0011

#OGF_HOST_CTL = 0x03
OCF_SET_EVENT_MASK = 0x0001
#OCF_RESET = 0x0003
#OCF_SET_EVENT_FLT = 0x0005
OCF_FLUSH = 0x0008
OCF_READ_PIN_TYPE = 0x0009
OCF_WRITE_PIN_TYPE = 0x000A
OCF_CREATE_NEW_UNIT_KEY = 0x000B
OCF_READ_STORED_LINK_KEY = 0x000D
OCF_WRITE_STORED_LINK_KEY = 0x0011
OCF_DELETE_STORED_LINK_KEY = 0x0012
#OCF_CHANGE_LOCAL_NAME = 0x0013
#OCF_READ_LOCAL_NAME = 0x0014
OCF_READ_CONN_ACCEPT_TIMEOUT = 0x0015
OCF_WRITE_CONN_ACCEPT_TIMEOUT = 0x0016
#OCF_READ_PAGE_TIMEOUT = 0x0017
#OCF_WRITE_PAGE_TIMEOUT = 0x0018
OCF_READ_SCAN_ENABLE = 0x0019
#OCF_WRITE_SCAN_ENABLE = 0x001A
#OCF_READ_PAGE_ACTIVITY = 0x001B
#OCF_WRITE_PAGE_ACTIVITY = 0x001C
#OCF_READ_INQ_ACTIVITY = 0x001D
#OCF_WRITE_INQ_ACTIVITY = 0x001E
#OCF_READ_AUTH_ENABLE = 0x001F
#OCF_WRITE_AUTH_ENABLE = 0x0020
#OCF_READ_ENCRYPT_MODE = 0x0021
#OCF_WRITE_ENCRYPT_MODE = 0x0022
#OCF_READ_CLASS_OF_DEV = 0x0023
#OCF_WRITE_CLASS_OF_DEV = 0x0024
#OCF_READ_VOICE_SETTING = 0x0025
#OCF_WRITE_VOICE_SETTING = 0x0026
OCF_READ_AUTOMATIC_FLUSH_TIMEOUT = 0x0027
OCF_WRITE_AUTOMATIC_FLUSH_TIMEOUT = 0x0028
OCF_READ_NUM_BROADCAST_RETRANS = 0x0029
OCF_WRITE_NUM_BROADCAST_RETRANS = 0x002A
OCF_READ_HOLD_MODE_ACTIVITY = 0x002B
OCF_WRITE_HOLD_MODE_ACTIVITY = 0x002C
#OCF_READ_TRANSMIT_POWER_LEVEL = 0x002D
OCF_READ_SYNC_FLOW_ENABLE = 0x002E
OCF_WRITE_SYNC_FLOW_ENABLE = 0x002F
OCF_SET_CONTROLLER_TO_HOST_FC = 0x0031
#OCF_HOST_BUFFER_SIZE = 0x0033
OCF_HOST_NUM_COMP_PKTS = 0x0035
#OCF_READ_LINK_SUPERVISION_TIMEOUT = 0x0036
#OCF_WRITE_LINK_SUPERVISION_TIMEOUT = 0x0037
OCF_READ_NUM_SUPPORTED_IAC = 0x0038
#OCF_READ_CURRENT_IAC_LAP = 0x0039
#OCF_WRITE_CURRENT_IAC_LAP = 0x003A
OCF_READ_PAGE_SCAN_PERIOD_MODE = 0x003B
OCF_WRITE_PAGE_SCAN_PERIOD_MODE = 0x003C
OCF_READ_PAGE_SCAN_MODE = 0x003D
OCF_WRITE_PAGE_SCAN_MODE = 0x003E
OCF_SET_AFH_CLASSIFICATION = 0x003F
OCF_READ_INQUIRY_SCAN_TYPE = 0x0042
OCF_WRITE_INQUIRY_SCAN_TYPE = 0x0043
#OCF_READ_INQUIRY_MODE = 0x0044
#OCF_WRITE_INQUIRY_MODE = 0x0045
OCF_READ_PAGE_SCAN_TYPE = 0x0046
OCF_WRITE_PAGE_SCAN_TYPE = 0x0047
#OCF_READ_AFH_MODE = 0x0048
#OCF_WRITE_AFH_MODE = 0x0049
OCF_READ_EXT_INQUIRY_RESPONSE = 0x0051
OCF_WRITE_EXT_INQUIRY_RESPONSE = 0x0052
OCF_REFRESH_ENCRYPTION_KEY = 0x0053
OCF_READ_SIMPLE_PAIRING_MODE = 0x0055
OCF_WRITE_SIMPLE_PAIRING_MODE = 0x0056
OCF_READ_LOCAL_OOB_DATA = 0x0057
OCF_READ_INQ_RESPONSE_TX_POWER_LEVEL = 0x0058
OCF_READ_INQUIRY_TRANSMIT_POWER_LEVEL = 0x0058
OCF_WRITE_INQUIRY_TRANSMIT_POWER_LEVEL = 0x0059
OCF_READ_DEFAULT_ERROR_DATA_REPORTING = 0x005A
OCF_WRITE_DEFAULT_ERROR_DATA_REPORTING = 0x005B
OCF_ENHANCED_FLUSH = 0x005F
OCF_SEND_KEYPRESS_NOTIFY = 0x0060
OCF_READ_LOGICAL_LINK_ACCEPT_TIMEOUT = 0x0061
OCF_WRITE_LOGICAL_LINK_ACCEPT_TIMEOUT = 0x0062
OCF_SET_EVENT_MASK_PAGE_2 = 0x0063
OCF_READ_LOCATION_DATA = 0x0064
OCF_WRITE_LOCATION_DATA = 0x0065
OCF_READ_FLOW_CONTROL_MODE = 0x0066
OCF_WRITE_FLOW_CONTROL_MODE = 0x0067
OCF_READ_ENHANCED_TRANSMIT_POWER_LEVEL = 0x0068
OCF_READ_BEST_EFFORT_FLUSH_TIMEOUT = 0x0069
OCF_WRITE_BEST_EFFORT_FLUSH_TIMEOUT = 0x006A
OCF_READ_LE_HOST_SUPPORTED = 0x006C
OCF_WRITE_LE_HOST_SUPPORTED = 0x006D

#OGF_INFO_PARAM = 0x04
#OCF_READ_LOCAL_VERSION = 0x0001
OCF_READ_LOCAL_COMMANDS = 0x0002
#OCF_READ_LOCAL_FEATURES = 0x0003
OCF_READ_LOCAL_EXT_FEATURES = 0x0004
#OCF_READ_BUFFER_SIZE = 0x0005
OCF_READ_COUNTRY_CODE = 0x0007
#OCF_READ_BD_ADDR = 0x0009
OCF_READ_DATA_BLOCK_SIZE = 0x000A

#OGF_STATUS_PARAM = 0x05
#OCF_READ_FAILED_CONTACT_COUNTER = 0x0001
#OCF_RESET_FAILED_CONTACT_COUNTER = 0x0002
OCF_READ_LINK_QUALITY = 0x0003
#OCF_READ_RSSI = 0x0005
#OCF_READ_AFH_MAP = 0x0006
OCF_READ_CLOCK = 0x0007
OCF_READ_LOCAL_AMP_INFO = 0x0009
OCF_READ_LOCAL_AMP_ASSOC = 0x000A
OCF_WRITE_REMOTE_AMP_ASSOC = 0x000B

#OGF_TESTING_CMD = 0x3e
OCF_READ_LOOPBACK_MODE = 0x0001
OCF_WRITE_LOOPBACK_MODE = 0x0002
OCF_ENABLE_DEVICE_UNDER_TEST_MODE = 0x0003
OCF_WRITE_SIMPLE_PAIRING_DEBUG_MODE = 0x0004

OGF_LE_CTL = 0x08
OCF_LE_SET_EVENT_MASK = 0x0001
OCF_LE_READ_BUFFER_SIZE = 0x0002
OCF_LE_READ_LOCAL_SUPPORTED_FEATURES = 0x0003
OCF_LE_SET_RANDOM_ADDRESS = 0x0005
OCF_LE_SET_ADVERTISING_PARAMETERS = 0x0006
OCF_LE_READ_ADVERTISING_CHANNEL_TX_POWER = 0x0007
OCF_LE_SET_ADVERTISING_DATA = 0x0008
OCF_LE_SET_SCAN_RESPONSE_DATA = 0x0009
OCF_LE_SET_ADVERTISE_ENABLE = 0x000A
OCF_LE_SET_SCAN_PARAMETERS = 0x000B
OCF_LE_SET_SCAN_ENABLE = 0x000C
OCF_LE_CREATE_CONN = 0x000D
OCF_LE_CREATE_CONN_CANCEL = 0x000E
OCF_LE_READ_WHITE_LIST_SIZE = 0x000F
OCF_LE_CLEAR_WHITE_LIST = 0x0010
OCF_LE_ADD_DEVICE_TO_WHITE_LIST = 0x0011
OCF_LE_REMOVE_DEVICE_FROM_WHITE_LIST = 0x0012
OCF_LE_CONN_UPDATE = 0x0013
OCF_LE_SET_HOST_CHANNEL_CLASSIFICATION = 0x0014
OCF_LE_READ_CHANNEL_MAP = 0x0015
OCF_LE_READ_REMOTE_USED_FEATURES = 0x0016
OCF_LE_ENCRYPT = 0x0017
OCF_LE_RAND = 0x0018
OCF_LE_START_ENCRYPTION = 0x0019
OCF_LE_LTK_REPLY = 0x001A
OCF_LE_LTK_NEG_REPLY = 0x001B
OCF_LE_READ_SUPPORTED_STATES = 0x001C
OCF_LE_RECEIVER_TEST = 0x001D
OCF_LE_TRANSMITTER_TEST = 0x001E
OCF_LE_TEST_END = 0x001F
OCF_LE_SET_DATA_LEN = 0x0022
OCF_LE_READ_DEFAULT_DATA_LEN = 0x0023
OCF_LE_WRITE_DEFAULT_DATA_LEN = 0x0024

#OGF_VENDOR_CMD = 0x3f


#EVT_INQUIRY_COMPLETE = 0x01
#EVT_INQUIRY_RESULT = 0x02
#EVT_CONN_COMPLETE = 0x03
#EVT_CONN_REQUEST = 0x04
#EVT_DISCONN_COMPLETE = 0x05
#EVT_AUTH_COMPLETE = 0x06
#EVT_REMOTE_NAME_REQ_COMPLETE = 0x07
#EVT_ENCRYPT_CHANGE = 0x08
EVT_CHANGE_CONN_LINK_KEY_COMPLETE = 0x09
EVT_MASTER_LINK_KEY_COMPLETE = 0x0A
#EVT_READ_REMOTE_FEATURES_COMPLETE = 0x0B
#EVT_READ_REMOTE_VERSION_COMPLETE = 0x0C
#EVT_QOS_SETUP_COMPLETE = 0x0D
#EVT_CMD_COMPLETE = 0x0E
#EVT_CMD_STATUS = 0x0F
EVT_HARDWARE_ERROR = 0x10
EVT_FLUSH_OCCURRED = 0x11
#EVT_ROLE_CHANGE = 0x12
#EVT_NUM_COMP_PKTS = 0x13
#EVT_MODE_CHANGE = 0x14
EVT_RETURN_LINK_KEYS = 0x15
#EVT_PIN_CODE_REQ = 0x16
#EVT_LINK_KEY_REQ = 0x17
#EVT_LINK_KEY_NOTIFY = 0x18
EVT_LOOPBACK_COMMAND = 0x19
EVT_DATA_BUFFER_OVERFLOW = 0x1A
EVT_MAX_SLOTS_CHANGE = 0x1B
#EVT_READ_CLOCK_OFFSET_COMPLETE = 0x1C
#EVT_CONN_PTYPE_CHANGED = 0x1D
#EVT_QOS_VIOLATION = 0x1E
EVT_PSCAN_REP_MODE_CHANGE = 0x20
EVT_FLOW_SPEC_COMPLETE = 0x21
#EVT_INQUIRY_RESULT_WITH_RSSI = 0x22
EVT_READ_REMOTE_EXT_FEATURES_COMPLETE = 0x23
EVT_SYNC_CONN_COMPLETE = 0x2C
EVT_SYNC_CONN_CHANGED = 0x2D
EVT_SNIFF_SUBRATING = 0x2E
#EVT_EXTENDED_INQUIRY_RESULT = 0x2F
EVT_ENCRYPTION_KEY_REFRESH_COMPLETE = 0x30
EVT_IO_CAPABILITY_REQUEST = 0x31
EVT_IO_CAPABILITY_RESPONSE = 0x32
EVT_USER_CONFIRM_REQUEST = 0x33
EVT_USER_PASSKEY_REQUEST = 0x34
EVT_REMOTE_OOB_DATA_REQUEST = 0x35
EVT_SIMPLE_PAIRING_COMPLETE = 0x36
EVT_LINK_SUPERVISION_TIMEOUT_CHANGED = 0x38
EVT_ENHANCED_FLUSH_COMPLETE = 0x39
EVT_USER_PASSKEY_NOTIFY = 0x3B
EVT_KEYPRESS_NOTIFY = 0x3C
EVT_REMOTE_HOST_FEATURES_NOTIFY = 0x3D
EVT_LE_META_EVENT = 0x3E
EVT_LE_CONN_COMPLETE = 0x01
EVT_LE_ADVERTISING_REPORT = 0x02
EVT_LE_CONN_UPDATE_COMPLETE = 0x03
EVT_LE_READ_REMOTE_USED_FEATURES_COMPLETE = 0x04
EVT_LE_LTK_REQUEST = 0x05
EVT_LE_DATA_LEN_CHANGE = 0x07
EVT_LE_ENHANCED_CONN_COMPLETE = 0x0A
EVT_PHYSICAL_LINK_COMPLETE = 0x40
EVT_CHANNEL_SELECTED = 0x41
EVT_DISCONNECT_PHYSICAL_LINK_COMPLETE = 0x42
EVT_PHYSICAL_LINK_LOSS_EARLY_WARNING = 0x43
EVT_PHYSICAL_LINK_RECOVERY = 0x44
EVT_LOGICAL_LINK_COMPLETE = 0x45
EVT_DISCONNECT_LOGICAL_LINK_COMPLETE = 0x46
EVT_FLOW_SPEC_MODIFY_COMPLETE = 0x47
EVT_NUMBER_COMPLETED_BLOCKS = 0x48
EVT_AMP_STATUS_CHANGE = 0x4D
#EVT_VENDOR = 0xFF

