#!/usr/bin/env python3
"""
GomorraSQL - Interfaccia CLI
Esegue query GomorraSQL da linea di comando
"""

import sys
from pathlib import Path

# Aggiungi src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.compiler import GomorraCompiler
import json


def print_results(results):
    """Stampa i risultati in formato tabellare"""
    if not results:
        print("Nessun risultato")
        return
    
    # Intestazioni
    headers = list(results[0].keys())
    print("\n" + " | ".join(headers))
    print("-" * (len(" | ".join(headers))))
    
    # Righe
    for row in results:
        print(" | ".join(str(row[h]) for h in headers))
    
    print(f"\n({len(results)} righe)")


def main():
    """Entry point CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GomorraSQL - Compilatore SQL Napoletano")
    parser.add_argument("input", help="Query o file .gsql da eseguire")
    parser.add_argument("--data-dir", default="data", help="Directory contenente i file CSV")
    parser.add_argument("--show-ir", action="store_true", help="Mostra LLVM IR generato")
    parser.add_argument("--no-optimize", action="store_true", help="Disabilita ottimizzazioni LLVM IR")
    
    args = parser.parse_args()
    
    # Ottimizzazioni abilitate di default, disabilitate solo con --no-optimize
    compiler = GomorraCompiler(data_dir=args.data_dir, optimize=not args.no_optimize)
    
    try:
        # Parse query per generare AST
        if Path(args.input).exists():
            print(f"📄 Esecuzione file: {args.input}")
            with open(args.input, 'r') as f:
                code = f.read()
        else:
            print(f"🔍 Esecuzione query diretta")
            code = args.input
        
        # Parse e analisi semantica
        ast = compiler.parser.parse(code)
        compiler.semantic_analyzer.analyze(ast)
        
        # Mostra LLVM IR se richiesto
        if args.show_ir:
            print("\n--- LLVM IR GENERATO ---")
            compilation = compiler.codegen.get_ir(ast)
            print(compilation.llvm_ir)
            
        
        # Esegui query
        results = compiler.codegen.generate_and_execute(ast)
        
        # Stampa risultati
        print_results(results)
        
    except SyntaxError as e:
        print(f"\n❌ ERRORE SINTATTICO: {e}")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ ERRORE: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
