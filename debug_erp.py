import pkgutil
import erpbrasil
import sys

print(f"Python Version: {sys.version}")
print(f"ERPBrasil path: {erpbrasil.__path__}")

print("\n--- Listando submódulos de erpbrasil ---")
for loader, module_name, is_pkg in pkgutil.walk_packages(erpbrasil.__path__, erpbrasil.__name__ + "."):
    print(f"Module: {module_name} (Package: {is_pkg})")

print("\n--- Tentativa de importação direta ---")
try:
    import erpbrasil.base
    print("SUCCESS: import erpbrasil.base")
    try:
        from erpbrasil.base import certificado
        print("SUCCESS: from erpbrasil.base import certificado")
    except ImportError as e:
        print(f"FAILED: from erpbrasil.base import certificado -> {e}")
except ImportError as e:
    print(f"FAILED: import erpbrasil.base -> {e}")

try:
    from erpbrasil.base.certificado import Certificado
    print("SUCCESS: from erpbrasil.base.certificado import Certificado")
except ImportError as e:
    print(f"FAILED: from erpbrasil.base.certificado import Certificado -> {e}")
