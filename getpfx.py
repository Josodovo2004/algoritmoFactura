from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from cryptography import x509
import base64

namespaces = {
    'xsi': "http://www.w3.org/2001/XMLSchema-instance",
    'xsd': "http://www.w3.org/2001/XMLSchema",
    'cac': "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    'cbc': "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    'ccts': "urn:un:unece:uncefact:documentation:2",
    'ds': "http://www.w3.org/2000/09/xmldsig#",
    'ext': "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
    'qdt': "urn:oasis:names:specification:ubl:schema:xsd:QualifiedDatatypes-2",
    'udt': "urn:un:unece:uncefact:data:specification:UnqualifiedDataTypesSchemaModule:2",
    '': "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
}
def extract_pfx_details(pfx_path, pfx_password):
    # Load the .pfx file
    with open(pfx_path, 'rb') as pfx_file:
        pfx_data = pfx_file.read()

    # Load the PFX file
    with open(pfx_path, 'rb') as f:
        pfx_data = f.read()
    private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(pfx_data, pfx_password)

    # Convert the private key and certificate to PEM format
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_key_pem = certificate.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    cert_pem = certificate.public_bytes(serialization.Encoding.PEM)

    # Base64 encode the certificate for XML insertion, removing headers and footers
    cert_base64 = base64.b64encode(cert_pem).decode('utf-8')

    # Extract additional details from the certificate
    signature_algorithm = certificate.signature_algorithm_oid._name
    serial_number = certificate.serial_number
    issuer = certificate.issuer.rfc4514_string()
    subject = certificate.subject.rfc4514_string()
    not_valid_before = certificate.not_valid_before
    not_valid_after = certificate.not_valid_after
    extensions = {ext.oid._name: ext.value for ext in certificate.extensions}

    # Structure the results
    result = {
        "private_key_pem": private_key_pem.decode('utf-8'),
        "public_key_pem": public_key_pem.decode('utf-8'),
        "cert_base64": cert_base64,
        "signature_algorithm": signature_algorithm,
        "serial_number": serial_number,
        "issuer": issuer,
        "subject": subject,
        "validity_period": {
            "not_valid_before": not_valid_before,
            "not_valid_after": not_valid_after
        },
        "extensions": extensions
    }

    # Include additional certificates if present
    if additional_certificates:
        result["additional_certificates"] = [cert.public_bytes(serialization.Encoding.PEM).decode('utf-8') for cert in additional_certificates]

    return result
if __name__ == '__main__':
    # Example usage
    pfx_path = 'certificado.pfx'
    pfx_password = b'Jose_d@vid2004'
    details = extract_pfx_details(pfx_path, pfx_password)

    for key, value in details.items():
        print(f'{key}:{value}')

    for key in details.keys():
        print(key)
