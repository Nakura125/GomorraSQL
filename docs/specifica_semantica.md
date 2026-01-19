# Specifica Semantica - GomorraSQL

## 1. Introduzione

L'analisi semantica di GomorraSQL verifica che le query sintatticamente corrette abbiano significato valido rispetto al modello dati (file CSV) e alle regole del linguaggio.

## 2. Scope e Ambiente

### 2.1 Scope Globale Unico

GomorraSQL adotta un **modello a scope singolo**:
- Tutte le variabili (colonne) appartengono allo scope del file CSV specificato
- Non esistono dichiarazioni di variabili: le colonne sono definite dall'header del CSV
- Lo scope è determinato staticamente dal file `NMIEZ`

### 2.2 Symbol Table

La symbol table contiene:

```python
class SymbolTable:
    source_file: str           # Nome del file CSV
    columns: Dict[str, Type]   # {nome_colonna: tipo}
    
class Type(Enum):
    STRING = "string"
    NUMBER = "number"
    UNKNOWN = "unknown"
```

**Popolazione della Symbol Table**:
1. Durante l'analisi semantica, si legge l'header del CSV
2. Si estraggono i nomi delle colonne
3. I tipi sono inferiti analizzando le prime N righe o marcati come `UNKNOWN`

## 3. Regole Semantiche

### 3.1 Regola S1: Validazione Colonne Esistenti

**Descrizione**: Ogni identificatore usato in `RIPIGLIAMM` e nella clausola `A` deve esistere nell'header del file CSV.

**Algoritmo di Verifica**:
```python
def check_column_exists(identifier: str, symbol_table: SymbolTable) -> bool:
    if identifier not in symbol_table.columns:
        raise SemanticError(f"Colonna '{identifier}' non esiste in {symbol_table.source_file}")
    return True
```

**Esempi**:

✓ **Valido**:
```sql
-- CSV header: nome,cognome,eta
RIPIGLIAMM nome, eta NMIEZ "file.csv" STAMM_ACCISI
```

✗ **Errore Semantico**:
```sql
-- CSV header: nome,cognome,eta
RIPIGLIAMM nome, indirizzo NMIEZ "file.csv" STAMM_ACCISI
-- Errore: Colonna 'indirizzo' non esiste in file.csv
```

### 3.2 Regola S2: Type Checking nelle Condizioni

**Descrizione**: Gli operatori di confronto richiedono compatibilità di tipo tra operandi.

**Tabella Compatibilità**:

| Operatore | Tipo Sinistro | Tipo Destro | Valido | Note |
|-----------|---------------|-------------|--------|------|
| `EGAL` | NUMBER | NUMBER | ✓ | Confronto numerico |
| `EGAL` | STRING | STRING | ✓ | Confronto lessicografico |
| `EGAL` | NUMBER | STRING | ✗ | Type mismatch |
| `NON E COSA` | NUMBER | NUMBER | ✓ | |
| `NON E COSA` | STRING | STRING | ✓ | |
| `CHIU ASSAI` | NUMBER | NUMBER | ✓ | Confronto numerico |
| `CHIU ASSAI` | STRING | STRING | ⚠ | Warning: confronto lessicografico |
| `CHIU ASSAI` | NUMBER | STRING | ✗ | Type mismatch |
| `CHIU POC` | NUMBER | NUMBER | ✓ | |
| `CHIU POC` | STRING | STRING | ⚠ | Warning |
| `EGAL O CHIU` | NUMBER | NUMBER | ✓ | |
| `EGAL O POC` | NUMBER | NUMBER | ✓ | |

**Algoritmo di Verifica**:
```python
def check_type_compatibility(left: Expression, op: ComparisonOp, 
                            right: Expression, symbol_table: SymbolTable):
    left_type = infer_type(left, symbol_table)
    right_type = infer_type(right, symbol_table)
    
    # Regola 1: Uguaglianza/Disuguaglianza ammette confronti omogenei
    if op in [EQUAL, NOT_EQUAL]:
        if left_type == right_type:
            return True
        else:
            raise SemanticError(f"Type mismatch: {left_type} {op} {right_type}")
    
    # Regola 2: Operatori ordinali richiedono numeri
    if op in [GREATER, LESS, GREATER_EQUAL, LESS_EQUAL]:
        if left_type == NUMBER and right_type == NUMBER:
            return True
        elif left_type == STRING and right_type == STRING:
            warning(f"Confronto lessicografico tra stringhe con {op}")
            return True
        else:
            raise SemanticError(f"Operatore {op} richiede operandi numerici")
```

**Esempi**:

✓ **Valido**:
```sql
-- eta è NUMBER, 18 è NUMBER
RIPIGLIAMM nome NMIEZ "file.csv" A eta CHIU ASSAI 18 STAMM_ACCISI
```

