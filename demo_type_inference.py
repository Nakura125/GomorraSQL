#!/usr/bin/env python3
"""
Demo: Type Inference CSV→IR
Dimostra il sistema automatico di inferenza tipi per generazione LLVM IR
"""

import sys
import csv
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.compiler import GomorraCompiler


def print_section(title):
    """Helper per stampare sezioni"""
    print("\n" + "="*70)
    print(title)
    print("="*70)


def demo_integer_inference():
    """Demo: Inferenza automatica tipi integer"""
    print_section("DEMO 1: Type Inference per Colonne INTEGER")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Crea CSV con interi
        csv_path = Path(tmpdir) / "integers.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'eta', 'punteggio'])
            writer.writerow([1, 25, 100])
            writer.writerow([2, 30, 95])
            writer.writerow([3, 22, 88])
            writer.writerow([4, 28, 92])
        
        print(f"\n📄 CSV creato: integers.csv")
        print("   Colonne: id, eta, punteggio")
        print("   Valori: tutti interi (senza punti decimali)")
        
        compiler = GomorraCompiler(data_dir=tmpdir)
        query = '''
        RIPIGLIAMMO id, eta, punteggio
        MMIEZ 'A "integers.csv"
        arò eta > 25
        '''
        
        print(f"\n🔍 Query:")
        print(query)
        
        results = compiler.compile_and_run(query)
        
        print(f"\n🧠 Type Inference Automatico:")
        for col, typ in compiler.codegen.column_types.items():
            print(f"   • {col}: {typ.__name__}")
        
        print(f"\n📊 LLVM IR Generato (estratto):")
        ir_lines = str(compiler.codegen.module).split('\n')
        for line in ir_lines:
            if 'icmp' in line or 'i32' in line:
                print(f"   {line.strip()}")
        
        print(f"\n✓ Risultati: {len(results)} righe")
        for row in results:
            print(f"   ID={row['id']}, Età={row['eta']}, Punteggio={row['punteggio']}")


def demo_float_inference():
    """Demo: Inferenza automatica tipi float"""
    print_section("DEMO 2: Type Inference per Colonne FLOAT")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Crea CSV con float
        csv_path = Path(tmpdir) / "floats.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['prodotto_id', 'prezzo', 'rating'])
            writer.writerow([101, '19.99', '4.5'])
            writer.writerow([102, '29.99', '4.8'])
            writer.writerow([103, '9.99', '3.2'])
            writer.writerow([104, '39.99', '4.9'])
        
        print(f"\n📄 CSV creato: floats.csv")
        print("   Colonne: prodotto_id (int), prezzo (float), rating (float)")
        print("   Valori: numeri con punto decimale")
        
        compiler = GomorraCompiler(data_dir=tmpdir)
        query = '''
        RIPIGLIAMMO prodotto_id, prezzo, rating
        MMIEZ 'A "floats.csv"
        arò rating > 4
        '''
        
        print(f"\n🔍 Query:")
        print(query)
        
        results = compiler.compile_and_run(query)
        
        print(f"\n🧠 Type Inference Automatico:")
        for col, typ in compiler.codegen.column_types.items():
            print(f"   • {col}: {typ.__name__}")
        
        print(f"\n📊 LLVM IR Generato (estratto):")
        ir_lines = str(compiler.codegen.module).split('\n')
        for line in ir_lines:
            if 'fcmp' in line or 'double' in line:
                print(f"   {line.strip()}")
        
        print(f"\n✓ Risultati: {len(results)} righe")
        for row in results:
            print(f"   ID={row['prodotto_id']}, Prezzo={row['prezzo']}€, Rating={row['rating']}⭐")


def demo_mixed_types():
    """Demo: Inferenza con tipi misti"""
    print_section("DEMO 3: Type Inference MISTO (int + float + string)")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Crea CSV con tipi misti
        csv_path = Path(tmpdir) / "mixed.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'nome', 'stipendio', 'bonus'])
            writer.writerow([1, 'Alice', '50000', '5000.50'])
            writer.writerow([2, 'Bob', '60000', '6500.75'])
            writer.writerow([3, 'Charlie', '55000', '5250.25'])
            writer.writerow([4, 'Diana', '48000', '4800.00'])
        
        print(f"\n📄 CSV creato: mixed.csv")
        print("   Colonne:")
        print("     • id: integer")
        print("     • nome: string")
        print("     • stipendio: integer")
        print("     • bonus: float")
        
        compiler = GomorraCompiler(data_dir=tmpdir)
        query = '''
        RIPIGLIAMMO nome, stipendio, bonus
        MMIEZ 'A "mixed.csv"
        arò stipendio > 49000
        '''
        
        print(f"\n🔍 Query:")
        print(query)
        
        results = compiler.compile_and_run(query)
        
        print(f"\n🧠 Type Inference Automatico:")
        type_map = {int: "🔢 int (i32)", float: "🔢 float (double)", str: "📝 string (i8*)"}
        for col, typ in compiler.codegen.column_types.items():
            symbol = type_map.get(typ, f"{typ.__name__}")
            print(f"   • {col:15} → {symbol}")
        
        print(f"\n✓ Risultati: {len(results)} righe")
        for row in results:
            print(f"   {row['nome']:10} | Stipendio: {row['stipendio']:6}€ | Bonus: {row['bonus']}€")


