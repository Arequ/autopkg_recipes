Description: Downloads the latest version of Google Chrome Ebter (64-bit) for Windows
Identifier: com.github.arequ.download.Chrome-Enterprise-Win-64
MinimumVersion: '1.0.0'

Input:
  APP_FILENAME: GoogleChromeStandaloneEnterprise64.msi
  SUBJECT: /C=US/ST=California/L=Mountain View/O=Google LLC/CN=Google LLC
  DOWNLOAD_URL: https://dl.google.com/chrome/install/GoogleChromeStandaloneEnterprise64.msi
  NAME: Google Chrome (64-bit)

Process:
- Processor: URLDownloaderPython
  Arguments:
    url: '%DOWNLOAD_URL%'
    filename: '%APP_FILENAME%'

- Processor: WinSignatureVerify
  Arguments:
    pathname: '%pathname%'
    expected_subject: '%SUBJECT%'
    expected_signature: '%SIGNATURE%'

- Processor: EndOfCheckPhase

- Processor: StopProcessingIf
  Arguments:
    predicate: 'download_changed == FALSE'
