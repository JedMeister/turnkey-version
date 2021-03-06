# Copyright (c) 2010 Liraz Siri <liraz@turnkeylinux.org>
#               2020 TurnKey GNU/Linux <admin@turnkeylinux.org>
#
# This file is part of turnkey-version.
#
# turnkey-version is open source software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.

import re
import subprocess
from subprocess import PIPE
import os
from sys import stdin


DEFAULT = 'etc/turnkey_version'


def _parse_turnkey_release(version):
    m = re.match(r'turnkey-.*?-(\d.*?)-[^\d]', version)
    if m:
        return m.group(1)


def get_debian_codename(encoding=stdin.encoding, rootfs=None):
    """Return Debian codename of the system (leverages lsb_release)"""
    comm = ['lsb_release', '-sc']
    if rootfs and rootfs != '/':
        comm = ['chroot', rootfs] + comm
    proc = subprocess.run(comm, stdout=PIPE,
                          encoding=encoding)
    if proc.returncode != 0:
        return
    return proc.stdout.strip()


def get_turnkey_release(rootfs='/'):
    """Return release_version. On error, returns None"""
    turnkey_version = get_turnkey_version(rootfs=rootfs)
    if turnkey_version:
        return _parse_turnkey_release(turnkey_version)


# used by turnkey-version
def get_turnkey_version(rootfs='/', fpath=DEFAULT):
    """Return turnkey_version. On error, returns None.
    Warning: if fpath is an absoulte path, rootfs will be ignored.
    """
    try:
        with open(os.path.join(rootfs, fpath), 'r') as fob:
            return fob.read().strip()
    except IOError:
        pass


class AppVer:
    def __init__(self, turnkey_version=None, rootfs=None):
        if not turnkey_version:
            turnkey_version = get_turnkey_version(rootfs=rootfs)
        tkl_ver_list = turnkey_version.split('-')
        if tkl_ver_list[0] == 'turnkey':
            tkl_ver_list.pop(0)
        *appname, self.tklver, self.codename, self.arch = tkl_ver_list
        self.deb_codename = get_debian_codename(rootfs=rootfs)
        self.appname = '-'.join(appname)

    def app_ver(self):
        return (self.appname, self.tklver, self.codename, self.arch)

    def app_json(self, deb_ver=False):
        _json = {'name': self.appname, 'tklver': self.tklver,
                 'codename': self.codename, 'arch': self.arch}
        if deb_ver:
            _json['debian_codename'] = self.deb_codename
        return _json

# used by turnkey-sysinfo
def fmt_base_distribution(encoding=stdin.encoding):
    """Return a formatted distribution string:
        e.g., Debian 10/Buster"""

    proc = subprocess.run(["lsb_release", "-ircd"], stdout=PIPE,
                          encoding=encoding)
    if proc.returncode != 0:
        return

    d = dict([line.split(':\t')
              for line in proc.stdout.splitlines()])

    basedist = "{} {}/{}".format(d['Distributor ID'],
                                 d['Release'],
                                 d['Codename'].capitalize())
    return basedist


def fmt_sysversion(encoding=stdin.encoding):
    version_parts = []
    release = get_turnkey_release()
    if release:
        version_parts.append("TurnKey GNU/Linux {}".format(release))

    basedist = fmt_base_distribution(encoding)
    if basedist:
        version_parts.append(basedist)

    if len(version_parts) == 2:
        version = '{} ({})'.format(version_parts[0], version_parts[1])
    elif len(version_parts) == 1:
        version = version_parts[0]
    else:
        version = "Unknown"
    return version
