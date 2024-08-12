from lxml import etree as ET
import xmlsec
from generate import generateXmlFactura
from datetime import date, time
from getpfx import extract_pfx_details
from dxmlFromString import dxmlFromString
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
import io
import zipfile
import base64
import os
import xmlsec
import requests

emisor = {
    'ruc' : '20605138293',
    'razon_social' : 'Empresa 01',
    'direccion' : 'ALZAMORA N 128 - IQUITOS - MAYNAS - LORETO',
    'usuario_emisor' : 'MODDATOS',
    'clave_emisor' : 'MODDATOS',
    'provincia' : 'Maynas',
    'Departamento' : 'Loreto',
    'Distrito' : 'Iquitos',
}

comprobante = {
    'serie' : 'F001',
    'correlativo' : '00000001',
    'fecha_emision' : str(date.today()),
    'tipo' : '01',
}

ubigeos = {
    "Iquitos":160101,
    "Punchana": 160108,
    "San Juan": 160113,
    "Belen": 160112,
}

codigoImpuestos = {
    "IGV" : (1000, "S","VAT"),
    "IVAP" : (1016, "S","VAT"),
    "ISC" : (2000, "S","EXC"),
    "EXP" : (9995,"G", "FRE"),
    "GRA" : (9996,"Z", "FRE"),
    "EXO" : (9997,"E", "VAT"),
    "INA" : (9998,"O", "FRE"),
    "OTR" : (9999,"S", "OTH"),
}

tipoOperacion = {
    "Gravado": 10,
    "Exonerado": 20,
    "Inafecto": 30,
}

tipoDocumento = {
    "Factura" : '01',
    "Boleta" : '03',
}

data = {
    "emisor": {
        "DocumentoEmisor": "20605138293",
        "RazonSocialEmisor": "Empresa Emisora S.A.C.",
        "NombreComercialEmisor": "Empresa Emisora",
        "direccion": "Calle Falsa 123, San Isidro, Lima, Peru",
        "ubigeo": ubigeos["Iquitos"],
        "codigoPais": "PE",
        "usuarioSol": "adminsol",
        "claveSol": "adminclave",
        "TipoDocumento": tipoDocumento["Factura"],  # Assuming 6 is for RUC
        "provincia" : "Maynas",
        "departamento" : "Loreto",
        "distrito" : "Iquitos",
        "calle" : "ALZAMORA N 128",	
    },
    "adquiriente": {
        "TipoDocumentoAdquiriente": "6",  # Assuming 6 is for RUC
        "NumeroDocumentoAdquiriente": "20543211234",
        "razonSocial": "Empresa Cliente S.A.C.",
        'CalleComprador' : 'Calle Falsa 123',
        'distritoComprador' : 'San Juan',
        'departamentoComprador' : 'Loreto',
        'provinciaComprador' : 'Maynas',
    },
    "comprobante": {
        "serieDocumento": "F001",
        "numeroDocumento": "123456",
        "fechaEmision": "2023-04-15",
        "codigoMoneda": "PEN",  # Assuming PEN for Peruvian Sol
        'ImporteTotalVenta': "1500.00",
        'MontoTotalImpuestos': '270.00',
        "totalOperacionesGravadas": '1500.00',
        "totalOperacionesExoneradas": '0.00',
        "totalOperacionesInafectas": '0.00',
        "totalConImpuestos" : '1770.00',
    },
    "taxes" : {
        "IGV": {  # Impuesto General a las Ventas
            'MontoTotalImpuesto': '270.00',  # Total del IGV aplicado
            "tasaImpuesto": '18',  # Tasa del IGV en porcentaje
            "operacionesGravadas": '1500.00',  # Total de operaciones gravadas sujetas a IGV
            'cod1' : '1000',
            'cod2' : 'IGV',
            'cod3' : 'VAT',
    } },
    # Puedes agregar más tipos de impuestos aquí
    "Items": [
        {
            "unidadMedida": "NIU",  # Assuming NIU for product unit
            'CantidadUnidadesItem': '10',
            "id": "P001",
            'NombreItem': 'Producto 1',
            'DescripcionItem': "",
            "valorUnitario": '100.00',
            'PrecioVentaUnitario': '118.00',  # Including IGV
            "tipoPrecio": "01",  # Assuming 01 is for unit price with taxes
            'MontoTotalImpuestoItem': '180.00',
            "tipoAfectacionIgv": codigoImpuestos["IGV"][0],
            "totalValorVenta": '1000.00',
            'ValorVentaItem': '1180.00',
            'totalTax' : '270',
            'tax' : {
                "IGV": {  # Impuesto General a las Ventas
                'MontoTotalImpuesto': '270.00',  # Total del IGV aplicado
                "tasaImpuesto": '18',  # Tasa del IGV en porcentaje
                "operacionesGravadas": '1500.00',  # Total de operaciones gravadas sujetas a IGV
                'cod1' : '1000',
                'cod2' : 'IGV',
                'cod3' : 'VAT',
                    }
                }
        },
        {
            "unidadMedida": "NIU",
            'CantidadUnidadesItem': '5',
            "id": "P002",
            'NombreItem': 'Producto 2',
            'DescripcionItem': "",
            "valorUnitario": '50.00',
            'PrecioVentaUnitario': '59.00',  # Including IGV
            "tipoPrecio": "01",
            'MontoTotalImpuestoItem': '90.00',
            "tipoAfectacionIgv": codigoImpuestos["IGV"][0],
            "totalValorVenta": '500.00',
            'ValorVentaItem': '590.00',
            'totalTax' : '270',
            'tax' : {
                "IGV": {  # Impuesto General a las Ventas
                'MontoTotalImpuesto': '270.00',  # Total del IGV aplicado
                "tasaImpuesto": '18',  # Tasa del IGV en porcentaje
                "operacionesGravadas": '1500.00',  # Total de operaciones gravadas sujetas a IGV
                'cod1' : '1000',
                'cod2' : 'IGV',
                'cod3' : 'VAT',
                    }
                }
        }
    ]
    }
