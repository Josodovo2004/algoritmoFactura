import os
import xmlsec
import xml.etree.ElementTree as ET
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def signature_xml(et_object, flg_firma, ruta_firma, pass_firma):
    # Assume et_object is an instance of xml.etree.ElementTree
    root = et_object
    # Load the private key and certificate from the PFX file
    with open(ruta_firma, 'rb') as pfx_file:
        pfx_data = pfx_file.read()
    private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
        pfx_data, pass_firma.encode(), default_backend()
    )

    # Create a KeysManager and add the key and certificate
    ctx = xmlsec.KeysManager()
    key = xmlsec.Key.from_memory(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ),
        xmlsec.KeyFormat.PEM,
        None
    )
    ctx.add_key(key)

    # Create a signature template
    signature_node = xmlsec.template.create(
        root, xmlsec.Transform.EXCL_C14N, xmlsec.Transform.RSA_SHA1, ns="ds"
    )

    # Add a reference to the document and apply transforms
    ref = xmlsec.template.add_reference(
        signature_node, xmlsec.Transform.SHA1
    )
    xmlsec.template.add_transform(ref, xmlsec.Transform.ENVELOPED)

    # Add KeyInfo and X509Data
    key_info = xmlsec.template.ensure_key_info(signature_node)
    xmlsec.template.add_x509_data(key_info)

    # Append the signature to the specified element
    doc_element = root.findall('.//ExtensionContent')[flg_firma]
    doc_element.append(signature_node)

    # Sign the document
    sign_ctx = xmlsec.SignatureContext(ctx)
    sign_ctx.key = key
    sign_ctx.sign(signature_node)

    # Set the ID attribute for the Signature element
    signature_node.set('Id', 'SignatureSP')

    # Extract the hash and signature value
    namespaces = {"ds": "http://www.w3.org/2000/09/xmldsig#"}
    hash_cpe = root.find('.//ds:DigestValue', namespaces).text
    firma_cpe = root.find('.//ds:SignatureValue', namespaces).text

    # Save the signed document
    et_object.write('signed_document.xml', encoding='utf-8', xml_declaration=True)

    # Return the response
    resp = {
        'respuesta': 'ok',
        'hash_cpe': hash_cpe,
        'firma_cpe': firma_cpe
    }
    return resp

if __name__ == '__main__':
    # Usage example
    # Assuming `element` is an ET.Element object representing the root of your XML document
    element = ET.Element('root')  # Replace with your actual ET.Element object
    et_object = ET.ElementTree(element)
    response = signature_xml(et_object, 0, 'path/to/your.pfx', 'your_password')
    print(response)
        