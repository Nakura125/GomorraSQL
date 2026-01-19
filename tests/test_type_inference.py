"""
Test per verificare il type inference CSV→IR
"""
import pytest
import sys
from pathlib import Path
import csv
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.compiler import GomorraCompiler


def test_type_inference_integer():
    """Test type inference per colonne integer"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # CSV con solo interi
        csv_path = Path(tmpdir) / "integers.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'age', 'score'])
            writer.writerow([1, 25, 100])
            writer.writerow([2, 30, 95])
            writer.writerow([3, 22, 88])
        
        compiler = GomorraCompiler(data_dir=tmpdir)
        query = '''
        RIPIGLIAMMO id, age
        MMIEZ 'A "integers.csv"
        arò age > 24
        '''
        
        results = compiler.compile_and_run(query)
        
        # Verifica type inference
        assert compiler.codegen.column_types['id'] == int
        assert compiler.codegen.column_types['age'] == int
        assert compiler.codegen.column_types['score'] == int
        
        # Verifica risultati
        assert len(results) == 2
        assert results[0]['age'] == '25'


def test_type_inference_float():
    """Test type inference per colonne float"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # CSV con float
        csv_path = Path(tmpdir) / "floats.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'price', 'rating'])
            writer.writerow([1, '19.99', '4.5'])
            writer.writerow([2, '29.99', '4.8'])
            writer.writerow([3, '9.99', '3.2'])
        
        compiler = GomorraCompiler(data_dir=tmpdir)
        query = '''
        RIPIGLIAMMO id, price
        MMIEZ 'A "floats.csv"
        arò rating > 4
        '''
        
        results = compiler.compile_and_run(query)
        
        # Verifica type inference
        assert compiler.codegen.column_types['id'] == int
        assert compiler.codegen.column_types['price'] == float
        assert compiler.codegen.column_types['rating'] == float
        
        assert len(results) == 2


def test_type_inference_string():
    """Test type inference per colonne string"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # CSV con stringhe
        csv_path = Path(tmpdir) / "strings.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'city'])
            writer.writerow([1, 'Mario', 'Napoli'])
            writer.writerow([2, 'Luigi', 'Roma'])
            writer.writerow([3, 'Gino', 'Milano'])
        
        compiler = GomorraCompiler(data_dir=tmpdir)
        query = '''
        RIPIGLIAMMO id, name, city
        MMIEZ 'A "strings.csv"
        arò id > 0
        '''
        
        results = compiler.compile_and_run(query)
        
        # Verifica type inference
        assert compiler.codegen.column_types['id'] == int
        assert compiler.codegen.column_types['name'] == str
        assert compiler.codegen.column_types['city'] == str
        
        assert len(results) == 3


def test_type_inference_mixed():
    """Test type inference con tipi misti"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # CSV con tipi misti
        csv_path = Path(tmpdir) / "mixed.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'salary', 'bonus'])
            writer.writerow([1, 'Alice', '50000', '5000.50'])
            writer.writerow([2, 'Bob', '60000', '6500.75'])
            writer.writerow([3, 'Charlie', '55000', '5250.25'])
        
        compiler = GomorraCompiler(data_dir=tmpdir)
        query = '''
        RIPIGLIAMMO name, salary, bonus
        MMIEZ 'A "mixed.csv"
        arò id > 1
        '''
        
        results = compiler.compile_and_run(query)
        
        # Verifica type inference
        assert compiler.codegen.column_types['id'] == int
        assert compiler.codegen.column_types['name'] == str
        assert compiler.codegen.column_types['salary'] == int
        assert compiler.codegen.column_types['bonus'] == float
        
        assert len(results) == 2


def test_type_inference_null_values():
    """Test type inference con valori NULL"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # CSV con NULL
        csv_path = Path(tmpdir) / "nulls.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'score'])
            writer.writerow([1, 'Test1', '100'])
            writer.writerow([2, '', ''])  # NULL values
            writer.writerow([3, 'Test3', '90'])
        
        compiler = GomorraCompiler(data_dir=tmpdir)
        query = '''
        RIPIGLIAMMO id, name, score
        MMIEZ 'A "nulls.csv"
        arò name nun è nisciun
        '''
        
        results = compiler.compile_and_run(query)
        
        # Verifica type inference (ignora NULL, inferisce da valori non-NULL)
        assert compiler.codegen.column_types['id'] == int
        assert compiler.codegen.column_types['name'] == str
        assert compiler.codegen.column_types['score'] == int
        
        assert len(results) == 2


def test_llvm_ir_generation_with_types():
    """Test che LLVM IR venga generato con i tipi corretti"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # CSV per test
        csv_path = Path(tmpdir) / "test.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'value', 'rating'])
            writer.writerow([1, '100', '4.5'])
            writer.writerow([2, '200', '3.8'])
        
        compiler = GomorraCompiler(data_dir=tmpdir)
        
        # Test con integer comparison
        query_int = 'RIPIGLIAMMO id MMIEZ \'A "test.csv" arò id > 1'
        compiler.compile_and_run(query_int)
        ir_code = str(compiler.codegen.module)
        
        # Deve usare icmp (integer comparison)
        assert 'icmp' in ir_code
        assert 'i32' in ir_code  # tipo integer
        
        # Test con float comparison
        query_float = 'RIPIGLIAMMO id MMIEZ \'A "test.csv" arò rating > 4'
        compiler.compile_and_run(query_float)
        ir_code = str(compiler.codegen.module)
        
        # Deve usare fcmp (float comparison)
        assert 'fcmp' in ir_code
        assert 'double' in ir_code  # tipo float


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
