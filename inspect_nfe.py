import nfelib.v4_00.leiauteNFe as nfe

print("--- Pesquisando a Classe Raiz da NFe ---")
attrs = dir(nfe)

# Procura classes que comecem com NFe ou TNFe (corrigido o typo 'a' -> 'attr')
roots = [attr for attr in attrs if (attr.startswith('NFe') or attr.startswith('TNFe'))]

for r_name in roots:
    cls = getattr(nfe, r_name)
    # Verifica se é uma classe e tem __init__
    if isinstance(cls, type):
        import inspect
        try:
            sig = inspect.signature(cls.__init__)
            if 'infNFe' in sig.parameters:
                print(f"ROOT CANDIDATE: {r_name} | Params: {sig}")
        except:
            pass

# Lista também classes que podem ser o root
print("\n--- Outras classes de interesse ---")
for r_name in ['TNFe', 'NFe', 'nfeProc', 'TnfeProc']:
    if r_name in attrs:
        print(f"Classe {r_name} existe no módulo.")
