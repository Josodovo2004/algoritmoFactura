from OpenSSL import crypto
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend

PFX_FILE = 'certificado.pfx'
PFX_PASS = b'Jose_d@vid2004'  # Note: the password must be of type bytes


with open(PFX_FILE, 'rb') as f:
    pfx_data = f.read()

private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
    pfx_data, PFX_PASS, backend=default_backend()
)

from cryptography import x509
from cryptography.hazmat.backends import default_backend

# Assuming 'certificate' is your X.509 certificate object from the previous code

# Convert the certificate to an x509 object (if not already)
cert = x509.load_pem_x509_certificate(
    certificate.public_bytes(serialization.Encoding.PEM),
    backend=default_backend()
)

# Extracting information to put into a dictionary
certificate_info = {
    "subject": cert.subject,
    "issuer": cert.issuer,
    "serial_number": cert.serial_number,
    "not_valid_before": cert.not_valid_before,
    "not_valid_after": cert.not_valid_after,
    "public_key": cert.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
}



for key in certificate_info.keys():
    print(f"{key}")

# Note: The 'subject' and 'issuer' fields are represented as Name objects and need further processing to be more readable or usable
# Here's an example of converting a Name object into a more usable dictionary
def name_to_dict(name):
    return {name.oid._name: name.value for name in name}

certificate_info["subject"] = name_to_dict(cert.subject)
certificate_info["issuer"] = name_to_dict(cert.issuer)

for key, value in certificate_info.items():
    print(f"{key}: {value}")

print('-------------subject-----------------')

for key, value in certificate_info["subject"].items():
    print(f"{key}: {value}")

print('-------------isuerr-----------------')
for key, value in certificate_info["issuer"].items():
    print(f"{key}: {value}")