import lxml.etree as ET
from datetime import date, datetime
import xml.dom.minidom as mini
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64
import xmlsec

def pretify(element, indent = '    '):
    queue = [(0, element)]
    while queue:
        level, element = queue.pop(0)
        children = [(level + 1, child) for child in list(element)]
        if children:
            element.text = '\n' + indent * (level+1)
        if queue:
            element.tail = '\n' + indent * queue[0][0]
        else:
            element.tail = '\n' + indent * (level-1)
        
        queue[0:0] = children

def generateXmlFactura(data, ruta_firma, pass_firma, filePath):
    
     # Extract variables from data dictionary
    tipoComprobante51 = data.get('tipoComprobante51')
    tipoComprobante01 = data.get('tipoComprobante01')
    numeroComprobante = data.get('numeroComprobante')
    CantidadTotalDeItems = data.get('CantidadTotalDeItems')
    taxes = data.get('taxes')
    emisor = data.get('emisor')
    adquiriente = data.get('adquiriente')
    Items = data.get('Items', {})
    

    invoice = ET.Element('Invoice')

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
    '' : "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
}
    #urls del Invoice 
    for key, value in namespaces.items():
        ET.register_namespace(str('xmlns' + key), value)
        print(2)

    #UBL extensions (Zona de Llaves)

    ext_UBLExtensions = ET.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}UBLExtensions')
    ext_UBLExtension = ET.SubElement(ext_UBLExtensions, '{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}UBLExtension')
    ExtensionContent = ET.SubElement(ext_UBLExtension, '{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}ExtensionContent')


     # Create ElementTree object
    et_object = ET.ElementTree(invoice)

    # Signing the XML document
    root = et_object.getroot()
    
    # Load the private key and certificate from the PFX file
    with open(ruta_firma, 'rb') as pfx_file:
        pfx_data = pfx_file.read()
    private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
        pfx_data, pass_firma.encode(), default_backend()
    )

    

    
    #Versiones
    ET.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}UBLVersionID').text = '2.1'
    ET.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CustomizationID').text = '2.0'

    #Datos del Comprobante de Pago
    cbc_ProfileID = ET.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ProfileID', {
        'schemeName': "SUNAT:Identificador de Tipo de Operación", 
        'schemeAgencyName': "PE:SUNAT", 
        'schemeURI': "urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo51"
    })
    cbc_ProfileID.text = tipoComprobante51

    ET.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID').text = numeroComprobante
    ET.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueDate').text = str(date.today())
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    sec = now.second
    now = f'{hour}:{minute}:{sec}'
    ET.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueTime').text = now

    cbc_InvoiceTypeCode = ET.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}InvoiceTypeCode', {
        'listAgencyName': "SUNAT:Identificador de Tipo de Documento",
        'listName': "SUNAT:Identificador de Tipo de Documento",
        'listURI': "urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01"
    })
    cbc_InvoiceTypeCode.text = tipoComprobante01

    cbc_DocumentCurrencyCode = ET.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}DocumentCurrencyCode', {
        'listID': "ISO 4217 Alpha",
        'listName': "Currency",
        'listAgencyName': "United Nations Economic Commission for Europe"
    })
    cbc_DocumentCurrencyCode.text = 'PEN'

    ET.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}LineCountNumeric').text = CantidadTotalDeItems

    #Signature
    cac_Signature = ET.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Signature')
    ET.SubElement(cac_Signature, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID').text = numeroComprobante

    cac_SignatoryParty = ET.SubElement(cac_Signature, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}SignatoryParty')
    cac_PartyIdentification = ET.SubElement(cac_SignatoryParty, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyIdentification')
    ET.SubElement(cac_PartyIdentification, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID').text = emisor['DocumentoEmisor']

    cac_PartyName = ET.SubElement(cac_SignatoryParty, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyName')
    ET.SubElement(cac_PartyName, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name').text = f'<![CDATA[{emisor["NombreComercialEmisor"]}]]>'

    cac_DigitalSignatureAttachment = ET.SubElement(cac_Signature, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}DigitalSignatureAttachment')
    cac_ExternalReference = ET.SubElement(cac_DigitalSignatureAttachment, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}ExternalReference')
    ET.SubElement(cac_ExternalReference, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}URI').text = '#SignatureSP'


    #Datos Del Emisor
    cac_AccountingSupplierParty = ET.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingSupplierParty')
    cac_Party = ET.SubElement(cac_AccountingSupplierParty, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Party')

    cac_PartyIdentification = ET.SubElement(cac_Party, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyIdentification')
    ET.SubElement(cac_PartyIdentification, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID', {
        'schemeID': emisor['TipoDocumento'], 
        'schemeName': "Documento de Identidad", 
        'schemeAgencyName': "PE:SUNAT", 
        'schemeURI': "urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06"
    }).text = emisor['DocumentoEmisor']

    cac_PartyName = ET.SubElement(cac_Party, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyName')
    ET.SubElement(cac_PartyName, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name').text = f'<![CDATA[{emisor["NombreComercialEmisor"]}]]>'

    cac_PartyTaxScheme = ET.SubElement(cac_Party, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyTaxScheme')
    ET.SubElement(cac_PartyTaxScheme, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}RegistrationName').text =  f'<![CDATA[{emisor["RazonSocialEmisor"]}]]>'
    ET.SubElement(cac_PartyTaxScheme, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CompanyID', {
        'schemeID': emisor['TipoDocumento'],
        'schemeName': "SUNAT:Identificador de Documento de Identidad",
        'schemeAgencyName': "PE:SUNAT",
        'schemeURI': "urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06"
    }).text = emisor['DocumentoEmisor']

    cac_TaxScheme = ET.SubElement(cac_PartyTaxScheme, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxScheme')
    ET.SubElement(cac_TaxScheme, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID', {
        'schemeID': emisor['TipoDocumento'],
        'schemeName': "SUNAT:Identificador de Documento de Identidad",
        'schemeAgencyName': "PE:SUNAT",
        'schemeURI': "urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06"
    }).text = emisor['DocumentoEmisor']

    cac_PartyLegalEntity = ET.SubElement(cac_Party, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyLegalEntity')
    ET.SubElement(cac_PartyLegalEntity, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}RegistrationName').text = 'RazonSocialEmisor'

    cac_RegistrationAddress = ET.SubElement(cac_PartyLegalEntity, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}RegistrationAddress')
    ET.SubElement(cac_RegistrationAddress, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID', {
        'schemeName': 'Ubigeos',
        'schemeAgencyName': 'PE:INEI'
    }).text = 'ubigeoDeDistrito'
    ET.SubElement(cac_RegistrationAddress, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}AddressTypeCode', {
        'listAgencyName': 'PE:SUNAT',
        'listName': 'Establecimientos anexos'
    }).text = '0000'
    ET.SubElement(cac_RegistrationAddress, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CityName').text = f'<![CDATA[{emisor["provincia"]}]]>'
    ET.SubElement(cac_RegistrationAddress, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CountrySubentity').text = f'<![CDATA[{emisor["departamento"]}]]>'
    ET.SubElement(cac_RegistrationAddress, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}District').text = f'<![CDATA[{emisor["distrito"]}]]>'

    cac_AddressLine = ET.SubElement(cac_RegistrationAddress, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AddressLine')
    ET.SubElement(cac_AddressLine, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Line').text = f'<![CDATA[{emisor["calle"]} - {emisor["distrito"]} - {emisor["provincia"]} - {emisor["departamento"]}]]>'

    cac_Country = ET.SubElement(cac_RegistrationAddress, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Country')
    ET.SubElement(cac_Country, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IdentificationCode', {
        'listID': 'ISO 3166-1',
        'listAgencyName': 'United Nations Economic Commission for Europe',
        'listName': 'Country'
    }).text = 'PE'

    # Datos Consumidor
    cac_AccountingCustomerParty = ET.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingCustomerParty')
    cac_Party_Customer = ET.SubElement(cac_AccountingCustomerParty, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Party')

    cac_PartyIdentification_Customer = ET.SubElement(cac_Party_Customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyIdentification')
    ET.SubElement(cac_PartyIdentification_Customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID', {
        'schemeID': adquiriente['TipoDocumentoAdquiriente'], 
        'schemeName': "Documento de Identidad", 
        'schemeAgencyName': "PE:SUNAT", 
        'schemeURI': "urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06"
    }).text = adquiriente['NumeroDocumentoAdquiriente']

    cac_PartyName_Customer = ET.SubElement(cac_Party_Customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyName')
    ET.SubElement(cac_PartyName_Customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name').text = 'NombreComercialComprador'

    cac_PartyTaxScheme_Customer = ET.SubElement(cac_Party_Customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyTaxScheme')
    ET.SubElement(cac_PartyTaxScheme_Customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}RegistrationName').text = 'RazonSocialComprador'
    ET.SubElement(cac_PartyTaxScheme_Customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CompanyID', {
        'schemeID': adquiriente['TipoDocumentoAdquiriente'],
        'schemeName': "SUNAT:Identificador de Documento de Identidad",
        'schemeAgencyName': "PE:SUNAT",
        'schemeURI': "urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06"
    }).text = adquiriente['NumeroDocumentoAdquiriente']

    cac_TaxScheme_Customer = ET.SubElement(cac_PartyTaxScheme_Customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxScheme')
    ET.SubElement(cac_TaxScheme_Customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID', {
        'schemeID': adquiriente['TipoDocumentoAdquiriente'],
        'schemeName': "SUNAT:Identificador de Documento de Identidad",
        'schemeAgencyName': "PE:SUNAT",
        'schemeURI': "urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06"
    }).text = adquiriente['NumeroDocumentoAdquiriente']

    cac_PartyLegalEntity_Customer = ET.SubElement(cac_Party_Customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyLegalEntity')
    ET.SubElement(cac_PartyLegalEntity_Customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}RegistrationName').text = 'RazonSocialComprador'

    cac_RegistrationAddress_Customer = ET.SubElement(cac_PartyLegalEntity_Customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}RegistrationAddress')
    ET.SubElement(cac_RegistrationAddress_Customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID', {
        'schemeName': 'Ubigeos',
        'schemeAgencyName': 'PE:INEI'
    })
    ET.SubElement(cac_RegistrationAddress_Customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CityName').text = '<![CDATA[]]>'
    ET.SubElement(cac_RegistrationAddress_Customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CountrySubentity').text = '<![CDATA[]]>'
    ET.SubElement(cac_RegistrationAddress_Customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}District').text = '<![CDATA[]]>'

    cac_AddressLine_Customer = ET.SubElement(cac_RegistrationAddress_Customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AddressLine')
    ET.SubElement(cac_AddressLine_Customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Line').text = f"<![CDATA[{adquiriente['CalleComprador']} - {adquiriente['distritoComprador']} - {adquiriente['provinciaComprador']} - {adquiriente['departamentoComprador']}]]>"

    cac_Country_Customer = ET.SubElement(cac_RegistrationAddress_Customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Country')
    ET.SubElement(cac_Country_Customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IdentificationCode', {
        'listID': 'ISO 3166-1',
        'listAgencyName': 'United Nations Economic Commission for Europe',
        'listName': 'Country'
    })

    # TaxTotal
    cac_TaxTotal = ET.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxTotal')
    ET.SubElement(cac_TaxTotal, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxAmount', {'currencyID': 'PEN'}).text = data['MontoTotalImpuestos']
    for tax in taxes.values():
        cac_TaxSubtotal = ET.SubElement(cac_TaxTotal, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxSubtotal')
        ET.SubElement(cac_TaxSubtotal, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxAmount', {'currencyID': 'PEN'}).text = tax['MontoTotalImpuesto']

        cac_TaxCategory = ET.SubElement(cac_TaxSubtotal, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxCategory')
        cac_TaxScheme_Subtotal = ET.SubElement(cac_TaxCategory, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxScheme')
        ET.SubElement(cac_TaxScheme_Subtotal, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID').text = tax['cod1'] #1000
        ET.SubElement(cac_TaxScheme_Subtotal, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name').text = tax['cod2'] #IGV
        ET.SubElement(cac_TaxScheme_Subtotal, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxTypeCode').text = tax['cod3'] #VAT

    # LegalMonetaryTotal
    cac_LegalMonetaryTotal = ET.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}LegalMonetaryTotal')
    ET.SubElement(cac_LegalMonetaryTotal, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PayableAmount', {'currencyID': 'PEN'}).text = data['ImporteTotalVenta']

    # InvoiceLine
    for item in Items:
        cac_InvoiceLine = ET.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}InvoiceLine')
        ET.SubElement(cac_InvoiceLine, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID').text = item['id']
        ET.SubElement(cac_InvoiceLine, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}InvoicedQuantity', {'unitCode': 'NIU'}).text = item['CantidadUnidadesItem']
        ET.SubElement(cac_InvoiceLine, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}LineExtensionAmount', {'currencyID': 'PEN'}).text = item['ValorVentaItem']

        # PricingReference
        cac_PricingReference = ET.SubElement(cac_InvoiceLine, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PricingReference')
        cac_AlternativeConditionPrice = ET.SubElement(cac_PricingReference, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AlternativeConditionPrice')
        ET.SubElement(cac_AlternativeConditionPrice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PriceAmount', {'currencyID': 'PEN'}).text = item['PrecioVentaUnitario']

        cbc_PriceTypeCode = ET.SubElement(cac_AlternativeConditionPrice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PriceTypeCode', {
            'listName': "SUNAT:Indicador de Tipo de Precio", 
            'listAgencyName': "PE:SUNAT", 
            'listURI': "urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo16"
        })
        cbc_PriceTypeCode.text = '01'

        # TaxTotal for InvoiceLine
        cac_TaxTotal_Line = ET.SubElement(cac_InvoiceLine, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxTotal')
        ET.SubElement(cac_TaxTotal_Line, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxAmount', {'currencyID': 'PEN'}).text = item['MontoTotalImpuestoItem']
        for tax in item['tax']:
            cac_TaxSubtotal_Line = ET.SubElement(cac_TaxTotal_Line, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxSubtotal')
            ET.SubElement(cac_TaxSubtotal_Line, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxAmount', {'currencyID': 'PEN'}).text = tax['MontoImpuestoItem']

            cac_TaxCategory_Line = ET.SubElement(cac_TaxSubtotal_Line, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxCategory')
            ET.SubElement(cac_TaxCategory_Line, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Percent').text = tax['PorcentajeImpuestoItem']

            cac_TaxScheme_Line = ET.SubElement(cac_TaxCategory_Line, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxScheme')
            ET.SubElement(cac_TaxScheme_Line, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID').text = tax['cod1'] #1000
            ET.SubElement(cac_TaxScheme_Line, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name').text = tax['cod2'] #IGV
            ET.SubElement(cac_TaxScheme_Line, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxTypeCode').text = tax['cod3'] #VAT

        # Item
        cac_Item = ET.SubElement(cac_InvoiceLine, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Item')
        ET.SubElement(cac_Item, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Description').text = F'<![CDATA[{item["DescripcionItem"]}]]>'
        ET.SubElement(cac_Item, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name').text = item['NombreItem']

        # Price
        cac_Price = ET.SubElement(cac_InvoiceLine, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Price')
        ET.SubElement(cac_Price, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PriceAmount', {'currencyID': 'PEN'}).text = item['PrecioVentaUnitario']



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

    

    tree = ET.ElementTree(invoice)
    
    tree.write( filePath, encoding='UTF-8', xml_declaration=True)

    # Convert to string for output
    xml_string = ET.tostring(invoice, encoding='utf-8', xml_declaration=True).decode()

    return filePath
