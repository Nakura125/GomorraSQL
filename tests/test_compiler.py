"""
Test Suite per GomorraSQL con pytest
"""

import pytest
import sys
from pathlib import Path

# Aggiungi src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.compiler import GomorraCompiler
from src.semantic_analyzer import SemanticError


@pytest.fixture
def compiler():
    """Fixture che fornisce un'istanza del compiler"""
    return GomorraCompiler(data_dir="data")


def test_simple_select(compiler):
    """Test SELECT semplice"""
    query = '''
    RIPIGLIAMMO nome, eta 
    MMIEZ 'A "guaglioni.csv" 
    arò eta > 18
    '''
    
    results = compiler.compile_and_run(query)
    assert len(results) == 3
    assert 'nome' in results[0]
    assert 'eta' in results[0]


def test_select_with_complex_where(compiler):
    """Test SELECT con WHERE complesso (AND/OR)"""
    query = '''
    RIPIGLIAMMO nome, zona
    MMIEZ 'A "guaglioni.csv"
    arò (eta > 18 e zona = "Scampia") o nome = "Ciro"
    '''
    
    results = compiler.compile_and_run(query)
    assert len(results) == 2
    # Ciro (nome = "Ciro") e Genny (eta > 18 AND zona = "Scampia")
    names = [r['nome'] for r in results]
    assert 'Ciro' in names
    assert 'Genny' in names


def test_join_simple(compiler):
    """Test JOIN semplice (prodotto cartesiano)"""
    query = '''
    RIPIGLIAMMO nome, ruolo
    MMIEZ 'A "guaglioni.csv"
    pesc e pesc "ruoli.csv"
    '''
    
    results = compiler.compile_and_run(query)
    assert len(results) == 16  # 4 × 4 prodotto cartesiano
    assert 'nome' in results[0]
    assert 'ruolo' in results[0]


def test_join_with_where(compiler):
    """Test JOIN con filtro WHERE"""
    query = '''
    RIPIGLIAMMO nome, ruolo, eta
    MMIEZ 'A "guaglioni.csv"
    pesc e pesc "ruoli.csv"
    arò eta > 18
    '''
    
    results = compiler.compile_and_run(query)
    assert len(results) == 12  # Escluso O_Track (17 anni)
    # Verifica che O_Track non sia presente
    names = [r['nome'] for r in results]
    assert 'O_Track' not in names


def test_join_inner_simulated(compiler):
    """Test JOIN con confronto tra colonne (simula INNER JOIN)"""
    query = '''
    RIPIGLIAMMO nome, nome_2, ruolo
    MMIEZ 'A "guaglioni.csv"
    pesc e pesc "ruoli.csv"
    arò nome = nome_2
    '''
    
    results = compiler.compile_and_run(query)
    assert len(results) == 4  # Solo match perfetti
    # Verifica che nome == nome_2 per tutte le righe
    for row in results:
        assert row['nome'] == row['nome_2']


def test_semantic_error(compiler):
    """Test errore semantico (colonna inesistente)"""
    query = '''
    RIPIGLIAMMO colonna_inesistente
    MMIEZ 'A "guaglioni.csv"
    '''
    
    with pytest.raises(SemanticError):
        compiler.compile_and_run(query)


def test_syntax_error(compiler):
    """Test errore sintattico"""
    # Query con sintassi invalida (manca FROM)
    query = 'RIPIGLIAMMO nome arò eta > 18'
    
    result = compiler.parser.parse(query)
    assert result is None  # Parser ritorna None su errore sintattico


def test_run_file(compiler, tmp_path):
    """Test esecuzione query da file"""
    # Crea file temporaneo con query
    query_file = tmp_path / "test_query.gsql"
    query_file.write_text('''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    arò eta > 20
    ''')
    
    results = compiler.run_file(str(query_file))
    assert len(results) == 2
    assert 'nome' in results[0]


def test_comparison_operators(compiler):
    """Test operatori di confronto"""
    # Test >
    query1 = 'RIPIGLIAMMO nome MMIEZ \'A "guaglioni.csv" arò eta > 20'
    results1 = compiler.compile_and_run(query1)
    assert len(results1) == 2  # Ciro (35), SangueBlu (25)
    
    # Test <
    query2 = 'RIPIGLIAMMO nome MMIEZ \'A "guaglioni.csv" arò eta < 20'
    results2 = compiler.compile_and_run(query2)
    assert len(results2) == 2  # Genny (19), O_Track (17)
    
    # Test =
    query3 = 'RIPIGLIAMMO nome MMIEZ \'A "guaglioni.csv" arò eta = 19'
    results3 = compiler.compile_and_run(query3)
    assert len(results3) == 1  # Solo Genny
    assert results3[0]['nome'] == 'Genny'
    
    # Test >=
    query4 = 'RIPIGLIAMMO nome MMIEZ \'A "guaglioni.csv" arò eta >= 25'
    results4 = compiler.compile_and_run(query4)
    assert len(results4) == 2  # Ciro (35), SangueBlu (25)
    
    # Test <=
    query5 = 'RIPIGLIAMMO nome MMIEZ \'A "guaglioni.csv" arò eta <= 19'
    results5 = compiler.compile_and_run(query5)
    assert len(results5) == 2  # Genny (19), O_Track (17)
    
    # Test != / <>
    query6 = 'RIPIGLIAMMO nome MMIEZ \'A "guaglioni.csv" arò eta <> 19'
    results6 = compiler.compile_and_run(query6)
    assert len(results6) == 3  # Tutti tranne Genny
    names = [r['nome'] for r in results6]
    assert 'Genny' not in names


def test_null_check(compiler):
    """
    Test operatore NULL check (MANDATORY test #4 from feedback)
    
    Testa la funzionalità "è nisciun" (IS NULL) e "nun è nisciun" (IS NOT NULL)
    per il filtraggio di valori mancanti o nulli nel CSV.
    
    Requisito da feedback: "Null Check: Utilizzo dell'operatore è nisciun
    per il filtraggio di valori mancanti o nulli"
    """
    # Test IS NULL - trova righe con zona vuota/NULL
    query_is_null = '''
    RIPIGLIAMMO nome, zona, eta
    MMIEZ 'A "guaglioni_null.csv"
    arò zona è nisciun
    '''
    
    results_null = compiler.compile_and_run(query_is_null)
    assert len(results_null) == 2  # Genny e Patrizia hanno zona vuota
    names_null = [r['nome'] for r in results_null]
    assert 'Genny' in names_null
    assert 'Patrizia' in names_null
    assert 'Ciro' not in names_null  # Ha zona valida
    
    # Test IS NOT NULL - trova righe con zona non vuota
    query_is_not_null = '''
    RIPIGLIAMMO nome, zona, eta
    MMIEZ 'A "guaglioni_null.csv"
    arò zona nun è nisciun
    '''
    
    results_not_null = compiler.compile_and_run(query_is_not_null)
    assert len(results_not_null) == 2  # Ciro e O_Track hanno zona valida
    names_not_null = [r['nome'] for r in results_not_null]
    assert 'Ciro' in names_not_null
    assert 'O_Track' in names_not_null
    assert 'Genny' not in names_not_null  # Ha zona vuota
    assert 'Patrizia' not in names_not_null  # Ha zona e eta vuote