name = f'{data["emisor"]["DocumentoEmisor"]}-01-{data["comprobante"]["serieDocumento"]}-{data["comprobante"]["numeroDocumento"]}.xml'
filePath = dxmlFromString(data)
pfx_path = "certificado.pfx"  # Replace with your .pfx file path
pfx_password = b'Jose_d@vid2004'  # Replace with your .pfx password

with open(pfx_path, "rb") as pfx_file:
    pfx_data = pfx_file.read()

# Extract the certificate and private key
private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(pfx_data, pfx_password)


def modify_xml(file_path):
    # Read the XML file into a string
    with open(file_path, 'rb') as file:
        xml_string = file.read()


    # Parse the XML string using lxml.etree
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return

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
    ref.set('URI', "")
    xmlsec.template.add_transform(ref, xmlsec.Transform.ENVELOPED)

    # Add KeyInfo and X509Data
    key_info = xmlsec.template.ensure_key_info(signature_node)
    x509_data = xmlsec.template.add_x509_data(key_info)
    
    # Add X509Certificate within X509Data
    x509_certificate = ET.SubElement(x509_data, '{http://www.w3.org/2000/09/xmldsig#}X509Certificate')
    x509_certificate.text = base64.b64encode(certificate.public_bytes(serialization.Encoding.DER)).decode('ascii')

    # Append the signature to the specified element
    doc_element = root.findall('.//{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}ExtensionContent')[0]
    doc_element.append(signature_node)

    # Sign the document
    sign_ctx = xmlsec.SignatureContext(ctx)
    sign_ctx.key = key
    sign_ctx.sign(signature_node)

    # Set the ID attribute for the Signature element
    signature_node.set('Id', 'SignatureSP')

    # Save the signed XML document back to the file
    with open(file_path, 'wb') as file:
        file.write(ET.tostring(root, pretty_print=True))


modify_xml(filePath)


def zip_and_encode_base64(xml_file_path: str):
    nombrexml = xml_file_path.split('/')[1]  # Extract the XML file name from the path
    carpetaxml = 'xml/'  # Path to the directory containing the XML file
    rutaxml = os.path.join(carpetaxml, nombrexml)
    nombrezip = nombrexml.replace('.xml', '.zip')
    rutazip = os.path.join(carpetaxml, nombrezip)

    # Step 03: Zip the XML file
    with zipfile.ZipFile(rutazip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(rutaxml, arcname=nombrexml)

    # Step 04: Prepare the message to send to SUNAT (Envelope)
    with open(rutazip, 'rb') as f:
        contenido_del_zip = base64.b64encode(f.read()).decode('utf-8')

    return contenido_del_zip

encoded_zip = zip_and_encode_base64(filePath)

xml_envio =f'''<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
        xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ser="http://service.sunat.gob.pe" 
        xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
     <soapenv:Header>
            <wsse:Security>
                <wsse:UsernameToken>
                    <wsse:Username>{data["emisor"]["DocumentoEmisor"]}MCCULEIN</wsse:Username>
	<wsse:Password>ovenneclu</wsse:Password>
                </wsse:UsernameToken>
           </wsse:Security>
 </soapenv:Header>
 <soapenv:Body>
	<ser:sendBill>
		<fileName>{filePath.replace(".xml", ".ZIP").split('/')[1]}</fileName>
		<contentFile>{encoded_zip}</contentFile>
	</ser:sendBill>
 </soapenv:Body>
</soapenv:Envelope>'''

# The web service URL
ws = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService"

# Headers
headers = {
    "Content-Type": "text/xml; charset=utf-8",
    "Accept": "text/xml",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "SOAPAction": "",
    "Content-Length": str(len(xml_envio))

}

zip_data = base64.b64decode(encoded_zip)

with open("decoded_file.zip", "wb") as file:
    file.write(zip_data)

# SSL verification (use your .pfk file here)
cert_path = "certificado.pfx"  # Replace with your .pfk file path

# Check if the certificate file exists
if not os.path.isfile(cert_path):
    raise FileNotFoundError(f"Certificate file not found: {cert_path}")

# Path to the CA bundle
ca_bundle_path = "cacert.pem"  # Replace with the path to your cacert.pem file



# Send the request
response = requests.post(url=ws, data=xml_envio, headers=headers, verify=ca_bundle_path)



# Check HTTP status code
if response.status_code == 200:
    # Parse the XML response
    try:
        # Convert response text to bytes
        xml_bytes = response.content
        
        # Save the XML response to a file
        with open('response.xml', 'wb') as xml_file:
            xml_file.write(xml_bytes)
        
        # Parse the XML bytes using lxml.etree
        root = ET.fromstring(xml_bytes)
        print(root)
        print('correct')
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
else:
    print(f"HTTP request failed with status code {response.status_code}")