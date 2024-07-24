from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from cryptography import x509

def extract_pfx_details(pfx_path, pfx_password):
    # Load the .pfx file
    with open(pfx_path, 'rb') as pfx_file:
        pfx_data = pfx_file.read()

    # Parse the .pfx file to get private key, certificate, and additional certificates
    private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
        pfx_data,
        pfx_password,
        backend=default_backend()
    )

    # Extract the private key in PEM format
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    # Extract the public key in PEM format
    public_key_pem = certificate.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    # Extract the certificate in PEM format
    cert_pem = certificate.public_bytes(serialization.Encoding.PEM).decode('utf-8')

    # Base64 encode the certificate for XML insertion, removing headers and footers
    cert_base64 = "".join(cert_pem.splitlines()[1:-1])

    # Extract the signature algorithm used in the certificate
    signature_algorithm = certificate.signature_algorithm_oid._name

    # Extract subject and issuer as dictionaries
    def name_to_dict(name):
        attributes = {}
        for attribute in name:
            attributes[attribute.oid._name] = attribute.value
        return attributes

    subject_dict = name_to_dict(certificate.subject)
    issuer_dict = name_to_dict(certificate.issuer)

    # Structure the results
    result = {
        "private_key_pem": private_key_pem,
        "public_key_pem": public_key_pem,
        "cert_base64": cert_base64,
        "signature_algorithm": signature_algorithm,
        "subject": subject_dict,
        "issuer": issuer_dict
    }

    return result

# Example usage
pfx_path = 'certificado.pfx'
pfx_password = b'Jose_d@vid2004'
details = extract_pfx_details(pfx_path, pfx_password)

for key, value in details.items():
    print(f'{key}:{value}')
