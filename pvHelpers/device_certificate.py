from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import ExtensionOID, NameOID
import base64
import pvHelpers as H

class DeviceCertificate:
    def __init__(self, cert_string):
        self.cert_string = cert_string

    # Description: Loads the certificate using the appropriate decoder based on format detection.
    # PEM is identified by its -----BEGIN CERTIFICATE----- header; everything else is treated as base64-encoded DER.
    # NOTE: .cer files exported from Windows or macOS are commonly DER-encoded (binary ASN.1)
    # rather than PEM (Base64 text with -----BEGIN CERTIFICATE----- headers).
    def _load_certificate(self):
        try:
            if self.cert_string.strip().startswith("-----BEGIN CERTIFICATE-----"):
                return x509.load_pem_x509_certificate(self.cert_string.encode(), default_backend())
            else:
                der_bytes = base64.b64decode(self.cert_string)
                return x509.load_der_x509_certificate(der_bytes, default_backend())
        except Exception:
            return None

    def verify_certificate(self):
        return self._load_certificate() is not None

    def get_certificate_details(self):
        try:
            cert = self._load_certificate()
            if cert is None:
                return None

            # Extract common name from subject and issuer
            subject_cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
            issuer_cn = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)

            issued_to = subject_cn[0].value if subject_cn else "N/A"
            issued_by = issuer_cn[0].value if issuer_cn else "N/A"

            not_after = cert.not_valid_after

            # Extract SAN extension
            try:
                san = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
                friendly_name = san.value.get_values_for_type(x509.DNSName)
            except x509.ExtensionNotFound:
                friendly_name = None
            
            return H.jdumps({
                'issued_to': issued_to,
                'issued_by': issued_by,
                'expiration_date': not_after.strftime("%m-%d-%Y"),
                'friendly_name': friendly_name
            })
        except Exception as e:
            return None
