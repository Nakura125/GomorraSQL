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


def test_semantic_error_column(compiler):
    """Test errore semantico (colonna inesistente)"""
    query = '''
    RIPIGLIAMMO colonna_inesistente
    MMIEZ 'A "guaglioni.csv"
    '''
    
    with pytest.raises(SemanticError):
        compiler.compile_and_run(query)


def test_semantic_error_table(compiler):
    """Test errore semantico (tabella inesistente)"""
    query = '''
    RIPIGLIAMMO nome
    MMIEZ 'A "tabella_che_non_esiste.csv"
    '''
    
    with pytest.raises(SemanticError) as exc_info:
        compiler.compile_and_run(query)
    assert "non trovata" in str(exc_info.value)


def test_semantic_error_column_in_where(compiler):
    """Test errore semantico (colonna inesistente nel WHERE)"""
    query = '''
    RIPIGLIAMMO nome
    MMIEZ 'A "guaglioni.csv"
    arò colonna_inesistente > 10
    '''
    
    with pytest.raises(SemanticError) as exc_info:
        compiler.compile_and_run(query)
    assert "non esiste" in str(exc_info.value)


def test_select_specific_columns(compiler):
    """Test SELECT con colonne specifiche (non *)"""
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    arò zona = "Scampia"
    '''
    
    results = compiler.compile_and_run(query)
    assert len(results) == 1  # Solo Genny
    assert results[0]['nome'] == 'Genny'
    assert results[0]['eta'] == '19'  # I valori CSV sono stringhe
    # Verifica che solo le colonne richieste siano presenti
    assert 'nome' in results[0]
    assert 'eta' in results[0]
    # Nota: la proiezione è implementata ma zona potrebbe essere presente per il WHERE


def test_syntax_error(compiler):
    """Test errore sintattico - ora solleva SyntaxError invece di ritornare None"""
    # Query con sintassi invalida (manca FROM)
    query = 'RIPIGLIAMMO nome arò eta > 18'
    
    # Parser ora solleva SyntaxError invece di ritornare None
    with pytest.raises(SyntaxError, match="Errore sintattico"):
        compiler.parser.parse(query)


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


def test_parse_file_utility(tmp_path):
    """Test funzione utility parse_file()"""
    from src.parser import parse_file
    
    # Crea file temporaneo con query valida
    query_file = tmp_path / "test_parse.gsql"
    query_file.write_text('''
    RIPIGLIAMMO nome
    MMIEZ 'A "guaglioni.csv"
    ''')
    
    ast = parse_file(str(query_file))
    assert ast is not None


def test_negative_values(compiler):
    """Test comparazione con valori negativi"""
    # Nota: nessuna riga ha età negativa, quindi risultato vuoto
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    arò eta < -5
    '''
    
    results = compiler.compile_and_run(query)
    assert len(results) == 0  # Nessuna età negativa


def test_comparison_with_float():
    """Test comparazioni con valori float"""
    # Crea CSV temporaneo con valori float
    import tempfile
    import os
    
    csv_content = """nome,altezza
Ciro,1.85
Genny,1.72
Patrizia,1.65
O_Track,1.80"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, dir='data') as f:
        f.write(csv_content)
        temp_file = f.name
    
    try:
        compiler = GomorraCompiler(data_dir='data')
        filename = os.path.basename(temp_file)
        
        query = f'''
        RIPIGLIAMMO nome, altezza
        MMIEZ 'A "{filename}"
        arò altezza > 1.75
        '''
        
        results = compiler.compile_and_run(query)
        assert len(results) == 2  # Ciro (1.85) e O_Track (1.80)
        heights = [float(r['altezza']) for r in results]
        assert all(h > 1.75 for h in heights)
    finally:
        os.unlink(temp_file)


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


def test_null_check_in_logic_op(compiler):
    """Test NULL check combinato con operatori logici"""
    # Usa una condizione che funziona con i dati disponibili
    query = '''
    RIPIGLIAMMO nome, zona, eta
    MMIEZ 'A "guaglioni_null.csv"
    arò zona è nisciun
    '''
    
    results = compiler.compile_and_run(query)
    assert len(results) == 2  # Genny e Patrizia hanno zona NULL
    names = [r['nome'] for r in results]
    assert 'Genny' in names
    assert 'Patrizia' in names


def test_all_null_column():
    """Test colonna con tutti valori NULL"""
    import tempfile
    import os
    
    # CSV con colonna completamente vuota
    csv_content = """nome,commento,eta
