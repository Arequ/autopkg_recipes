#!/usr/local/autopkg/python
"""
See docstring for WinSignatureVerify class
"""

import re
from subprocess import CalledProcessError, check_output

from autopkglib import (  # pylint: disable=import-error,unused-import
    Processor, ProcessorError)

__all__ = ["WinSignatureVerify"]


class WinSignatureVerify(Processor):  # pylint: disable=too-few-public-methods
    """
    Requires:
    - https://github.com/mtrojnar/osslsigncode
    """

    description = __doc__
    input_variables = {
        "pathname": {"required": True, "description": "Full file path to verify"},
        "expected_subject": {
            "required": False,
            "description": "The expected Signer's Certificate",
        },
        "expected_hash": {
            "required": False,
            "description": "The expected CurrentDigitalSignature",
        },
    }
    output_variables = {
        "signature_verify": {"PASS or FAILED signature verification"},
    }
    cmd = [
        "/usr/bin/env",
        "osslsigncode",
        "verify",
    ]
    cert_info = None
    extension = None
    expected_hash = None
    expected_subject = None

    def find_pattern_first_match(self, pattern):
        """Returns the first specified regex match group"""
        results = re.search(pattern, self.cert_info)
        try:
            return results.group(1)
        except AttributeError:
            return None

    def get_cert_hash(self):
        """Searches cert data for matching expected signature and returns
        the match"""
        expected_hash = self.env["expected_hash"]
        if self.extension == "msi":
            return self.find_pattern_first_match(
                f"Current DigitalSignature.+: ({expected_hash})\\nCa"
            )
        elif self.extension == "exe":
            return self.find_pattern_first_match(
                f"Current message digest.+: ({expected_hash})\\nCa"
            )

    def get_cert_subject(self):
        """Searches cert data for matching expected subject and returns
        the match"""
        expected_subject = self.env["expected_subject"]
        return self.find_pattern_first_match(
            f"Signer's certificate:\\n.+\\n.+Subject: ({re.escape(expected_subject)})\\n"
        )

    def certificate_verify_result(self):
        """Gets the result of the signature verfication"""
        status = self.cert_info.split("\n")[-2]
        if status == "Succeeded":
            return True
        elif status == "Failed":
            return False

    def run_cmd(self):
        """Runs a shell command and returns its output, returns None on failure"""
        full_command = self.cmd + [self.env["pathname"]]
        try:
            return check_output(full_command).decode("utf-8")
        except CalledProcessError:
            print("we failed")
            return None

    def main(self):
        """gimme some main"""
        self.extension = self.env["pathname"].split(".")[-1]
        self.cert_info = self.run_cmd()
        if self.cert_info is not None:
            if "expected_hash" in self.env and "expected_subject" in self.env:
                if self.get_cert_subject() and self.get_cert_hash():
                    self.env["signature_verify"] = "PASSED"
                else:
                    self.env["signature_verify"] = "FAILED"
            else:
                if self.certificate_verify_result():
                    self.env["signature_verify"] = "PASSED"
                else:
                    self.env["signature_verify"] = "FAILED"
        else:
            self.env["signature_verify"] = "FAILED"

        if self.env["signature_verify"] == "PASSED":
            self.output("Signing chain validation status: PASSED", verbose_level=1)
        else:
            self.output("Signing chain validation status: FAILED", verbose_level=1)


if __name__ == "__main__":
    PROCESSOR = WinSignatureVerify()
    PROCESSOR.execute_shell()
