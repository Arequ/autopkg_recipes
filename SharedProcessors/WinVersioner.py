#!/usr/local/autopkg/python
"""
See docstring for WinVersioner class
"""

import hashlib
import os
import re
from subprocess import CalledProcessError, check_output

from autopkglib import (  # pylint: disable=import-error,unused-import
    Processor, ProcessorError)

__all__ = ["WinVersioner"]


class WinVersioner(Processor):  # pylint: disable=too-few-public-methods
    """Extracts an MSI or EXEs Metadata to gather version/control
    panel displayname.
    Requires:
    - brew install msitools
    - brew install exiftools
    """

    description = __doc__
    input_variables = {
        "pathname": {
            "required": True,
            "description": "Full file path to gather data from.",
        },
    }
    output_variables = {
        "pkg_display_name": {
            "description": "the app name as it shows up in control panel"
        },
        "pkg_version": {"description": "the verison of the app"},
        "pkg_sha256": {"description": "the sha256 value of the file"},
        "pkg_file_extension": {"description": "why look it up again?"},
    }

    def __init__(self):
        """Defining vars we will eventually need"""
        self.file_extension = None
        self.binaries = {
            "msi": {
                "arm": "/opt/homebrew/bin/msiinfo",
                "i386": "/usr/local/bin/msiinfo",
            },
            "exe": {
                "arm": "/opt/homebrew/bin/exiftool",
                "i386": "/usr/local/bin/exiftool",
            },
        }
        self.binary = None
        self.commands = {
            "msi": [self.binary, "export", self.env["pathname"], "Property"],
            "exe": [self.binary, self.env["pathname"]],
        }
        self.metadata = None

    def get_file_extension(self):
        """determine whether its an msi or exe"""
        return self.env["pathname"].split(".")[-1]

    def get_proper_arch(self):
        """Autopkg prebuilt python identifies as x86_64 using platform"""
        command = ["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"]
        output = self.run_cmd(command)
        if "Apple" in output:
            return "arm"
        return "i386"

    def get_sha256sum(self):
        """Returns the sha256 hash of a file specified."""
        sha256 = hashlib.sha256()
        with open(self.env["pathname"], "rb") as pkg_file:
            chunk = None
            while chunk != b"":
                chunk = pkg_file.read(1024)
                sha256.update(chunk)
        return sha256.hexdigest()

    def get_version(self):
        """gets the version respected by add/or remove
        programs in control panel"""
        patterns = {
            "msi": r"\nProductVersion\t(.*)\r",
            "exe": r"\nProduct Version\W*: (.*)\n",
        }
        # Chrome does its own thing...
        pattern = patterns[self.file_extension]
        matches = re.search(pattern, self.metadata)
        return matches.group(1)

    def get_chrome_version(self):
        """google do their own thing"""
        # freakin' chrome includes the right version in a comment field..
        command = [self.binary, "suminfo", self.env["pathname"]]
        output = self.run_cmd(command)
        pattern = "\nComments: (.*) Copyright.*"
        matches = re.search(pattern, output)
        try:
            return matches.group(1)
        except IndexError:
            raise ProcessorError(  # pylint: disable=raise-missing-from
                (
                    "Look into Chrome metadata, not match found in",
                    " comment containing version info. Error:",
                )
            )

    def get_display_name(self):
        """gets the installed (control panel) displayname"""
        patterns = {
            "msi": r"\nProductName\t(.*)\r",
            "exe": r"\nProduct Name\W*: (.*)\n",
        }
        pattern = patterns[self.file_extension]
        matches = re.search(pattern, self.metadata)
        try:
            return matches.group(1)
        except IndexError:
            raise ProcessorError(  # pylint: disable=raise-missing-from
                (f"We were not able to find {pattern} in provided metadata.")
            )

    def run_cmd(self, command):
        """Runs a shell command and returns its output,
        returns None on failure"""
        try:
            return check_output(command).decode("utf-8")
        except CalledProcessError:
            raise ProcessorError(  # pylint: disable=raise-missing-from
                f"Running of command: {command} has failed."
            )

    def main(self):
        """gimme some main"""
        proc_arch = self.get_proper_arch()
        self.file_extension = self.get_file_extension()
        self.binary = self.binaries[self.file_extension][proc_arch]
        # We know what binary we need, let's stop if it doesn't exist.
        if not os.path.isfile(self.binary):
            raise ProcessorError(
                (
                    f"FailedDeps: {self.binary} does not exist on disk.",
                    " Please use homebrew to install it.",
                )
            )
        # Build the appropriate command based on the file
        # extension and generated vars.
        command = self.commands[self.file_extension]
        self.metadata = self.run_cmd(command)
        if self.metadata:
            self.env["pkg_display_name"] = self.get_display_name()
            self.env["pkg_sha256"] = self.get_sha256sum()
            self.env["pkg_file_extension"] = self.file_extension
            if "chrome" in self.env["pkg_display_name"].lower():
                self.env["pkg_version"] = self.get_chrome_version()
            else:
                self.env["pkg_version"] = self.get_version()
        else:
            raise ProcessorError(
                ("We were not able to produce metadata for ", self.env["pathname"])
            )


if __name__ == "__main__":
    PROCESSOR = WinVersioner()
    PROCESSOR.execute_shell()