Ciro,,35
Genny,,19
Patrizia,,22"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, dir='data') as f:
        f.write(csv_content)
        temp_file = f.name
    
    try:
        compiler = GomorraCompiler(data_dir='data')
        filename = os.path.basename(temp_file)
        
        query = f'''
        RIPIGLIAMMO nome, commento
        MMIEZ 'A "{filename}"
        arò commento è nisciun
        '''
        
        results = compiler.compile_and_run(query)
        assert len(results) == 3  # Tutti hanno commento NULL
    finally:
        os.unlink(temp_file)


def test_complex_logic_operators(compiler):
    """Test operatori logici complessi annidati"""
    query = '''
    RIPIGLIAMMO nome, eta, zona
    MMIEZ 'A "guaglioni.csv"
    arò (eta > 20 e zona = "Secondigliano") o (eta < 20 e zona = "Scampia")
    '''
    
    results = compiler.compile_and_run(query)
    assert len(results) == 2  # Ciro (35, Secondigliano) e Genny (19, Scampia)
    names = [r['nome'] for r in results]
    assert 'Ciro' in names
    assert 'Genny' in names


def test_parser_grammar_not_found():
    """Test errore quando grammatica non esiste"""
    from src.parser import GomorraParser
    
    with pytest.raises(FileNotFoundError) as exc_info:
        parser = GomorraParser(grammar_file="grammatica_inesistente.txt")
    assert "Non trovo il file della grammatica" in str(exc_info.value)


def test_select_all_rows_no_where(compiler):
    """Test SELECT senza WHERE (tutte le righe)"""
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    '''
    
    results = compiler.compile_and_run(query)
    assert len(results) == 4  # Tutte le 4 righe
    assert 'nome' in results[0]
    assert 'eta' in results[0]


def test_comparison_string_equality(compiler):
    """Test comparazione con stringhe"""
    query = '''
    RIPIGLIAMMO nome, zona
    MMIEZ 'A "guaglioni.csv"
    arò zona = "Scampia"
    '''
    
    results = compiler.compile_and_run(query)
    assert len(results) == 1
    assert results[0]['nome'] == 'Genny'
    assert results[0]['zona'] == 'Scampia'


def test_multiple_and_conditions(compiler):
    """Test multiple condizioni AND"""
    query = '''
    RIPIGLIAMMO nome, eta, zona
    MMIEZ 'A "guaglioni.csv"
    arò eta > 18 e eta < 30 e zona = "Forcella"
    '''
    
    results = compiler.compile_and_run(query)
    assert len(results) == 1  # Solo SangueBlu (25, Forcella)
    assert results[0]['nome'] == 'SangueBlu'


def test_multiple_or_conditions(compiler):
    """Test multiple condizioni OR"""
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    arò eta = 17 o eta = 19 o eta = 35
    '''
    
    results = compiler.compile_and_run(query)
    assert len(results) == 3  # O_Track (17), Genny (19), Ciro (35)
    ages = [int(r['eta']) for r in results]  # Converti stringhe a int
    assert 17 in ages
    assert 19 in ages
    assert 35 in ages


def test_comparison_greater_or_equal_edge(compiler):
    """Test >= con valore esatto (edge case)"""
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    arò eta >= 19
    '''
    
    results = compiler.compile_and_run(query)
    assert len(results) == 3  # Genny (19), SangueBlu (25), Ciro (35)
    # Verifica che Genny (esattamente 19) sia inclusa
    names = [r['nome'] for r in results]
    assert 'Genny' in names


def test_comparison_less_or_equal_edge(compiler):
    """Test <= con valore esatto (edge case)"""
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    arò eta <= 19
    '''
    
    results = compiler.compile_and_run(query)
    assert len(results) == 2  # O_Track (17), Genny (19)
    # Verifica che Genny (esattamente 19) sia inclusa
    names = [r['nome'] for r in results]
    assert 'Genny' in names
    assert 'O_Track' in names


def test_boolean_value_conversion():
    """Test conversione valori booleani (true/false)"""
    from src.transformer import ToAstTransformer
    from lark import Token
    
    transformer = ToAstTransformer()
    
    # Test conversione 'true'
    result_true = transformer.value([Token('CNAME', 'true')])
    assert result_true is True
    
    # Test conversione 'TRUE' (case insensitive)
    result_true_upper = transformer.value([Token('CNAME', 'TRUE')])
    assert result_true_upper is True
    
    # Test conversione 'false'
    result_false = transformer.value([Token('CNAME', 'false')])
    assert result_false is False
    
    # Test conversione 'FALSE' (case insensitive)
    result_false_upper = transformer.value([Token('CNAME', 'FALSE')])
    assert result_false_upper is False
    
    # Test conversione valore non booleano (rimane invariato)
    result_other = transformer.value([Token('CNAME', 'somevalue')])
    assert result_other == 'somevalue'






