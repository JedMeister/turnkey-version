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
    """Read file.

    Args:
        rootfs (str):
            Path to rootfs (default '/').
        file_path (str):
            Path to text file (default '').

    Returns:
        str:
            Contents of text file as single string.

    Raises:
        TurnkeyVersionError:
            - if both rootfs and file_path
            file contents as a string
    if not rootfs and not file:
        raise TurnkeyVersionError("one of rootfs or file path are required")
    elif not rootfs and not file:
        raise TurnkeyVersionError("only one of rootfs/file path allowed")
    elif rootfs:
        file = join(rootfs, "etc/turnkey_version")
    assert file is not None
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


def _run_debian_cmd(command: list[str], rootfs: str = "/") -> str:
    """Run Debian command - in chroot if rootfs != '/'; return stdout."""
    if rootfs != "/":
        comm = ["chroot", rootfs, *command]
    proc = subprocess.run(comm, capture_output=True, text=True)
    if proc.returncode != 0:
        if comm[0] == "chroot":
            command[0] = f"chroot {command[0]}"
        raise TurnkeyVersionError(f"{command[0]} failed: '{proc.stderr}'")
    return proc.stdout.rstrip()


def get_debian_codename(rootfs: str = "/") -> str:
    """Return Debian codename of the system (leverages lsb_release)."""
    return _run_debian_cmd(["lsb_release", "--short", "--codename"], rootfs)


def get_debian_arch(rootfs: str = "/") -> str:
    """Return Debian codename of the system (leverages dpkg)."""
    return _run_debian_cmd(["dpkg", "--print-architecture"], rootfs)


def parse_tkl_version(turnkey_version: str) -> tuple[str, str, str, str]:
    """Parse TurnKey version string.

    Args:
        turnkey_version (str):
            E.g. 'turnkey-core-19.0-trixie-amd64', 'lamp-19.0-trixie-amd64'.

    Returns:
        tuple[str, str, str, str]:
            appliance name, turnkey version no, Debian codename, architechture

    Raises:
        TurnkeyVersionError:
            If parsed version string does not resolve to 4 components.

    """
    if turnkey_version.startswith("turnkey-"):
        turnkey_version = turnkey_version[8:]
    tkl_v_list = turnkey_version.rsplit("-", 3)
    try:
        tkl_version_tuple = (
            tkl_v_list[0], tkl_v_list[1], tkl_v_list[2], tkl_v_list[3],
        )
    except IndexError as e:
        raise TurnkeyVersionError(
            "Malformed TurnKey version string: {turnkey_version}",
        ) from e
    return tkl_version_tuple


def _parse_turnkey_release(version: str) -> str:
    """Get TurnKey version from full TurnKey version string.

    Args:
        version (str):
            Full TurnKey version string, with optional 'turnkey-' prefix.
            E.g. 'turnkey-core-19.0-trixie-amd64' or 'lamp-19.0-trixie-amd64'.

    Returns:
        str:
            TurnKey version number. E.g. (from above arg examples) '19.0'.

    """
    return parse_tkl_version(version)[1]


def get_turnkey_release(rootfs: str = "/") -> str | None:
    """Read 'etc/turnkey_version' and return TurnKey version number.

    Args:
        rootfs (str):
            'etc/turnkey_version' path prefix (default: '/')

    Returns:
        str | None:
            Full TurnKey version string or None on error.

    """
    turnkey_version = get_turnkey_version(rootfs=rootfs)
    if turnkey_version:
        return _parse_turnkey_release(turnkey_version)
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
