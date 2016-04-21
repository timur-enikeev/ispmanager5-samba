#!/usr/bin/python
# -*- coding: utf-8 -*-
#Configuration
ENABLE_FTP=True  # Enable creating samba users for ftp accounts (only for ProFTPd). Disalbe this option if you use another FTP server!

import logging, os, subprocess, sys, pwd, traceback, time
logging.basicConfig(level=logging.ERROR) # , filename='/samba_addon.log')

env = os.environ

def create_or_edit():
    """Create or change password of samba user"""
    smbpasswd_cmdlist = ['smbpasswd'] + [env['PARAM_name']] + ['-s'] # smbpasswd command with parameters
    if subprocess.call('pdbedit -u {}'.format(env['PARAM_name']).split(), stdout=sys.stderr): # check if user exists in SMB database
        smbpasswd_cmdlist.append('-a') # if user doesn't exist say smbpasswd to create this user
    smbpasswd = subprocess.Popen(smbpasswd_cmdlist, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) # Launching smbpasswd
    smbpasswd.stdin.write(env['PARAM_passwd'] + '\n') # Entering password and confirmation
    smbpasswd.stdin.write(env['PARAM_passwd'] + '\n')
    logging.info(smbpasswd.communicate())
    if smbpasswd.returncode == 0:
        enable_user(env['PARAM_name'])

def enable_user(user):
    """Enable SMB user"""
    subprocess.call('smbpasswd -e {}'.format(user).split(), stdout=sys.stderr)

def disable_user(user):
    """Disable SMB user"""
    subprocess.call('smbpasswd -d {}'.format(user).split(), stdout=sys.stderr)

def suspend():
    """Disable SMB accounts for suspended users"""
    users = env['PARAM_elids'].split(', ')
    for user in users:
        disable_user(user)
            

def resume():
    """Enable SMB accounts for enabled users"""
    users = env['PARAM_elids'].split(', ')
    for user in users:
        enable_user(user)
    
def delete():
    """Delete samba users"""
    logging.info('env: ' + str(env))
    users = env['PARAM_elids'].split(', ')
    for user in users:
        subprocess.call('smbpasswd -x {}'.format(user).split(), stdout=sys.stderr)
        if env['PARAM_func'] == 'ftp.user.delete':
            del_system_user(user)

def get_ftp_users():
    fp = open('/etc/proftpd/proftpd.passwd')
    fpl = fp.readlines()
    ftp_accounts = []
    for l in fpl:
        ftp_acc = {}
        l_splitted = l.split(':')
        if len(l_splitted) >= 7:
            ftp_acc['name'] = l_splitted[0]
            ftp_acc['uid'] = l_splitted[2]
            ftp_acc['gid'] = l_splitted[3]
            ftp_acc['homedir'] = l_splitted[5]
            ftp_accounts.append(ftp_acc)
    return ftp_accounts

def get_owner_of_ftp(ftpuser):
#Get username, UID and GID of owner of the FTP account. Returns first user in passwd file which is not in proftpd.passwd file
    try:
        ftp_users = get_ftp_users()
        ftp_account = None
        ftp_list = []
        for ftp_user in ftp_users:
            if ftp_user['name'] == ftpuser:
                ftp_account = ftp_user
                break
        else:
            return 1
        ftp_list = [ftp_user['name'] for ftp_user in ftp_users if ftp_user['uid'] == ftp_account['uid']]
        system_list = [u.pw_name for u in pwd.getpwall() if u.pw_uid == int(ftp_account['uid'])]
        for i, u in enumerate(system_list):
            if u in ftp_list:
                del system_list[i]
        return system_list[0]
    except:
        return None


def user_for_ftp():
#Create system user for ftp account. Return error if user with this name but different parameters (UID, home dir) already exists. Returns 0 if success, returns 1 if user wasn't created but FTP user can be created, returns 2 if FTP user can't be created, returns 3 if user with same name exists
    try:
        logging.info(str(env))
        ftpuser = env['PARAM_name']
        if 'PARAM_elid' in env:
            return 0
        if 'PARAM_owner' in env and env['PARAM_owner']: #If function was called by root and has "owner" parameter
            owner = env['PARAM_owner']
        elif int(env['AUTH_LEVEL']) < 30:
            owner = env['AUTH_USER']
        else:
            owner = get_owner_of_ftp(ftpuser)
            if not owner:
                return 1
        if owner == ftpuser:
            return 3
        owner_pwd = pwd.getpwnam(owner)
        uid = owner_pwd.pw_uid
        gid = owner_pwd.pw_gid
        homedir = os.path.normpath(owner_pwd.pw_dir + '/' + env['PARAM_home'])
        try:
            ftpuser_pwd = pwd.getpwnam(ftpuser)
        except:
            subprocess.call('useradd {} -u {} -g {} -o --shell /bin/false --home-dir={}'.format(ftpuser, uid, gid, homedir).split(), stdout=sys.stderr)
        else:
            if ftpuser_pwd.pw_uid != uid or ftpuser_pwd.pw_gid != gid:
                return 3
            elif os.path.normpath(ftpuser_pwd.pw_dir) != homedir:
                subprocess.call('usermod --home {} {}'.format(homedir, ftpuser).split(), stdout=sys.stderr)
    except:
        logging.error(traceback.format_exc())
        return 2
    return 0

def del_system_user(ftpuser):
    owner = get_owner_of_ftp(ftpuser)
    if owner and pwd.getpwnam(owner).pw_uid == pwd.getpwnam(ftpuser).pw_uid:
        subprocess.call('userdel -f {}'.format(ftpuser).split())

def success():
    print """<?xml version="1.0" encoding="UTF-8"?>
<doc/>"""

def user_exists():
    print """<?xml version="1.0" encoding="UTF-8"?>
    <doc>
      <error type="exists" object="user" lang="ru">
        <msg>Пользователь уже существует. User already exists.</msg>
      </error>
    </doc>"""

def other_error():
    print """<?xml version="1.0" encoding="UTF-8"?>
    <doc>
      <error />
    </doc>"""


try:
    if env['PARAM_func'] == 'user.delete' or (env['PARAM_func'] == 'ftp.user.delete' and ENABLE_FTP):
        delete()
        success()
    elif env['PARAM_func'] == 'user.suspend' or (env['PARAM_func'] == 'ftp.user.suspend' and ENABLE_FTP):
        suspend()
        success()
    elif env['PARAM_func'] == 'user.resume' or (env['PARAM_func'] == 'ftp.user.resume' and ENABLE_FTP):
        logging.info(str(env))
        resume()
        success()
    elif not 'PARAM_sok' in env or not env['PARAM_sok']:
        success()
    elif env['PARAM_func'] in ('user.add.finish', 'user.edit') and env['PARAM_passwd'] and env['PARAM_passwd'] == env['PARAM_confirm']:
        create_or_edit()
        success()
    elif ENABLE_FTP and env['PARAM_func'] == 'ftp.user.edit' and 'PARAM_sok' in env and env['PARAM_passwd'] and env['PARAM_passwd'] == env['PARAM_confirm']:
        r = user_for_ftp()
        if r == 0:
            create_or_edit()
            success()
        elif r == 1:
            success()
        elif r == 3:
            user_exists()
        else:
            other_error()
    else:
        success()          


except:
    logging.error(traceback.format_exc())
    success()


logging.shutdown()
