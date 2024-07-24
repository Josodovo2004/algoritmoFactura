import subprocess
import json
import subprocess
import json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import tostring
from signxml import XMLSigner, methods
import os
import base64

def call_php_script(ruta, ruta_firma, pass_firma, flg_firma=0):
    # Construct the command to run the PHP script
    command = [
        'C:\php', 'signature.php',  # Adjust the path to your PHP script
        ruta,
        ruta_firma,
        pass_firma,
        str(flg_firma)
    ]

    try:
        # Execute the PHP script
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        # Output from PHP script
        output = result.stdout

        # Assuming the PHP script outputs JSON
        response = json.loads(output)
        return response

    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running the PHP script: {e}")
        print(f"Error output: {e.stderr}")
        return None

# Step 1: Extract Certificate and Private Key from PFX
def extract_from_pfx(pfx_path, pfx_password):
    with open(pfx_path, 'rb') as f:
        pfx_data = f.read()
    private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
        pfx_data, pfx_password.encode(), backend=default_backend()
    )
    return private_key, certificate

# Step 2: Create XML Structure
def create_xml_structure():
    superroot = ET.Element("Invoice")
    ET.register_namespace('xsi', "http://www.w3.org/2001/XMLSchema-instance")
    ET.register_namespace('xsd', "http://www.w3.org/2001/XMLSchema")
    ET.register_namespace('cac', "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2")
    ET.register_namespace('cbc', "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2")
    ET.register_namespace('ccts', "urn:un:unece:uncefact:documentation:2")
    ET.register_namespace('ds', "http://www.w3.org/2000/09/xmldsig#")
    ET.register_namespace('ext', "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2")
    ET.register_namespace('qdt', "urn:oasis:names:specification:ubl:schema:xsd:QualifiedDatatypes-2")
    ET.register_namespace('udt', "urn:un:unece:uncefact:data:specification:UnqualifiedDataTypesSchemaModule:2")
    ET.register_namespace('', "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2")
    root = ET.SubElement(superroot,"ext:UBLExtensions")
    ubl_extension = ET.SubElement(root, "ext:UBLExtension")
    extension_content = ET.SubElement(ubl_extension, "ext:ExtensionContent")
    signature = ET.SubElement(extension_content, "ds:Signature", {"Id": "signatureKG"})
    signed_info = ET.SubElement(signature, "ds:SignedInfo")
    
    canonicalization_method = ET.SubElement(signed_info, "ds:CanonicalizationMethod", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315#WithComments")
    signature_method = ET.SubElement(signed_info, "ds:SignatureMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#dsa-sha1")
    reference = ET.SubElement(signed_info, "ds:Reference", URI="")
    transforms = ET.SubElement(reference, "ds:Transforms")
    transform = ET.SubElement(transforms, "ds:Transform", Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
    digest_method = ET.SubElement(reference, "ds:DigestMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
    digest_value = ET.SubElement(reference, "ds:DigestValue")
    digest_value.text = "+pruib33lOapq6GSw58GgQLR8VGIGqANloj4EqB1cb4="
    
    return superroot

# Step 3: Sign the XML Document
# This is a complex process that involves generating a digest of the parts of the XML you want to sign,
# then using the private key to sign that digest, and finally inserting the signature into the XML.
# There are libraries like `signxml` in Python that can help with XML signatures.
def sign_xml(private_key, certificate, xml_root):
    # Prepare the XML by inserting the certificate
    insert_certificate(xml_root, certificate)
    
    # Create an XMLSigner instance with the desired configuration
    signer = XMLSigner(method=methods.enveloped, signature_algorithm="rsa-sha256")
    
    # Sign the XML. The sign function expects the XML root element, the private key, and the certificate
    signed_root = signer.sign(xml_root, key=private_key, cert=certificate)
    
    # Return the signed XML root element
    return signed_root
# Step 4: Insert the Certificate
def insert_certificate(xml_element, certificate):
    # Convert the certificate to PEM format and insert it into the XML structure
    cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
    # You might need to clean up the PEM string (remove headers and newlines) before embedding
    cert_clean = cert_pem.decode().replace("-----BEGIN CERTIFICATE-----", "").replace("-----END CERTIFICATE-----", "").replace("\n", "")
    # Insert cert_clean into the XML at the correct location
    # This is a placeholder; you'll need to adjust it based on your XML structure

def main(pfx_path, pfx_password):
    private_key, certificate = extract_from_pfx(pfx_path, pfx_password)
    xml_root = create_xml_structure()
    signed_xml = sign_xml(private_key, certificate, xml_root)
    
    # Convert the signed XML back to a string or bytes for output/storage
    signed_xml_str = ET.tostring(signed_xml, encoding='utf8', method='xml')
    print(signed_xml_str)


# Example usage
if __name__ == "__main__":
    pfx_path = "certificado.pfx"
    pfx_password = "Jose_d@vid2004"
    main(pfx_path, pfx_password)


