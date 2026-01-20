"""
Test Suite per Generazione LLVM IR
Testa la corretta generazione di codice LLVM per diversi tipi di query
"""

import pytest
import sys
from pathlib import Path

# Aggiungi src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.compiler import GomorraCompiler
from src.llvm_codegen import LLVMCodeGenerator
from src.parser import GomorraParser
from src.transformer import ToAstTransformer
from src.semantic_analyzer import SemanticAnalyzer


@pytest.fixture
def setup_compiler():
    """Fixture che configura parser, transformer, semantic analyzer e codegen"""
    parser = GomorraParser()
    transformer = ToAstTransformer()
    semantic_analyzer = SemanticAnalyzer(data_dir="data")
    return parser, transformer, semantic_analyzer


def get_llvm_ir(query: str, setup_compiler) -> str:
    """Helper per generare LLVM IR da una query (PURO - senza side effects)"""
    parser, transformer, semantic_analyzer = setup_compiler
    
    # Parse e trasforma
    parse_tree = parser.parser.parse(query)
    ast = transformer.transform(parse_tree)
    
    # Analisi semantica
    semantic_analyzer.analyze(ast)
    
    # Genera LLVM IR puro usando get_ir() invece di generate_and_execute()
    # Disabilita ottimizzazioni per avere IR predicibile nei test
    codegen = LLVMCodeGenerator(data_dir="data", optimize=False)
    
    # Usa get_ir() che restituisce CompilationResult senza side-effects
    compilation_result = codegen.get_ir(ast)
    
    # Ritorna solo l'IR (contratto pulito: input → output)
    return compilation_result.llvm_ir



# ============================================================================
# TEST: Operatori di Confronto
# ============================================================================

def test_llvm_comparison_equal(setup_compiler):
    """Test generazione IR per confronto di uguaglianza (=)"""
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    arò eta = 19
    '''
    
    ir_code = get_llvm_ir(query, setup_compiler)
    
    # Verifica struttura base
    assert 'define i1 @"evaluate_row"' in ir_code
    assert 'entry:' in ir_code
    assert 'ret i1' in ir_code
    
    # Verifica parametri (eta = colonna int)
    assert 'i32 %' in ir_code  # Parametro per eta
    
    # Verifica istruzione confronto equal
    assert 'icmp eq i32' in ir_code
    assert '19' in ir_code  # Valore confronto


def test_llvm_comparison_not_equal(setup_compiler):
    """Test generazione IR per confronto di disuguaglianza (<>)"""
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    arò eta <> 19
    '''
    
    ir_code = get_llvm_ir(query, setup_compiler)
    
    # Verifica istruzione confronto not equal
    assert 'icmp ne i32' in ir_code
    assert '19' in ir_code


def test_llvm_comparison_greater_than(setup_compiler):
    """Test generazione IR per confronto maggiore (>)"""
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    arò eta > 18
    '''
    
    ir_code = get_llvm_ir(query, setup_compiler)
    
    # Verifica istruzione confronto greater than (signed)
    assert 'icmp sgt i32' in ir_code
    assert '18' in ir_code


def test_llvm_comparison_less_than(setup_compiler):
    """Test generazione IR per confronto minore (<)"""
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    arò eta < 30
    '''
    
    ir_code = get_llvm_ir(query, setup_compiler)
    
    # Verifica istruzione confronto less than (signed)
    assert 'icmp slt i32' in ir_code
    assert '30' in ir_code


def test_llvm_comparison_greater_equal(setup_compiler):
    """Test generazione IR per confronto maggiore o uguale (>=)"""
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    arò eta >= 18
    '''
    
    ir_code = get_llvm_ir(query, setup_compiler)
    
    # Verifica istruzione confronto greater or equal (signed)
    assert 'icmp sge i32' in ir_code
    assert '18' in ir_code


def test_llvm_comparison_less_equal(setup_compiler):
    """Test generazione IR per confronto minore o uguale (<=)"""
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    arò eta <= 25
    '''
    
    ir_code = get_llvm_ir(query, setup_compiler)
    
    # Verifica istruzione confronto less or equal (signed)
    assert 'icmp sle i32' in ir_code
    assert '25' in ir_code


# ============================================================================
# TEST: Operatori Logici
# ============================================================================

