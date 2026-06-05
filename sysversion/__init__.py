# Copyright (c) 2010 Liraz Siri <liraz@turnkeylinux.org>
# Copyright (c) 2020-2026 TurnKey GNU/Linux <admin@turnkeylinux.org>
#
# This file is part of turnkey-version.
#
# turnkey-version is open source software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.

import os
import re
import subprocess
import warnings
from os.path import join


class TurnkeyVersionError(Exception):
    pass


class TurnkeyVersionDeprecationWarning(DeprecationWarning):
    pass


def _read_file(
        rootfs: str | None = None,
        file_path: str = None,
) -> str:
    """Read TurnKey Linux appliance release version file.

    Notes:
        `rootfs` & `file_path` conflict - only one (or none) should be passed.
        `rootfs` is deprecated and slated for removal in TurnKey v20.0.

    Args:
        rootfs (str):
            Path to chroot; 'etc/turnkey-version' will be appended - i.e.
            rootfs="path/to/chroot" results in
            'file_path == path/to/chroot/etc/turnkey-version'.
        file_path (str):
            Path to text file to read (default '/etc/turnkey_version').

    Returns:
        str:
            Contents of text file as single string.

    Raises:
        TurnkeyVersionError:
            - If both `rootfs` and `file_path` are given.
            - `file_path` does not exist; is not a file or the user does not
              have read permission.
            - `file_path` is not UTF8 encoded plain text file containing
              expected text - should only contain TurnKey Linux version string.

    """
    if not rootfs and not file_path:
        raise TurnkeyVersionError("one of rootfs or file path are required")
    if rootfs and file_path:
        raise TurnkeyVersionError("only one of rootfs/file path allowed")
    elif rootfs:
        file_path = join(rootfs, "etc/turnkey_version")
    else:
        file_path = file_path if file_path else "/etc/turnkey_version"
    try:
        with open(file) as fob:
            return fob.read().strip()
    except (
        FileNotFoundError,
        PermissionError,
        IsADirectoryError,
        OSError,
        UnicodeDecodeError,
    ) as e:
        raise TurnkeyVersionError from e


def _run_debian_cmd(command: list[str], chrootfs: str | None = None) -> str:
    """Run Debian command via subprocess on system or in chroot.

    If `chrootfs` given, `command` will be in the chroot, otherwise will run on
    the host.

    Returns:
        str:
            stdout of command

    Raises:
        TurnkeyVersionError:
            If command fails. If run within chroot, it is the success/failure
            of the chroot command itself, not the command to be run.

    """
    rootfs = chrootfs if chrootfs else "/"
    cmd = command
    if rootfs != "/":
        cmd = ["chroot", rootfs, *command]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        comm = " ".join(cmd)
        raise TurnkeyVersionError(f"{comm} failed: '{proc.stderr}'")
    return proc.stdout.rstrip()


def get_debian_codename(chrootfs: str | None = None) -> str:
    """Return Debian codename of the system (leverages lsb_release)."""
    return _run_debian_cmd(["lsb_release", "--short", "--codename"], chrootfs)


def get_debian_arch(chrootfs: str | None = None) -> str:
    """Return Debian codename of the system (leverages dpkg)."""
    return _run_debian_cmd(["dpkg", "--print-architecture"], chrootfs)


def parse_tkl_version(turnkey_version: str) -> tuple[str, str, str, str]:
    """Parse TurnKey version string.

    Parse TKL version string ('turnkey-' prefix is stripped if it exists).
    It is assumed that `turnkey_version` is a valid version. As only the string
    format is validated, not the content.

    Args:
        turnkey_version (str):
            E.g. 'turnkey-core-19.0-trixie-amd64', 'lamp-19.0-trixie-amd64'.

    Returns:
        tuple[str, str, str, str]:
            appliance name, turnkey version no, Debian codename, architechture
            E.g. ("core", "19.0", "trixie", "amd64")

    Raises:
        TurnkeyVersionError:
            If version string (after optional 'turnkey-' has been removed) can
            not be split on '-' 3 times.

    """
    if turnkey_version.startswith("turnkey-"):
        turnkey_version = turnkey_version[8:]
    try:
        return tuple(turnkey_version.rsplit("-", 3))
    except IndexError as e:
        raise TurnkeyVersionError(
            "Malformed TurnKey version string: {turnkey_version}",
        ) from e