✗ **Errore Semantico**:
```sql
-- nome è STRING, 18 è NUMBER
RIPIGLIAMM nome NMIEZ "file.csv" A nome CHIU ASSAI 18 STAMM_ACCISI
-- Errore: Type mismatch - cannot compare STRING with NUMBER
```

⚠ **Warning**:
```sql
-- cognome è STRING, "Rossi" è STRING
RIPIGLIAMM nome NMIEZ "file.csv" A cognome CHIU ASSAI "Rossi" STAMM_ACCISI
-- Warning: Confronto lessicografico tra stringhe
```

### 3.3 Regola S3: Inferenza di Tipo

**Descrizione**: I tipi delle espressioni sono determinati come segue:

```python
def infer_type(expr: Expression, symbol_table: SymbolTable) -> Type:
    if isinstance(expr, NumberLiteral):
        return Type.NUMBER
    
    elif isinstance(expr, StringLiteral):
        return Type.STRING
    
    elif isinstance(expr, Identifier):
        # Lookup nella symbol table
        if expr.name in symbol_table.columns:
            return symbol_table.columns[expr.name]
        else:
            # Già gestito da S1
            raise SemanticError(f"Colonna non definita: {expr.name}")
```

**Strategie di Inferenza dai Dati CSV**:

1. **Analisi Euristica**:
   - Legge le prime N righe (default: 100)
   - Tenta parsing numerico per ogni colonna
   - Se tutte le righe sono numeri → `Type.NUMBER`
   - Altrimenti → `Type.STRING`

2. **Lazy Typing**:
   - Durante la compilazione: `Type.UNKNOWN`
   - A runtime: casting dinamico quando necessario

```python
def infer_column_types(csv_file: str, sample_size: int = 100) -> Dict[str, Type]:
    types = {}
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        rows = list(itertools.islice(reader, sample_size))
        
        for column in reader.fieldnames:
            all_numeric = all(is_numeric(row[column]) for row in rows)
            types[column] = Type.NUMBER if all_numeric else Type.STRING
    
    return types
```

### 3.4 Regola S4: Validazione File Sorgente

**Descrizione**: Il file specificato in `NMIEZ` deve esistere ed essere accessibile.

**Verifica**:
```python
def check_source_file(source: str):
    # Rimuovi apici dalla stringa
    filepath = source.strip('"')
    
    if not os.path.exists(filepath):
        raise SemanticError(f"File non trovato: {filepath}")
    
    if not filepath.endswith('.csv'):
        warning(f"Il file {filepath} potrebbe non essere un CSV valido")
```

### 3.5 Regola S5: Wildcard `*`

**Descrizione**: Il simbolo `*` in `RIPIGLIAMM *` seleziona tutte le colonne del CSV.

**Semantica**:
- Se usato, non possono essere specificate altre colonne
- Equivale a elencare esplicitamente tutte le colonne nell'ordine del CSV

**Verifica**:
```python
def check_column_list(columns):
    if "*" in columns and len(columns) > 1:
        raise SemanticError("Non puoi usare '*' insieme ad altre colonne")
```

## 4. Fasi dell'Analisi Semantica

### Fase 1: Costruzione Symbol Table

```python
def build_symbol_table(ast: Query) -> SymbolTable:
    source_file = ast.source.strip('"')
    
    # Verifica esistenza file (S4)
    check_source_file(source_file)
    
    # Estrai nomi colonne dall'header
    column_names = read_csv_header(source_file)
    
    # Inferenza tipi (opzionale)
    column_types = infer_column_types(source_file)
    
    return SymbolTable(source_file, column_types)
```

### Fase 2: Validazione Colonne

```python
def validate_columns(ast: Query, symbol_table: SymbolTable):
    # Gestione wildcard (S5)
    if ast.columns == "*":
        return
    
    # Verifica esistenza colonne in SELECT (S1)
    for col in ast.columns:
        check_column_exists(col, symbol_table)
```

### Fase 3: Type Checking

```python
def validate_condition(condition: Condition, symbol_table: SymbolTable):
    if condition is None:
        return
    
    # Verifica colonne nella condizione (S1)
    if isinstance(condition.left, Identifier):
        check_column_exists(condition.left.name, symbol_table)
    
    if isinstance(condition.right, Identifier):
        check_column_exists(condition.right.name, symbol_table)
    
    # Type checking (S2, S3)
    check_type_compatibility(condition.left, condition.operator, 
                           condition.right, symbol_table)
```

## 5. Esempi Completi

### Esempio 1: Query Valida

**Input**:
```sql
RIPIGLIAMM nome, cognome, eta 
NMIEZ "guaglioni.csv" 
A eta CHIU ASSAI 18 
STAMM_ACCISI
```

**CSV Header**: `id,nome,cognome,data_nascita,email,corso,eta`

**Analisi Semantica**:
1. ✓ File `guaglioni.csv` esiste
2. ✓ Colonne `nome`, `cognome`, `eta` esistono
3. ✓ `eta` è inferito come NUMBER
4. ✓ `18` è NUMBER
5. ✓ `CHIU ASSAI` compatibile con NUMBER × NUMBER

