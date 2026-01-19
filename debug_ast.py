#!/usr/bin/env python3
"""
Debug: Stampa AST di una query
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser import GomorraParser

query = '''
RIPIGLIAMMO nome, zona
MMIEZ 'A "guaglioni.csv"
arò (eta > 18 e zona = "Scampia") o nome = "Ciro"
'''

parser = GomorraParser()
ast = parser.parse(query)

if ast:
    print("AST:")
    print(ast)
    print("\nWHERE condition:")
    print(ast.where)
    print(f"\nType: {type(ast.where)}")
    
    if hasattr(ast.where, 'conditions'):
        print(f"\nConditions: {len(ast.where.conditions)}")
        for i, cond in enumerate(ast.where.conditions):
            print(f"  [{i}] {type(cond).__name__}: {cond}")
