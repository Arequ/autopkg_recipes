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
import plistlib
import subprocess

from autopkglib import Processor, ProcessorError

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
                         corresponds to the primary key in the pkg hashes"
        },
        "pkg_version": {
            "required": True,
            "description": "Float64 value of importing version."
        },
        "pkg_display_name": {
            "required": False,
            "description": "Display name for pkg, will be same as shortname is none is specified."
        },
        "pkg_check": {
            "required": False,
            "description": "An optional hash with instructions for the gorilla style checks"
        },
        "pkg_dependencies": {
            "required": False,
            "description": "An optional array with required dependencies."
        },
        "pkg_installer": {
            "required": False,
            "description": "An optional hash with gorilla installer options."
        },
        "pkg_uninstaller": {
            "required": False,
            "description": "An optional hash with gorilla uninstaller options."
        },
    }
    output_variables = {
        "pkginfo_repo_path": {
            "description": (
                "The repo path where the pkginfo was written. "
                "Empty if item not imported."
            )
        },
        "pkg_repo_path": {
            "description": (
                "The repo path where the pkg was written. "
                "Empty if item not imported."
            )
        },
        "munki_info": {
            "description": "The pkginfo property list. Empty if item not imported."
        },
        "munki_repo_changed": {"description": "True if item was imported."},
        "munki_importer_summary_result": {
            "description": "Description of interesting results."
        },
    }
    description = __doc__

    def yaml_to_dict(self, file):
        """takes yaml and turns it into a dict"""

    def compare_file_hashes(self):
        """compares sha256sum of existing file with remotefile"""

    def modify_entry(self):

    def check_if_pkg_existing(self):

    def load_yaml_2_dict(yaml_file):


class Playa(Playa):
    def main(self):
        inputs = {
            "display_name"
        }
        with open(f"{self.env['gorilla_repo']}/catalogs/{self.env['gorilla_catalog']}") as f:
            catalog = yaml.load(f, Loader=yaml.FullLoader)
        if self.env['pkg_shortname'].lower() in [shortname.lower() for shortname in catalog.keys()]:

shortname = 'nessus'
version = '8.5.1.9999'

{'display_name': 'nessus', 'check': {'registry': {'name': 'Nessus Agent (x64)', 'version': '8.5.1.9999'}}, 'installer': {'location': 'pkgs/nessus/nessus-7.5.1.20012.msi', 'hash': 'ARANDOMHASHVALUE', 'arguments': ['/qn', '/norestart'], 'type': 'msi'}, 'uninstaller': {'location': 'pkgs/nessus/nessus-7.5.1.20012.msi', 'hash': 'E165770383BC176E818B7611F521BDAAD8B14F59D545ED2861A24D9D3CF00CFB', 'type': 'msi'}, 'version': '8.5.1.9999'}


if __name__ == "__main__":
    PROCESSOR = GorillaImporter()
    PROCESSOR.execute_shell()


## Read

    print(data)

## Write
with open('./catalogs/alpha.yaml') as f:
    data = yaml.load(f, Loader=yaml.FullLoader)
    print(data)
    sorted_data = yaml.dump(data, sort_keys=True)
    print(sorted_data)

with open('./catalogs/alpha_test.yaml', 'w') as f:
    yaml.dump(data, f, explicit_start=True, sort_keys=False)

"""
Guesstimate preferred order of keys to keep things in line...
---
GorillaPkgName:
  dependencies: if required seem to be top of list.
  display_name: HumanReadableName # not actually used anywhere..
  check:
    file:
      - path: 'required_full_pathname_to_see_if_file_exists'
        version: 'optional version of file found in Details under properties'
        hash: 'option sha256 of item at path'
    registry:
      name: 'Name as it appears in registry' # HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\
      version: 0.0.0.0 # version as it appears in same registry location
    script: |
      a powershell script..
      that can go on
      for lines...
      needs to
      exit 0
  installer:
    location: 'required file_path relative to gorilla repo'
    hash: 'required sha256 of file at location'
    arguments:
      - 'Optional'
      - 'List'
      - 'Of arguments'
    type: 'required define installer type (nupkg, msi, exe, ps1)'
  uninstaller:
    location: 'required file_path relative to gorilla repo'
    hash: 'required sha256 of file at location'
    arguments:
      - 'Optional'
      - 'List'
      - 'Of arguments'
    type: 'required define installer type (nupkg, msi, exe, ps1)'
"""
# Chrome input examples..
pkg_sha256 = "076337e41345fe3a538c813782e771bdc2575cada95e779101b0fadb55b4ecc8"
pkg_version = "103.0.5060.53"
pathname = "./"

# For things like google chrome, we can't completely rely on the file hash because for some odd reason...
# They thought it was a good idea to have a different file hash per download as a way to track where stuff
# is being downloaded from I presume. For example, I can't find the link that produces the hash that is
# currently uploaded on the s3 bucket...

# So we'll move on to comparing the existing msi files version..
# We can do an MSIInspect or we can do it from the filename since we expect every file to have 
# a correct version name in it..
# We'll start off with filename as path of least resistance for at least MSI and EXE files..

def get_file_extension(self):
    """determine whether its an msi or exe"""
    return self.env["pathname"].split(".")[-1]

def find_existing_entry(self):
    # There may be an existing entry somewhere with the specific alterations required to install
    # a specific piece of software, let's look for that first.
    os.glob
def get_msi_or_exe_version():

def determine_file_extension():

