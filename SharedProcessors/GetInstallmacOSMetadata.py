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

# This is heavily influenced by installinstallmacos.py by Greg Neagle
# https://github.com/munki/macadmin-scripts/blob/main/installinstallmacos.py


"""
Gets the download URL of latest version of macOS Installer App from Apple's CDN
This script makes a lot of assumptions and can break.
"""

import plistlib
import ssl
import urllib.request
from xml.dom import minidom
from xml.parsers.expat import ExpatError

from autopkglib import Processor, ProcessorError


class GetInstallmacOSMetadata(Processor):
    """
    Processor to get the download URL of the latest version of macOS Installer App from Apple's CDN
    """

    description = __doc__
    input_variables = {
        "MACOS_VERSION": {
            "required": False,
            "description": "TODO: not implemented yet. Passed if you want to get the URL for a specific macOS version.",
        },
        "MACOS_BUILD": {
            "required": False,
            "description": "TODO: not implemented yet. Passed if you want to get the URL for a specific macOS build.",
        },
        "SUCATALOG_URL": {
            "required": False,
            "description": "URL to Apples Software Update Catalog. Defaults to latest known catalog.",
            "default": "https://swscan.apple.com/content/catalogs/others/index-10.16-10.15-10.14-10.13-10.12-10.11-10.10-10.9"
            "-mountainlion-lion-snowleopard-leopard.merged-1.sucatalog",
        },
    }
    output_variables = {
        "url": {
            "description": "Download URL",
            "required": True,
        },
        "display_name": {
            "description": "METADATA",
            "required": True,
        },
        "version": {
            "description": "version",
            "required": True,
        },
        "build": {
            "description": "build",
            "required": True,
        },
    }

    def get_remote_plist(self, url):
        """
        Helper function to download the remote plist from the given URL

        :param url: URL to download the plist from
        :return: dictionary representation of the plist data
        """
        try:
            context = ssl.create_default_context()
            with urllib.request.urlopen(url, timeout=30) as response:
                plist_data = response.read()
        except urllib.error.URLError as e:
            print(f"Error downloading plist from URL {url}: {e}")
            return None
        plist_data_dict = plistlib.loads(plist_data)
        return plist_data_dict if plist_data_dict else plist_data

    def has_install_assistant_pkg(self, product):
        """
        Helper function to check if the given product has an InstallAssistant.pkg

        :param product: product dictionary to check
        :return: True if the product has an InstallAssistant.pkg, False otherwise
        """
        emi_key = "ExtendedMetaInfo"
        iapi_key = "InstallAssistantPackageIdentifiers"
        if product.get(emi_key) and product.get(emi_key).get(iapi_key):
            return True
        return False

    def find_install_assistant_pkg(self, product):
        """
        Helper function to find the InstallAssistant.pkg in the given product

        :param product: product dictionary to find the InstallAssistant.pkg in
        :return: list of dictionaries representing the InstallAssistant.pkg packages
        """
        return [
            pkg
            for pkg in product["Packages"]
            if pkg["URL"].endswith("InstallAssistant.pkg")
        ]

    def get_metadata(self, product):
        """
        Helper function to get the metadata (title, build, version) of the given product

        :param product: product dictionary to get the metadata from
        :return: tuple of metadata (title, build, version)
        """
        dist_url = product["Distributions"].get("English")
        try:
            context = ssl.create_default_context()
            with urllib.request.urlopen(dist_url, timeout=30) as response:
                dist_data = response.read().decode()
        except urllib.error.URLError as e:
            print(f"Error downloading .dist from URL {dist_url}: {e}")
            return None, None, None

        try:
            xmldoc = minidom.parseString(dist_data)
            title = xmldoc.getElementsByTagName("title")[0].firstChild.nodeValue
            build = xmldoc.getElementsByTagName("string")[0].firstChild.nodeValue
            version = xmldoc.getElementsByTagName("string")[1].firstChild.nodeValue
        except ExpatError as e:
            print("Error parsing XML:", e)
            return None, None, None
        return title, build, version

    def get_macos_installers(self, catalog):
        """
        Helper function to get the macOS installers from the given catalog

        :param catalog: catalog dictionary to get the macOS installers from
        :return: dictionary of macOS installers
        """
        for product_key in list(catalog["Products"].keys()):
            product = catalog["Products"][product_key]
            if self.has_install_assistant_pkg(product):
                catalog["Products"][product_key][
                    "Packages"
                ] = self.find_install_assistant_pkg(product)
                if len(catalog["Products"][product_key]["Packages"]) == 1:
                    catalog[product_key] = catalog["Products"][product_key]
                    (title, build, version) = self.get_metadata(catalog[product_key])
                    catalog[product_key]["title"] = title
                    catalog[product_key]["build"] = build
                    catalog[product_key]["version"] = version
        keys_to_delete = ["CatalogVersion", "ApplePostURL", "IndexDate", "Products"]
        for key in keys_to_delete:
            del catalog[key]
        return catalog

    def main(self):
        """
        Main function to run the processor
        """
        catalog = self.get_remote_plist(self.env["SUCATALOG_URL"])
        macos_installers = self.get_macos_installers(catalog)
        sorted_installers = {
            k: v
            for k, v in sorted(
                macos_installers.items(),
                key=lambda item: item[1]["version"],
                reverse=True,
            )
        }
        latest = next(iter(sorted_installers.values()))
        self.env["display_name"] = latest["title"]
        self.env["version"] = latest["version"]
        self.env["build"] = latest["build"]
        self.env["url"] = latest["Packages"][0]["URL"]
