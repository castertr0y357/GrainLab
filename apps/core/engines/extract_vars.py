import ast
import os

res = []
engines_dir = 'e:/Coding Projects/GrainLab/apps/core/engines'

for f in os.listdir(engines_dir):
    if f.endswith('_engine.py') and f != 'base_engine.py':
        p = os.path.join(engines_dir, f)
        with open(p, encoding='utf-8') as file:
            c = file.read()
            n = ast.parse(c)
            for node in n.body:
                if isinstance(node, ast.ClassDef) and node.name.endswith('Engine'):
                    for stmt in node.body:
                        if isinstance(stmt, ast.Assign) and isinstance(stmt.targets[0], ast.Name) and stmt.targets[0].id == 'variations':
                            keys = [k.value for k in stmt.value.keys if isinstance(k, ast.Constant)]
                            res.append(f + ' variations: ' + ', '.join(keys))

print('\n'.join(res))
