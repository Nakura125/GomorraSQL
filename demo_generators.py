#!/usr/bin/env python3
"""
Demo: Scalabilità con Generatori Python
Dimostra come i generatori permettano di gestire file CSV grandi
"""

import sys
import csv
import time
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.compiler import GomorraCompiler


def create_large_csv(path: Path, num_rows: int, name: str):
    """Crea un file CSV grande per testing"""
    print(f"📝 Creando {name} con {num_rows:,} righe...")
    start = time.time()
    
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'nome', 'valore', 'categoria'])
        for i in range(num_rows):
            writer.writerow([i, f'Utente_{i}', i * 100, f'Cat_{i % 10}'])
    
    elapsed = time.time() - start
    size_mb = path.stat().st_size / (1024 * 1024)
    print(f"✓ Creato in {elapsed:.2f}s - Dimensione: {size_mb:.2f} MB")
    return size_mb


def demo_simple_select():
    """Demo: SELECT con filtro su file grande"""
    print("\n" + "="*70)
    print("DEMO 1: SELECT con Generatori su File Grande")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Crea file da 10,000 righe (~1 MB)
        csv_path = Path(tmpdir) / "large.csv"
        size = create_large_csv(csv_path, 10000, "large.csv")
        
        # Esegui query
        compiler = GomorraCompiler(data_dir=tmpdir)
        query = '''
        RIPIGLIAMMO nome, valore
        MMIEZ 'A "large.csv"
        arò valore > 500000
        '''
        
        print("\n🔍 Query:")
        print(query)
        
        start = time.time()
        results = compiler.compile_and_run(query)
        elapsed = time.time() - start
        
        print(f"\n✓ Esecuzione completata in {elapsed:.3f}s")
        print(f"📊 Risultati: {len(results):,} righe su {10000:,} totali")
        print(f"\n   Prime 3 righe:")
        for i, row in enumerate(results[:3]):
            print(f"   {i+1}. {row}")


def demo_join_scalability():
    """Demo: JOIN su file grandi con prodotto cartesiano"""
    print("\n" + "="*70)
    print("DEMO 2: JOIN Scalabile con Generatori")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Crea due file: 1000 × 500 = 500,000 righe nel prodotto cartesiano
        table1 = Path(tmpdir) / "utenti.csv"
        table2 = Path(tmpdir) / "ordini.csv"
        
        size1 = create_large_csv(table1, 1000, "utenti.csv")
        
        print(f"\n📝 Creando ordini.csv con 500 righe...")
        start = time.time()
        with open(table2, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'prodotto', 'prezzo'])
            for i in range(500):
                writer.writerow([i, f'Prodotto_{i}', i * 10])
        elapsed = time.time() - start
        size2 = table2.stat().st_size / (1024 * 1024)
        print(f"✓ Creato in {elapsed:.2f}s - Dimensione: {size2:.2f} MB")
        
        # Esegui JOIN
        compiler = GomorraCompiler(data_dir=tmpdir)
        query = '''
        RIPIGLIAMMO nome, prodotto, prezzo
        MMIEZ 'A "utenti.csv"
        pesc e pesc "ordini.csv"
        arò prezzo > 4000
        '''
        
        print("\n🔍 Query JOIN con filtro:")
        print(query)
        
        print(f"\n⚙️  Calcolo prodotto cartesiano: 1,000 × 500 = 500,000 righe...")
        start = time.time()
        results = compiler.compile_and_run(query)
        elapsed = time.time() - start
        
        print(f"\n✓ JOIN completato in {elapsed:.3f}s")
        print(f"📊 Risultati dopo filtro: {len(results):,} righe")
        print(f"💾 Dimensione file originali: {size1 + size2:.2f} MB")
        print(f"\n   Prime 3 righe:")
        for i, row in enumerate(results[:3]):
            print(f"   {i+1}. nome={row['nome']}, prodotto={row['prodotto']}, prezzo={row['prezzo']}")


def demo_generator_vs_list():
    """Demo: Confronto generatori vs list() per memoria"""
    print("\n" + "="*70)
    print("DEMO 3: Efficienza Memoria - Generatori vs List")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test.csv"
        create_large_csv(csv_path, 5000, "test.csv")
        
        compiler = GomorraCompiler(data_dir=tmpdir)
        
        print("\n📊 Test generatore _csv_generator():")
        print("   ✓ Itera sui dati SENZA caricare tutto in memoria")
        print("   ✓ Usa yield per streaming on-demand")
        
        gen = compiler.codegen._csv_generator(csv_path)
        print(f"   Tipo: {type(gen).__name__}")
        
        # Leggi solo 5 righe
        print("\n   Prime 5 righe (senza caricare tutte le 5,000):")
        for i, row in enumerate(gen):
            if i >= 5:
                break
            print(f"   {i+1}. ID={row['id']}, Nome={row['nome']}")
        
        print("\n💡 Vantaggio: Il generatore carica una riga alla volta")
        print("   invece di tutte le 5,000 righe contemporaneamente!")


def main():
    """Entry point"""
    print("\n" + "="*70)
    print("🚀 GomorraSQL - Demo Scalabilità con Generatori Python")
    print("="*70)
    print("\nIl TODO #2 del feedback richiede:")
    print("  'Generatori Python per JOIN scalabile su grandi file'")
    print("\nImplementazione completata con:")
    print("  ✓ _csv_generator(): Legge CSV con yield")
    print("  ✓ _cartesian_product_generator(): JOIN lazy")
    print("  ✓ _get_csv_columns(): Solo header, no dati")
    
    try:
        demo_simple_select()
        demo_join_scalability()
        demo_generator_vs_list()
        
        print("\n" + "="*70)
        print("✅ TUTTE LE DEMO COMPLETATE CON SUCCESSO")
        print("="*70)
        print("\n📈 Metriche Finali:")
        print("   • SELECT su 10,000 righe: ✓")
        print("   • JOIN 1,000 × 500 = 500,000 righe: ✓")
        print("   • Generatori lazy: ✓")
        print("   • Memory-efficient: ✓")
        
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
