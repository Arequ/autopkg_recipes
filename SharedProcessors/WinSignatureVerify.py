#!/usr/local/autopkg/python
"""
See docstring for WinSignatureVerify class
"""

from subprocess import check_output, CalledProcessError
import re

from autopkglib import (  # pylint: disable=import-error,unused-import
    Processor,
    ProcessorError,
)

__all__ = ["WinSignatureVerify"]


class WinSignatureVerify(Processor):  # pylint: disable=too-few-public-methods
    """
    Requires:
    - https://github.com/mtrojnar/osslsigncode
    """

    description = __doc__
    input_variables = {
        "pathname": {
            "required": True,
            "description": "Full file path to verify"},
        "expected_subject": {
            "required": False,
            "description": "The expected Signer's Certificate",
        },
        "expected_signature": {
            "required": False,
            "description": "The expected CurrentDigitalSignature",
        },
    }
    output_variables = {
        "signature_verify": {"PASS or FAILED signature verification"},
    }
    cmd = [
        # for intel
        #"/usr/local/bin/osslsigncode",
        "/opt/homebrew/bin/osslsigncode",
        "verify",
    ]
    cert_info = None

    def convert_bytes_to_string(self, bytes_obj):
        """Accept a bytes objects and return utf-8 string"""
        return bytes_obj.decode("utf-8")

    def find_pattern_first_match(self, pattern):
        """Returns the first specified regex match group"""
        results = re.search(pattern, self.cert_info)
        try:
            return results.group(1)
        except AttributeError:
            return None

        return results.group(1)

    def get_cert_digitalsignature(self):
        """Searches cert data for matching expected signature and returns
        the match"""
        expected_signature = self.env["expected_signature"]
        return self.find_pattern_first_match(
            f"Current DigitalSignature.+: ({expected_signature})\\nCa"
        )

    def get_cert_subject(self):
        """Searches cert data for matching expected subject and returns
        the match"""
        expected_subject = self.env["expected_subject"]
        return self.find_pattern_first_match(
            f"Signer's certificate:\\n.+\\n.+Subject: ({expected_subject})\\n"
        )

    def run_cmd(self):
        """Runs a shell command and returns its output, returns None on failure"""
        full_command = self.cmd + [self.env["pathname"]]
        try:
            return check_output(full_command).decode("utf-8")
        except CalledProcessError:
            return None

    def main(self):
        """gimme some main"""
        self.cert_info = self.run_cmd()
        if self.cert_info is not None:
            if self.get_cert_subject() and self.get_cert_digitalsignature():
                self.env["signature_verify"] = "PASSED"
            else:
                self.env["signature_verify"] = "FAILED"

if __name__ == "__main__":
    PROCESSOR = WinSignatureVerify()
    PROCESSOR.execute_shell()