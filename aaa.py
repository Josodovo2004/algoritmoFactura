import xml.etree.ElementTree as ET
from generate import generateXmlFactura

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
    "Factura" : "01",
    "Boleta" : "03",
}

generateXmlFactura('1010', '01', 'F001-00000001', '3', [1,1,1], '20605138293', '20605138293', '6', 'Empresa a', 'Empresa a', '6', {'item1': 1,'item3': 1,'item2': 1})

