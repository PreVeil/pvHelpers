import collections
import re
import socket
import struct
import subprocess
import sys

from pvHelpers.user import LUserInfo, LUserInfoWin
from pvHelpers.utils import NotAssigned, g_log, params, to_int

if sys.platform == "win32":
    from .win_helpers import *


LSOF_CACHE = collections.deque(maxlen=3)


@params({unicode, str}, int, {unicode, str}, int)
def resolve_connection_info(remote_addr, remote_port, local_process_addr, local_process_port):
    if remote_addr != u"127.0.0.1":
        g_log.error(u"resolve_connection_info: only 127.0.0.1 connections allowed, address: {}:{}".format(remote_addr, remote_port))
        return False, None

    if sys.platform in ["linux2", "darwin"]:
        return _get_conn_process_info_unix(remote_addr, remote_port, local_process_addr, local_process_port)
    elif sys.platform in ["win32"]:
        return _get_conn_process_info_windows(remote_addr, remote_port, local_process_addr, local_process_port)

    raise NotImplementedError(u"platform not supported")

def _get_conn_process_info_unix(remote_addr, remote_port, local_process_addr, local_process_port):
    ################
    # Listing all open tcp files of the Local Server (Crypto, IMAP, SMTP) with ESTABLISHED TCP status
    #
    # -l => avoid the conversion of uids to login names
    # -n => avoid the convesion of host address to hostnames
    # -P => avoid the conversion of port numbers to port names
    # -M => avoid the portmapper if enabled by default
    # -i => constrain for only internet files open for the address and protocol
    # -s => constrain for the state of the TCP connection.
    # -F => prepare output for application use (not print format), `un` are field descriptors for uid and Internet address
    # Internet address has this pattern : `n$LOCAL_ADDR:$LOCAL_PORT->$REMOTE_ADDR:$REMOTE_PORT`
    # The output will always include `pu` field descriptors (pid and file descriptor number)
    # thus, `-Fun` means the output will have five fields for each open file ; fields in the below order:
    # [(pid, uid, (file descriptor, Internet address)*)*]
    ################
    lsof_command = "lsof -l -n -P -M -iTCP@{}:{} -sTCP:ESTABLISHED -Fufn".format(local_process_addr, local_process_port)
    try:
        result = subprocess.check_output(lsof_command.split(" "), close_fds=True)
        open_files = _materialize_lsof(result)
    except (subprocess.CalledProcessError, AttributeError, IndexError) as e:
        g_log.exception(u"lsof exception {}".format(e))
        return False, None

    LSOF_CACHE.appendleft(open_files)
    remote_client_files = filter(lambda f: f["local_addr"] == remote_addr and f["local_port"] == remote_port, open_files)

    if len(remote_client_files) == 0:
        g_log.error(u"_get_conn_process_info_unix: couldn't fetch the connection file info")
        return False, None

    # if len(remote_client_files) > 1 (the process has multiple connections open to Crypto Server),
    # they'll be identical in all attributes except for their file descriptor numbers
    status, uid = to_int(remote_client_files[0]["uid"])
    if not status:
        g_log.error(u"_get_conn_process_info_unix: int coercion of uid failed")
        return False, None

    return True, {
        "pid": remote_client_files[0]["pid"],
        "uid": LUserInfo.new(sys.platform, uid)
    }