def get_turnkey_release(chrootfs: str | None = None) -> str | None:
    """Read turnkey_version file and return full TurnKey version string.

    Attempts to read /etc/turnkey_version and parse contents. If `chrootfs`
    given, will seek file relative to chroot path. TurnKey version string is
    not validated.

    Returns:
        str | None:
            Full TurnKey version string or None on error.

    """
    try:
        v_file = "etc/turnkey_version"
        v_file = join(chrootfs, v_file) if chroot else f"/{v_file}"
        return _read_file(file_path=v_file)
    except TurnkeyVersionError:
        return None


# used by turnkey-version
def get_turnkey_version(
    rootfs: str = None, fpath: str | None = None,
) -> str | None:
    """Return turnkey_version.

    On error, returns None.

    Warning: if fpath is an absolute path, rootfs will be ignored.
    """
    if rootfs is not None and isabs(fpath):
        warnings.warn(
            "Passing 'fpath' as an absolute path when 'rootfs' is also set"
            " currently ignores 'rootfs' silently. In a future version this"
            " will raise a ValueError. To suppress this warning do one of the"
            " following: Pass a relative 'fpath' or do not pass 'rootfs' when"
            " passing an absolute 'fpath'.",
            TurnkeyVersionDeprecationWarning,
            stacklevel=2,  # note user code using deprecateted funcionality
        )
        version_file_path = fpath
    if
    version_file_path = join(rootfs, fpath)

    # support pre-deprecation functionality
    if rootfs is None
    rootfs = rootfs if not None else "/"

    try:
        return 
    try:
        with open(os.path.join(rootfs, fpath)) as fob:
            return fob.read().strip()
    except OSError:
        pass
    return None


class AppVer:
    def __init__(
        self, turnkey_version: str | None = None, rootfs: str = "/",
    ) -> None:
        if not turnkey_version:
            turnkey_version = get_turnkey_version(rootfs=rootfs)
        if not turnkey_version:
            raise TurnkeyVersionError("Error: No TurnKey version found")
        if turnkey_version.startswith("turnkey-"):
            turnkey_version = turnkey_version[8:]
        self.appname, self.tklver, self.codename, self.arch \
                = turnkey_version.rsplit("-", 3)
        self.deb_codename = get_debian_codename(rootfs=rootfs)

    def app_ver(self) -> tuple[str, str, str, str]:
        return (self.appname, self.tklver, self.codename, self.arch)

    def app_json(self, deb_ver: bool = False) -> dict[str, str]:
        _json = {"name": self.appname, "tklver": self.tklver,
                 "codename": self.codename, "arch": self.arch}
        if deb_ver:
            _json["debian_codename"] = self.deb_codename
        return _json


# used by turnkey-sysinfo
def fmt_base_distribution() -> str:
    """Return a formatted distribution string.

    E.g. Debian 10/Buster
    """
    proc = subprocess.run(
        ["lsb_release", "--short", "--id", "--codename", "--release"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise TurnkeyVersionError(f"lsb_release failed: '{proc.stderr}'")
    distro, release, codename = proc.stdout.splitlines()
    return f"{distro} {release}/{codename.capitalize()}"


def fmt_sysversion() -> str:
    version_parts = []
    release = get_turnkey_release()
    if release:
        version_parts.append(f"TurnKey GNU/Linux {release}")

    basedist = fmt_base_distribution()
    if basedist:
        version_parts.append(basedist)

    if len(version_parts) == 2:
        version = f"{version_parts[0]} ({version_parts[1]})"
    elif len(version_parts) == 1:
        version = version_parts[0]
    else:
        version = "Unknown"
    return version
