#!/usr/local/autopkg/python
#
# Copyright 2022 Alex Alequin
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
See docstring for WinVersioner class
"""

import hashlib
import platform
import re
from subprocess import CalledProcessError, check_output

from autopkglib import (  # pylint: disable=import-error,unused-import
    Processor, ProcessorError)

__all__ = ["WinVersioner"]


class WinVersioner(Processor):  # pylint: disable=too-few-public-methods
    """
    Requires:
    - https://github.com/Homebrew/linuxbrew-core/blob/master/Formula/msitools.rb
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
        "pkg_version": {"description": "the version of the app"},
        "pkg_sha256": {"description": "the sha256 value of the file"},
        "pkg_file_extension": {"description": "why look it up again?"},
    }

    def get_file_extension(self):
        """determine whether its an msi or exe"""
        return self.env["pathname"].split(".")[-1]

    def get_sha256sum(self):
        """Returns the sha256 hash of a file specified."""
        sha256 = hashlib.sha256()
        with open(self.env["pathname"], "rb") as f:
            chunk = None
            while chunk != b"":
                chunk = f.read(1024)
                sha256.update(chunk)
        return sha256.hexdigest()

    def get_version(self):
        """gets the version displayed by add/or remove programs in control panel/registry"""
        patterns = {
            "msi": r"\nProductVersion\t(.*)\r",
            "exe": r"\nProduct Version\W*: (.*)\n",
        }
        pattern = patterns[self.file_extension]
        matches = re.search(pattern, self.metadata)
        return matches.group(1)

    def get_chrome_version(self):
        """google do their own thing.
        chrome includes the right version in a comment field.."""
        if self.env["pathname"] == "test":
            output = self.output
        else:
            command = ["/usr/bin/env", "msiinfo", "suminfo", self.env["pathname"]]
            output = self.run_cmd(command)
        pattern = "\nComments: (.*) Copyright.*"
        matches = re.search(pattern, output)
        try:
            return matches.group(1)
        except IndexError:
            raise ProcessorError(
                "Look into Chrome metadata, not match found in comment containing version info"
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
            raise ProcessorError(
                f"We were not able to find {pattern} in provided metadata."
            )

    def run_cmd(self, command):
        """Runs a shell command and returns its output, returns None on failure"""
        try:
            return check_output(command).decode("utf-8")
        except CalledProcessError:
            raise ProcessorError(f"Running of command: {command} has failed.")

    def main(self):
        """gimme some main"""
        self.file_extension = self.get_file_extension()
        # Build the appropriate command based on the file extension and generated vars.
        self.commands = {
            "msi": [
                "/usr/bin/env",
                "msiinfo",
                "export",
                self.env["pathname"],
                "Property",
            ],
            "exe": ["/usr/bin/env", "exiftool", self.env["pathname"]],
        }
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
            self.output(
                f"""Extracted package data:
                Display Name: {self.env["pkg_display_name"]}
                Version: {self.env["pkg_version"]}
                Hash (256): {self.env["pkg_sha256"]}
                File Extension: {self.env["pkg_file_extension"]}
                """,
                verbose_level=2,
            )
        else:
            raise ProcessorError(
                f"We were not able to produce metadata for {self.env['pathname']}"
            )


if __name__ == "__main__":
    PROCESSOR = WinVersioner()
    PROCESSOR.execute_shell()