**Risultato**: ✅ Semanticamente corretta

### Esempio 2: Colonna Inesistente

**Input**:
```sql
RIPIGLIAMM nome, indirizzo 
NMIEZ "guaglioni.csv" 
STAMM_ACCISI
```

**CSV Header**: `id,nome,cognome,eta`

**Analisi Semantica**:
1. ✓ File esiste
2. ✓ Colonna `nome` esiste
3. ✗ Colonna `indirizzo` **non esiste**

**Errore**: ❌ `SemanticError: Colonna 'indirizzo' non esiste in guaglioni.csv`

### Esempio 3: Type Mismatch

**Input**:
```sql
RIPIGLIAMM nome 
NMIEZ "guaglioni.csv" 
A nome CHIU ASSAI 100 
STAMM_ACCISI
```

**CSV Header**: `nome,cognome,eta` (nome è STRING)

**Analisi Semantica**:
1. ✓ File esiste
2. ✓ Colonna `nome` esiste (tipo: STRING)
3. ✓ `100` è NUMBER
4. ✗ `CHIU ASSAI` con STRING × NUMBER **non valido**

**Errore**: ❌ `SemanticError: Type mismatch - cannot compare STRING with NUMBER`

### Esempio 4: Warning per Confronto Stringhe

**Input**:
```sql
RIPIGLIAMM nome 
NMIEZ "guaglioni.csv" 
A cognome CHIU ASSAI "Rossi" 
STAMM_ACCISI
```

**Analisi Semantica**:
1. ✓ File esiste
2. ✓ Colonna `cognome` esiste (tipo: STRING)
3. ✓ `"Rossi"` è STRING
4. ⚠ `CHIU ASSAI` con STRING × STRING: confronto lessicografico

**Risultato**: ✅ Valida, ⚠️ Warning emesso

## 6. Gestione Errori Semantici

### 6.1 Tipi di Errori

```python
class SemanticError(Exception):
    """Errore fatale che impedisce la compilazione"""
    pass

class SemanticWarning:
    """Avviso non bloccante"""
    pass
```

### 6.2 Messaggi di Errore

Formato: `[ERRORE SEMANTICO] <descrizione> (riga: <num>, colonna: <num>)`

Esempi:
- `[ERRORE SEMANTICO] Colonna 'stipendio' non trovata in affiliati.csv`
- `[ERRORE SEMANTICO] Type mismatch: impossibile confrontare STRING con NUMBER`
- `[WARNING] Confronto lessicografico tra stringhe 'cognome' e 'Rossi'`

## 7. Coercion e Casting (Opzionale)

### 7.1 Casting Implicito

Possibile estensione: conversione automatica stringhe → numeri

```python
def try_coerce(left_type: Type, right_type: Type) -> Tuple[Type, Type]:
    # Se uno è NUMBER e l'altro STRING numerico, converti
    if left_type == Type.STRING and right_type == Type.NUMBER:
        if can_parse_as_number(left_value):
            return (Type.NUMBER, Type.NUMBER)
    
    return (left_type, right_type)
```

**Esempio**:
```sql
-- Se 'eta' è salvata come stringa nel CSV ma contiene "25"
A eta CHIU ASSAI 18  -- Casting automatico "25" → 25
```

## 8. Annotazioni AST dopo Analisi Semantica

Dopo l'analisi, l'AST viene arricchito con informazioni semantiche:

```python
class AnnotatedExpression(Expression):
    original: Expression
    inferred_type: Type
    
class AnnotatedQuery(Query):
    symbol_table: SymbolTable
    column_indices: Dict[str, int]  # Mapping colonna → indice CSV
```

## 9. Pseudocodice Completo Analizzatore Semantico

```python
def semantic_analysis(ast: Query) -> AnnotatedQuery:
    # Fase 1: Costruzione Symbol Table
    symbol_table = build_symbol_table(ast)
    
    # Fase 2: Validazione colonne
    validate_columns(ast, symbol_table)
    
    # Fase 3: Validazione condizione (se presente)
    if ast.condition:
        validate_condition(ast.condition, symbol_table)
    
    # Fase 4: Annotazione AST
    annotated_ast = annotate_ast(ast, symbol_table)
    
    return annotated_ast
```

## 10. Estensioni Future

### 10.1 Funzioni Aggregate
- Validazione: `CUNTA(*)` valido, `CUNTA(colonna_inesistente)` errore
- Type checking: `SOMMA` richiede colonna numerica

### 10.2 Operatori Logici
- `E` (AND), `O` (OR): richiedono condizioni booleane
- Propagazione tipo: `condition E condition → boolean`

### 10.3 Null Safety
- Gestione valori mancanti nel CSV
- Operatore `NUN E NIENT` (IS NOT NULL)