# https://msdn.microsoft.com/en-us/library/windows/desktop/bb408406(v=vs.85).aspx
def _get_conn_process_info_windows(remote_addr, remote_port, local_process_addr, local_process_port):
    row_num = 1
    # Make an initial call to GetTcpTable2 to
    # get the necessary size into the ulSize variable
    counter = 0
    while(True):
        counter += 1
        tcpTable = MIB_TCPTABLE2(row_num)
        ulSize = INT(SIZEOF(tcpTable))
        status = ctypes.windll.iphlpapi.GetTcpTable2(REF(tcpTable), REF(ulSize), False)
        if status == WIN_ERROR.ERROR_INSUFFICIENT_BUFFER:
            required_buffer_size = ulSize.value
            row_num = int((required_buffer_size - SIZEOF(DWORD)) / SIZEOF(MIB_TCPROW2())) + 2 # just adding space for 2 extra rows
        elif status != WIN_ERROR.NO_ERROR:
            g_log.error(u"_get_conn_process_info_windows: unexpected error code: {}".format(status))
            return False, None
        else:
            break

        if counter == 5:
            g_log.error(u"_get_conn_process_info_windows: failed to get tcp table data, status: {}".format(status))
            return False, None

    tcp_connections = set()
    for i in range(0, tcpTable.dwNumEntries):
        _row = tcpTable.table[i]
        if _row.dwState == TCP_STATE.MIB_TCP_STATE_ESTAB:

            lPort = socket.ntohs(_row.dwLocalPort)
            lAddr = socket.inet_ntoa(struct.pack("L", _row.dwLocalAddr))
            rPort = socket.ntohs(_row.dwRemotePort)
            rAddr = socket.inet_ntoa(struct.pack("L", _row.dwRemoteAddr))
            pid = _row.dwOwningPid
            tcp_connections.add((pid, lAddr, lPort, rAddr, rPort))

    remote_connections = filter(lambda c: c[1] == remote_addr and c[2] == remote_port and c[3] == local_process_addr and c[4] == local_process_port, tcp_connections)

    if len(remote_connections) != 1:
        g_log.error(u"_get_conn_process_info_windows: couldn't fetch the connection file info, pcount: {}, p: {}".format(len(tcp_connections), tcp_connections))
        return False, None

    pid = remote_connections[0][0]
    try:
        p_handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, 0, pid)
        p_token = ws.OpenProcessToken(p_handle, ws.TOKEN_ALL_ACCESS)
        _sid = ws.GetTokenInformation(p_token, ws.TokenUser)[0]
        _psids = [psid[0] for psid in ws.GetTokenInformation(p_token, ws.TokenGroups)]
    except (pywintypes.error, Exception) as e:
        g_log.exception(u"failed to get process handle, pid: {}, exception: {}".format(remote_connections[0], e))
        return False, None
    finally:
        win32api.CloseHandle(p_handle)

    return True, {"pid": pid, "uid":  LUserInfoWin(_sid, _psids)}


# This function assumes the executed losf command is : `lsof -l -n -P -M -iTCP@REMOTE_ADDR:REMOTE_PORT -sTCP:ESTABLISHED -Fun`
# Throws IndexError/AttributeError if the command returns are not as expected
# TODO: improve this expensive lookup
def _materialize_lsof(output):
    f_array = output.split("\n")

    open_files, i = [], 0
    while i < len(f_array):
        # Start of a process set
        if f_array[i].startswith("p"):
            # all field values are prefixed with its field descriptor letter (`p123` for pid=123)
            pid = f_array[i][1:]; i += 1
            uid = f_array[i][1:]; i += 1

            while i < len(f_array) and f_array[i].startswith("f"):
                fd = f_array[i][1:]; i += 1
                internet_address = f_array[i][1:]; i += 1
                match = re.match("^([0-9.]+):([0-9]+)->([0-9.]+):([0-9]+)$", internet_address)
                if match is None:
                    g_log.error("_materialize_lsof: internet_address doesn't match pattern: {}".format(internet_address))
                    break

                la, lp, ra, rp = match.group(1,2,3,4)
                status, _lp = to_int(lp)
                if not status:
                    g_log.error("_materialize_lsof: lp port coercion failed: {}".format(lp))
                    continue
                status, _rp = to_int(rp)
                if not status:
                    g_log.error("_materialize_lsof: rp port coercion failed: {}".format(rp))
                    continue
                open_files.append({
                    "pid": pid,
                    "uid": uid,
                    "fd": fd,
                    "local_addr": la,
                    "local_port": _lp,
                    "remote_addr": ra,
                    "remote_port": _rp
                })

        else:
            i += 1

    return open_files
