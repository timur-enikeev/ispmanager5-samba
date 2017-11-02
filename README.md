# ispmanager5-samba
Plugin for creating Samba accounts for ISPManager 5 users

Tested on Debian Jessie and ISPManager Lite
## License
GNU LGPL 2.1 or later.

## Installation

1. Install Samba
2. Copy samba.py to /usr/local/mgr5/addon/
3. Make this file executable: chmod +x /usr/local/mgr5/addon/samba.py
4. Copy ispmgr_mod_samba.xml to /usr/local/mgr5/etc/xml
5. Restart ISPManager: /usr/local/mgr5/sbin/mgrctl -m ispmgr exit

## Configuration

ENABLE_FTP={True, False} — enable/disable creating samba accounts for FTP users. Works only if you use ProFTPd as FTP server. Disable it if you use another FTP server.