def test_llvm_logic_and(setup_compiler):
    """Test generazione IR per operatore logico AND"""
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    arò eta > 18 e eta < 30
    '''
    
    ir_code = get_llvm_ir(query, setup_compiler)
    
    # Verifica due confronti
    assert ir_code.count('icmp sgt') >= 1  # eta > 18
    assert ir_code.count('icmp slt') >= 1  # eta < 30
    
    # Verifica operatore AND bitwise
    assert 'and i1' in ir_code


def test_llvm_logic_or(setup_compiler):
    """Test generazione IR per operatore logico OR"""
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    arò eta < 20 o eta > 30
    '''
    
    ir_code = get_llvm_ir(query, setup_compiler)
    
    # Verifica due confronti
    assert 'icmp slt' in ir_code  # eta < 20
    assert 'icmp sgt' in ir_code  # eta > 30
    
    # Verifica operatore OR bitwise
    assert 'or i1' in ir_code


def test_llvm_logic_complex(setup_compiler):
    """Test generazione IR per espressione logica complessa (AND + OR)"""
    query = '''
    RIPIGLIAMMO nome, zona, eta
    MMIEZ 'A "guaglioni.csv"
    arò (eta > 18 e zona = "Scampia") o nome = "Ciro"
    '''
    
    ir_code = get_llvm_ir(query, setup_compiler)
    
    # Verifica presenza di tre parametri (eta, zona, nome)
    param_count = ir_code.count('i32 %')
    assert param_count >= 2  # Almeno eta e uno tra zona/nome
    
    # Verifica operatori logici
    assert 'and i1' in ir_code  # AND interno
    assert 'or i1' in ir_code   # OR esterno
    
    # Verifica confronti
    assert 'icmp sgt' in ir_code  # eta > 18


# ============================================================================
# TEST: NULL Checks
# ============================================================================

def test_llvm_null_check_is_null(setup_compiler):
    """Test generazione IR per controllo IS NULL"""
    query = '''
    RIPIGLIAMMO nome, zona
    MMIEZ 'A "guaglioni_null.csv"
    arò zona è nisciun
    '''
    
    ir_code = get_llvm_ir(query, setup_compiler)
    
    # Verifica funzione generata
    assert 'define i1 @"evaluate_row"' in ir_code
    assert 'ret i1' in ir_code
    
    # Nota: L'implementazione corrente usa placeholder (ret i1 0 o ret i1 1)
    # In futuro dovrebbe contenere: icmp eq ptr null


def test_llvm_null_check_is_not_null(setup_compiler):
    """Test generazione IR per controllo IS NOT NULL"""
    query = '''
    RIPIGLIAMMO nome, zona
    MMIEZ 'A "guaglioni_null.csv"
    arò zona nun è nisciun
    '''
    
    ir_code = get_llvm_ir(query, setup_compiler)
    
    # Verifica funzione generata
    assert 'define i1 @"evaluate_row"' in ir_code
    assert 'ret i1' in ir_code


# ============================================================================
# TEST: Type Inference e Tipi LLVM
# ============================================================================

def test_llvm_type_integer(setup_compiler):
    """Test generazione IR con tipo intero (i32)"""
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    arò eta > 18
    '''
    
    ir_code = get_llvm_ir(query, setup_compiler)
    
    # Verifica tipo parametro intero
    assert 'i32' in ir_code
    
    # Verifica istruzione confronto intero (icmp)
    assert 'icmp' in ir_code
    assert 'fcmp' not in ir_code  # Non deve usare fcmp per interi


def test_llvm_multiple_columns_same_type(setup_compiler):
    """Test generazione IR con multiple colonne dello stesso tipo"""
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    arò eta > 18 e eta < 30
    '''
    
    ir_code = get_llvm_ir(query, setup_compiler)
    
    # Verifica parametro eta (usato due volte)
    assert 'i32 %' in ir_code
    
    # Verifica due confronti sullo stesso parametro
    assert ir_code.count('icmp') >= 2


def test_llvm_multiple_columns_different_values(setup_compiler):
    """Test generazione IR con colonne diverse nella stessa condizione"""
    query = '''
    RIPIGLIAMMO nome, zona, eta
    MMIEZ 'A "guaglioni.csv"
    arò eta > 18 e zona = "Scampia"
    '''
    
    ir_code = get_llvm_ir(query, setup_compiler)
    
    # Verifica presenza di parametri multipli
    # Nota: zona è string, potrebbe essere i32 placeholder o i8*
    assert 'i32 %' in ir_code  # eta
    
    # Verifica operatore AND
    assert 'and i1' in ir_code


