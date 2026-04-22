import importlib.util

libs_to_check = [
    "erpbrasil.base.certificado",
    "erpbrasil.base",
    "erpbrasil.edoc.nfe",
    "erpbrasil.edoc",
    "nfelib",
    "cryptography",
    "OpenSSL"
]

for lib in libs_to_check:
    spec = importlib.util.find_spec(lib)
    if spec is None:
        print(f"FAILED: {lib} not found")
    else:
        print(f"SUCCESS: {lib} found at {spec.origin}")

try:
    from erpbrasil.base.certificado import Certificado
    print("IMPORT SUCCESS: erpbrasil.base.certificado.Certificado")
except Exception as e:
    print(f"IMPORT ERROR erpbrasil.base.certificado: {str(e)}")

try:
    from erpbrasil.edoc.nfe import NFe
    print("IMPORT SUCCESS: erpbrasil.edoc.nfe.NFe")
except Exception as e:
    print(f"IMPORT ERROR erpbrasil.edoc.nfe: {str(e)}")
