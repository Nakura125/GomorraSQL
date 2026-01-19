"""
Test per verificare la scalabilità con generatori
"""
import pytest
import sys
from pathlib import Path
import csv
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.compiler import GomorraCompiler


def test_generator_scalability():
    """
    Test scalabilità con file CSV grandi usando generatori
    Verifica che i generatori funzionino correttamente
    """
    # Crea directory temporanea
    with tempfile.TemporaryDirectory() as tmpdir:
        # Crea file CSV grande (100 righe)
        large_csv = Path(tmpdir) / "large_table.csv"
        with open(large_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'nome', 'valore'])
            for i in range(100):
                writer.writerow([i, f'Nome_{i}', i * 10])
        
        # Crea secondo file per JOIN (50 righe)
        second_csv = Path(tmpdir) / "second_table.csv"
        with open(second_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'categoria'])
            for i in range(50):
                writer.writerow([i, f'Cat_{i % 5}'])
        
        # Test SELECT semplice con generatori
        compiler = GomorraCompiler(data_dir=tmpdir)
        query = '''
        RIPIGLIAMMO id, nome, valore
        MMIEZ 'A "large_table.csv"
        arò valore > 500
        '''
        results = compiler.compile_and_run(query)
        
        # 51 righe hanno valore > 500 (da 51*10 a 99*10)
        assert len(results) == 49
        assert results[0]['valore'] == '510'
        
        # Test JOIN con generatori (100 × 50 = 5000 righe totali)
        query_join = '''
        RIPIGLIAMMO nome, categoria
        MMIEZ 'A "large_table.csv"
        pesc e pesc "second_table.csv"
        '''
        results_join = compiler.compile_and_run(query_join)
        
        # Prodotto cartesiano: 100 × 50 = 5000
        assert len(results_join) == 5000
        assert 'nome' in results_join[0]
        assert 'categoria' in results_join[0]


def test_generator_memory_efficiency():
    """
    Test che verifica che i generatori non carichino tutto in memoria
    contemporaneamente durante il processing
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Crea piccolo CSV
        test_csv = Path(tmpdir) / "test.csv"
        with open(test_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'nome'])
            for i in range(10):
                writer.writerow([i, f'Test_{i}'])
        
        compiler = GomorraCompiler(data_dir=tmpdir)
        
        # Verifica che il generatore _csv_generator funzioni
        gen = compiler.codegen._csv_generator(test_csv)
        
        # Il generatore non deve materializzare i dati
        assert hasattr(gen, '__iter__')
        assert hasattr(gen, '__next__')
        
        # Leggi prima riga
        first_row = next(gen)
        assert first_row['id'] == '0'
        assert first_row['nome'] == 'Test_0'
        
        # Leggi seconda riga
        second_row = next(gen)
        assert second_row['id'] == '1'


def test_generator_column_headers():
    """
    Test che _get_csv_columns legga solo l'header senza caricare dati
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        test_csv = Path(tmpdir) / "headers_test.csv"
        with open(test_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['col1', 'col2', 'col3'])
            # Aggiungi molte righe per verificare che non vengano caricate
            for i in range(1000):
                writer.writerow([i, i*2, i*3])
        
        compiler = GomorraCompiler(data_dir=tmpdir)
        
        # Leggi solo headers
        columns = compiler.codegen._get_csv_columns(test_csv)
        
        assert columns == ['col1', 'col2', 'col3']
        # Verifica che self.data sia ancora vuoto (non ha caricato le 1000 righe)
        assert len(compiler.codegen.data) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
