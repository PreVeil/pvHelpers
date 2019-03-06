var myip = myIpAddress();
var BYPASS = "DIRECT";
PUBLIC = "PROXY 199.168.151.10:10975; PROXY 104.129.194.41:10975; DIRECT";

function FindProxyForURL(url, host) {
    // Send everything other than HTTP, WSS and HTTPS direct
    // Uncomment middle line if FTP over HTTP is enabled
    if ((url.substring(0, 5) != "http:") &&
        (url.substring(0, 4) != "wss:") &&
        //                (url.substring(0,4) != "ftp:") &&
        (url.substring(0, 6) != "https:"))
        return BYPASS;

    /* Rest of the traffic */
    return PUBLIC;
}
