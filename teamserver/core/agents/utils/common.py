import importlib.util
import zipfile
import ast
import sys
import os

def find_library_path(lib_name):
    spec = importlib.util.find_spec(lib_name)
    if spec is None:
        raise ImportError(f"Module {lib_name} not found")
    
    lib_path = spec.submodule_search_locations[0] if spec.submodule_search_locations else spec.origin
    return lib_path

path = find_library_path("PIL")

def zip_modules(modules, output_zip):
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for module in modules:
            if os.path.isfile(module) and module.endswith('.py'):
                arcname = os.path.basename(module)
                zipf.write(module, arcname)
            elif os.path.isdir(module):
                for root, dirs, files in os.walk(module):
                    for file in files:
                        # if file.endswith('.pyd'):
                        #     continue 
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, start=os.path.dirname(module))
                        zipf.write(file_path, arcname)

def unzip_library(zip_path, extract_to):
    os.makedirs(extract_to, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        zipf.extractall(extract_to)

def find_non_builtin_imports(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=file_path)

    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])

    non_builtin = []
    for module in imports:
        if module in sys.builtin_module_names:
            continue
        spec = importlib.util.find_spec(module)
        if spec is None:
            continue
        if spec.origin is None or spec.origin == 'built-in':
            continue
        non_builtin.append(module)

    return non_builtin
