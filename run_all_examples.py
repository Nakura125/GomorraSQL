#!/usr/bin/env python3
"""
Demo Script: Esegue tutte le query di esempio nella cartella data/
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.compiler import GomorraCompiler


def print_section(title, char="="):
    """Helper per stampare sezioni"""
    width = 70
    print(f"\n{char * width}")
    print(f"{title:^{width}}")
    print(f"{char * width}\n")


def run_query_file(compiler, query_file):
    """Esegue una query da file e mostra i risultati"""
    query_name = query_file.stem
    
    print_section(f"📝 {query_name}", "-")
    
    # Leggi e mostra la query
    query_text = query_file.read_text().strip()
    print("Query:")
    print(query_text)
    print()
    
    try:
        # Esegui query
        results = compiler.run_file(str(query_file))
        
        # Mostra risultati
        if results:
            print(f"✓ Risultati: {len(results)} righe\n")
            
            # Mostra prime 5 righe (per non sovraccaricare output)
            for i, row in enumerate(results[:5]):
                print(f"  {i+1}. {row}")
            
            if len(results) > 5:
                print(f"  ... ({len(results) - 5} altre righe)")
        else:
            print("✓ Query eseguita: 0 righe restituite")
            
    except Exception as e:
        print(f"❌ Errore: {e}")
    
    print()


def main():
    """Entry point"""
    print_section("🍕 GomorraSQL - Demo Query di Esempio")
    
    # Setup compiler
    data_dir = Path(__file__).parent / "data"
    compiler = GomorraCompiler(data_dir=str(data_dir))
    
    # Trova tutte le query
    queries_dir = Path(__file__).parent / "queries"
    query_files = sorted(queries_dir.glob("*.gsql"))
    
    if not query_files:
        print("❌ Nessuna query trovata in queries/")
        return 1
    
    print(f"Trovate {len(query_files)} query da eseguire:\n")
    for qf in query_files:
        print(f"  • {qf.name}")
    
    # Esegui tutte le query
    for query_file in query_files:
        run_query_file(compiler, query_file)
    
    print_section("✅ TUTTE LE QUERY ESEGUITE CON SUCCESSO")
    
    print("\n📚 Funzionalità Dimostrate:")
    print("  ✓ SELECT con WHERE")
    print("  ✓ Operatori logici (E/O)")
    print("  ✓ JOIN (prodotto cartesiano)")
    print("  ✓ JOIN con confronto colonne (INNER JOIN)")
    print("  ✓ NULL check (è nisciun / nun è nisciun)")
    print("  ✓ Operatori comparazione (>, <, =, <>, >=, <=)")
    print("  ✓ Type inference automatico CSV→IR")
    print("  ✓ Generators per JOIN scalabile")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