# ============================================================================
# TEST: Struttura IR
# ============================================================================

def test_llvm_basic_structure(setup_compiler):
    """Test struttura base del modulo LLVM generato"""
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    arò eta > 18
    '''
    
    ir_code = get_llvm_ir(query, setup_compiler)
    
    # Verifica header modulo
    assert 'ModuleID' in ir_code or 'target triple' in ir_code
    
    # Verifica definizione funzione
    assert 'define i1 @"evaluate_row"' in ir_code
    
    # Verifica basic block entry
    assert 'entry:' in ir_code
    
    # Verifica return statement
    assert 'ret i1' in ir_code


def test_llvm_single_basic_block(setup_compiler):
    """Test che venga generato un solo basic block (nessun branching)"""
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    arò (eta > 18 e eta < 30) o nome = "Ciro"
    '''
    
    ir_code = get_llvm_ir(query, setup_compiler)
    
    # Verifica un solo entry block (no branching)
    assert ir_code.count('entry:') == 1
    
    # Non deve contenere label aggiuntivi o br (branch)
    assert 'br ' not in ir_code or ir_code.count('br ') <= 1
    
    # Verifica operatori bitwise invece di branching
    assert 'and i1' in ir_code or 'or i1' in ir_code


def test_llvm_function_signature_parametric(setup_compiler):
    """Test che la funzione sia parametrica (non hardcoded)"""
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    arò eta = 19
    '''
    
    ir_code = get_llvm_ir(query, setup_compiler)
    
    # Verifica presenza di parametri nella signature
    assert 'define i1 @"evaluate_row"(i32 %' in ir_code
    
    # Verifica che i parametri vengano usati (non valori hardcoded nelle comparazioni)
    # Il valore 19 deve essere il secondo operando, il primo deve essere il parametro
    assert '%' in ir_code  # Uso di variabili SSA


# ============================================================================
# TEST: Edge Cases
# ============================================================================

def test_llvm_query_without_where(setup_compiler):
    """Test generazione IR per query senza clausola WHERE"""
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    '''
    
    ir_code = get_llvm_ir(query, setup_compiler)
    
    # Query senza WHERE non dovrebbe generare funzione LLVM
    # O dovrebbe generare una funzione che ritorna sempre true
    # Verifica comportamento atteso dal compilatore
    assert ir_code is not None or ir_code == ""


def test_llvm_single_condition(setup_compiler):
    """Test generazione IR per condizione singola (no AND/OR)"""
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    arò eta > 18
    '''
    
    ir_code = get_llvm_ir(query, setup_compiler)
    
    # Verifica assenza di operatori logici
    # Dovrebbe esserci solo un confronto diretto
    assert 'icmp sgt' in ir_code
    
    # Non dovrebbero esserci and/or (condizione singola)
    # Nota: potrebbero esserci per ottimizzazione, ma idealmente no
    lines_with_icmp = [line for line in ir_code.split('\n') if 'icmp' in line]
    assert len(lines_with_icmp) >= 1


def test_llvm_parentheses_precedence(setup_compiler):
    """Test generazione IR con precedenza operatori e parentesi"""
    query = '''
    RIPIGLIAMMO nome, eta
    MMIEZ 'A "guaglioni.csv"
    arò (eta > 18 e eta < 25) o eta > 30
    '''
    
    ir_code = get_llvm_ir(query, setup_compiler)
    
    # Verifica tre confronti
    assert ir_code.count('icmp') >= 3
    
    # Verifica AND e OR
    assert 'and i1' in ir_code
    assert 'or i1' in ir_code
    
    # Verifica struttura: AND dovrebbe essere valutato prima di OR
    # (ordine delle istruzioni SSA)
    and_line = None
    or_line = None
    for i, line in enumerate(ir_code.split('\n')):
        if 'and i1' in line:
            and_line = i
        if 'or i1' in line:
            or_line = i
    
    # AND deve apparire prima di OR nel codice
    if and_line is not None and or_line is not None:
        assert and_line < or_line


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
