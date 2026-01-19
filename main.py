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
    
    args = parser.parse_args()
    
    compiler = GomorraCompiler(data_dir=args.data_dir)
    
    try:
        # Controlla se è un file o una query diretta
        if Path(args.input).exists():
            print(f"Esecuzione file: {args.input}\n")
            results = compiler.run_file(args.input)
        else:
            print(f"Esecuzione query diretta\n")
            results = compiler.compile_and_run(args.input)
        
        # Stampa risultati
        print_results(results)
        
    except Exception as e:
        print(f"\n❌ ERRORE: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
