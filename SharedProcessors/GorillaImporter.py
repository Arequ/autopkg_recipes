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

"""See docstring for GorillaImporter class"""

import os
import pathlib
import shutil

from autopkglib import Processor, ProcessorError
from ruamel.yaml import YAML

__all__ = ["GorillaImporter"]


class GorillaImporter(Processor):
    """Imports a pkg or dmg to the Munki repo."""

    input_variables = {
        "gorilla_repo": {
            "description": "Path to a mounted Munki repo.",
            "required": True,
        },
        "gorilla_catalog": {
            "description": "The catalog you intend on automatically updating..",
            "required": True,
        },
        "gorilla_subdirectories": {
            "required": True,
            "description": "Path to pkg: nupkg, msi, exe, ps1 relative to URL",
        },
        "pkg_shortname": {
            "required": True,
            "description": "CASE SENSITIVEThe pkg shortname,\
                         corresponds to the primary key in the pkg hashes",
        },
        "pkg_version": {
            "required": True,
            "description": "Float64 value of importing version.",
        },
        "pkg_display_name": {
            "required": False,
            "description": "Display name for pkg, will be same as shortname is none is specified.",
        },
        "pkg_check": {
            "required": False,
            "description": "An optional hash with instructions for the gorilla style checks",
        },
        "pkg_dependencies": {
            "required": False,
            "description": "An optional array with required dependencies.",
        },
        "pkg_installer_arguments": {
            "required": False,
            "description": "An optional array with gorilla installer options.",
        },
        "pkg_uninstaller_arguments": {
            "required": False,
            "description": "An optional array with gorilla uninstaller options.",
        },
        "yaml_entry": {
            "required": False,
            "description": "If you want to specify all the gorilla args",
        },
    }
    output_variables = {
        "pkg_repo_path": {
            "description": (
                "The repo path where the pkg was written. "
                "Empty if item not imported."
            )
        },
        "gorilla_repo_changed": {"description": "True if item was imported."},
        "gorilla_importer_summary_result": {
            "description": "Description of interesting results."
        },
    }
    description = __doc__

    def yaml_to_dict(self):
        """takes yaml and turns it into a dict"""
        self.yaml = YAML()
        self.yaml.default_flow_stye = False
        with open(self.yaml_file, "r") as f:
            return self.yaml.load(f.read())

    def write_out_catalog(self, catalog):
        """ Writes out a yaml file """
        with open(self.yaml_file, "w") as f:
            self.yaml.dump(catalog, f)

    def hashes_are_identical(self):
        """compares sha256sum of existing file with remotefile"""
        try:
            existing_file_hash = self.pkg_entry["installer"]["hash"]
        except KeyError:
            existing_file_hash = None
        new_file_hash = self.env["pkg_sha256"].upper()
        return existing_file_hash == new_file_hash

    def backup_catalog(self):
        """Backs up old version"""
        shutil.copy(self.yaml_file, f"{self.yaml_file}.bak")

    def update_pkg_entry(self):
        """Updates the package catalog entry with metadata extracted from the downloaded
        package file"""
        self.pkg_entry["display_name"] = self.env[
            "pkg_shortname"
        ]  # is not actually in use..
        self.pkg_entry["version"] = self.env["pkg_version"]

        # If it's in the catalog, it should have an installer key, no?
        self.pkg_entry["installer"]["hash"] = self.env["pkg_sha256"].upper()
        self.pkg_entry["installer"]["location"] = os.path.join(
            self.env["gorilla_subdirectories"], self.dest_filename
        )
        self.pkg_entry["installer"]["type"] = self.env["pkg_file_extension"]
        # We may have specified additional arguments, override everything with those.
        try:
            self.pkg_entry["installer"]["arguments"] = self.env[
                "pkg_installer_arguments"
            ]
        except KeyError:
            pass

        if "check" in self.pkg_entry.keys():
            if "registry" in self.pkg_entry["check"].keys():
                self.pkg_entry["check"]["registry"]["name"] = self.env[
                    "pkg_display_name"
                ]
                self.pkg_entry["check"]["registry"]["version"] = self.env["pkg_version"]

        if "uninstaller" in self.pkg_entry.keys():
            self.pkg_entry["uninstaller"]["hash"] = self.env["pkg_sha256"].upper()
            self.pkg_entry["uninstaller"]["location"] = os.path.join(
                self.env["gorilla_subdirectories"], self.dest_filename
            )
            self.pkg_entry["uninstaller"]["type"] = self.env["pkg_file_extension"]
            try:
                self.pkg_entry["uninstaller"]["arguments"] = self.env[
                    "pkg_uninstaller_arguments"
                ]
            except KeyError:
                pass

    def copy_pkg_to_repo(self):
        """Grabs the downloaded file pathname to move into the repo"""
        dest_path = os.path.join(
            self.env["gorilla_repo"], "pkgs", self.env["gorilla_subdirectories"]
        )
        if not os.path.isdir(dest_path):
            pathlib.Path(dest_path).mkdir(parents=True, exist_ok=True)
        self.env["pkg_repo_path"] = os.path.join(dest_path, self.dest_filename)
        shutil.copy(self.env["pathname"], self.env["pkg_repo_path"])
        self.output(
            f"Copied {self.env['pathname']} to {self.env['pkg_repo_path']}",
            verbose_level=2,
        )

    def main(self):
        """ do the thing """
        self.yaml_file = os.path.join(
            self.env["gorilla_repo"], "catalogs", f"{self.env['gorilla_catalog']}.yaml"
        )
        catalog = self.yaml_to_dict()
        if not catalog:
            catalog = {}
        self.dest_filename = f"{self.env['pkg_shortname']}-{self.env['pkg_version']}.{self.env['pkg_file_extension']}"
        self.copy_pkg_to_repo()

        try:
            self.pkg_entry = catalog[self.env["pkg_shortname"]]
        except KeyError:
            self.pkg_entry = {
                "installer": {"hash": None, "location": None, "type": None},
                "check": {"registry": {"version": None, "name": None}},
                "uninstaller": {"hash": None, "location": None, "type": None},
            }

        if "yaml_entry" in self.env:
            for key in self.env["yaml_entry"]:
                self.pkg_entry[key] = self.env["yaml_entry"][key]

        if self.hashes_are_identical():
            self.output("File hashes are identical. Stopping processor.")
            self.env["gorilla_repo_changed"] = False
            return

        self.update_pkg_entry()
        self.output(self.pkg_entry)
        # Update the catalog to include the new entries data.
        catalog[self.env["pkg_shortname"]] = self.pkg_entry
        # Backup catalog, just in case..
        shutil.copy(self.yaml_file, f"{self.yaml_file}.bak")

        self.write_out_catalog(catalog)
        self.env["gorilla_importer_summary"] = self.pkg_entry
        self.env["gorilla_repo_changed"] = True
        self.output(f"{self.pkg_entry} has been added to the catalog.")


if __name__ == "__main__":
    PROCESSOR = GorillaImporter()
    PROCESSOR.execute_shell()