def demo_null_handling():
    """Demo: Gestione NULL nell'inferenza"""
    print_section("DEMO 4: Type Inference con Valori NULL")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Crea CSV con NULL
        csv_path = Path(tmpdir) / "with_nulls.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'nome', 'voto'])
            writer.writerow([1, 'Test1', '95'])
            writer.writerow([2, '', ''])      # NULL values
            writer.writerow([3, 'Test3', '88'])
            writer.writerow([4, 'Test4', ''])  # NULL in voto
            writer.writerow([5, 'Test5', '92'])
        
        print(f"\n📄 CSV creato: with_nulls.csv")
        print("   Alcune righe hanno valori NULL (vuoti)")
        
        compiler = GomorraCompiler(data_dir=tmpdir)
        query = '''
        RIPIGLIAMMO id, nome, voto
        MMIEZ 'A "with_nulls.csv"
        arò nome nun è nisciun
        '''
        
        print(f"\n🔍 Query (filtra righe con nome NON NULL):")
        print(query)
        
        results = compiler.compile_and_run(query)
        
        print(f"\n🧠 Type Inference (ignora NULL, usa valori non-NULL):")
        for col, typ in compiler.codegen.column_types.items():
            print(f"   • {col}: {typ.__name__}")
        
        print(f"\n✓ Risultati: {len(results)} righe (solo con nome valido)")
        for row in results:
            voto = row['voto'] if row['voto'] else 'N/A'
            print(f"   ID={row['id']}, Nome={row['nome']}, Voto={voto}")


def demo_comparison():
    """Demo: Confronto prima/dopo type inference"""
    print_section("DEMO 5: Confronto PRIMA vs DOPO Type Inference")
    
    print("\n❌ PRIMA (senza type inference):")
    print("   • Tutti i valori hardcoded come i32")
    print("   • Impossibile gestire float correttamente")
    print("   • Stringhe ignorate")
    print("   • Possibili segmentation fault con dati reali")
    print("\n   Esempio IR:")
    print("   %result = icmp sgt i32 35, 18  ; Sempre i32!")
    
    print("\n✅ DOPO (con type inference):")
    print("   • Analisi automatica dei CSV (primi 100 valori)")
    print("   • Tipi inferiti: int → i32, float → double, string → i8*")
    print("   • IR generato con tipo corretto per ogni colonna")
    print("   • Comparazioni appropriate:")
    print("     - icmp per interi (i32)")
    print("     - fcmp per float (double)")
    print("     - strcmp per stringhe (i8*)")
    
    print("\n🎯 Vantaggi:")
    print("   ✓ Nessun hardcoding")
    print("   ✓ Type safety a compile-time")
    print("   ✓ Evita segmentation fault")
    print("   ✓ Performance ottimali (tipo giusto = istruzioni giuste)")


def main():
    """Entry point"""
    print("\n" + "="*70)
    print("🚀 GomorraSQL - Demo Type Inference CSV→IR")
    print("="*70)
    print("\nFeedback Requirement #1:")
    print("  'Mapping tipi CSV→IR coerente'")
    print("\nImplementazione:")
    print("  ✓ _infer_column_type(): Analizza valori CSV")
    print("  ✓ _analyze_csv_types(): Campiona 100 righe per inferire tipi")
    print("  ✓ visit_comparison(): Genera IR con tipo corretto")
    print("  ✓ Supporto: int (i32), float (double), string (i8*), NULL")
    
    try:
        demo_integer_inference()
        demo_float_inference()
        demo_mixed_types()
        demo_null_handling()
        demo_comparison()
        
        print("\n" + "="*70)
        print("✅ TUTTE LE DEMO COMPLETATE CON SUCCESSO")
        print("="*70)
        print("\n📊 Riepilogo:")
        print("   • Integer: Usa icmp + i32 ✓")
        print("   • Float: Usa fcmp + double ✓")
        print("   • String: Gestito (placeholder) ✓")
        print("   • NULL: Rilevato e ignorato nell'inferenza ✓")
        print("   • Tipi misti: Analisi indipendente per colonna ✓")
        
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
