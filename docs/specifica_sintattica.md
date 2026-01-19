# Specifica Sintattica - GomorraSQL

## 1. Grammatica EBNF Formale

```ebnf
(* Regola di Partenza *)
program ::= query

(* Struttura Query Principale *)
query ::= "RIPIGLIAMM" column_list "NMIEZ" source where_clause? "STAMM_ACCISI"

(* Lista Colonne *)
column_list ::= "*"
              | identifier_list

identifier_list ::= IDENTIFIER ("," IDENTIFIER)*

(* Sorgente Dati *)
source ::= STRING

(* Clausola WHERE (opzionale) *)
where_clause ::= "A" condition

(* Condizione *)
condition ::= expression comparison_op expression

(* Operatori di Confronto *)
comparison_op ::= "EGAL"
                | "NON E COSA"
                | "CHIU ASSAI"
                | "CHIU POC"
                | "EGAL O CHIU"
                | "EGAL O POC"

(* Espressioni *)
expression ::= IDENTIFIER
             | NUMBER
             | STRING

(* Token Terminali *)
IDENTIFIER ::= [a-zA-Z_][a-zA-Z0-9_]*
NUMBER ::= [0-9]+ ("." [0-9]+)?
STRING ::= '"' [^"]* '"'
```

## 2. Grammatica Lark (Python)

```lark
// ========================================
// GRAMMATICA GOMORRASQL PER LARK PARSER
// ========================================

start: query

// Query principale
query: "RIPIGLIAMM" column_list "NMIEZ" source where_clause? "STAMM_ACCISI"

// Lista colonne (tutte o specifiche)
column_list: all_columns
           | specific_columns

all_columns: "*"
specific_columns: IDENTIFIER ("," IDENTIFIER)*

// File sorgente
source: STRING

// Clausola WHERE
where_clause: "A" condition

// Condizione di filtro
condition: expression comparison expression

// Operatori di confronto
comparison: "EGAL"         -> op_equal
          | "NON E COSA"   -> op_not_equal
          | "CHIU ASSAI"   -> op_greater
          | "CHIU POC"     -> op_less
          | "EGAL O CHIU"  -> op_greater_equal
          | "EGAL O POC"   -> op_less_equal

// Espressioni
expression: IDENTIFIER     -> identifier_expr
          | NUMBER         -> number_expr
          | STRING         -> string_expr

// Token lessicali
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
NUMBER: /[0-9]+(\.[0-9]+)?/
STRING: /"[^"]*"/

// Ignora whitespace
%import common.WS
%ignore WS
```

## 3. Albero Sintattico Astratto (AST)

### 3.1 Struttura dei Nodi

```python
# Nodo radice del programma
class Program:
    query: Query

# Query completa
class Query:
    columns: List[str] | str  # "*" oppure ["col1", "col2", ...]
    source: str               # Nome del file CSV
    condition: Condition | None  # Clausola WHERE (opzionale)

# Condizione di filtro
class Condition:
    left: Expression
    operator: ComparisonOp
    right: Expression

# Operatori di confronto
class ComparisonOp(Enum):
    EQUAL = "EGAL"
    NOT_EQUAL = "NON E COSA"
    GREATER = "CHIU ASSAI"
    LESS = "CHIU POC"
    GREATER_EQUAL = "EGAL O CHIU"
    LESS_EQUAL = "EGAL O POC"

# Espressioni
class Expression:
    pass

class Identifier(Expression):
    name: str

class NumberLiteral(Expression):
    value: float

class StringLiteral(Expression):
    value: str
```

## 4. Esempi di Derivazione

### Esempio 1: Query Semplice Senza Filtro

**Input**:
```sql
RIPIGLIAMM nome, cognome NMIEZ "guaglioni.csv" STAMM_ACCISI
```

**Derivazione**:
```
program
└── query
    ├── RIPIGLIAMM
    ├── column_list
    │   └── specific_columns
    │       ├── IDENTIFIER("nome")
    │       ├── COMMA
    │       └── IDENTIFIER("cognome")
    ├── NMIEZ
    ├── source
    │   └── STRING("guaglioni.csv")
    └── STAMM_ACCISI
```

### Esempio 2: Query con WHERE

**Input**:
```sql
RIPIGLIAMM * NMIEZ "dati.csv" A eta CHIU ASSAI 18 STAMM_ACCISI
```

**Derivazione**:
```
program
└── query
    ├── RIPIGLIAMM
    ├── column_list
    │   └── all_columns
    │       └── ASTERISK("*")
    ├── NMIEZ
    ├── source
    │   └── STRING("dati.csv")
    ├── where_clause
    │   ├── A
    │   └── condition
    │       ├── expression
    │       │   └── IDENTIFIER("eta")
    │       ├── comparison
    │       │   └── op_greater("CHIU ASSAI")
    │       └── expression
    │           └── NUMBER(18)
    └── STAMM_ACCISI
```

### Esempio 3: Query con Confronto Stringhe

**Input**:
```sql
RIPIGLIAMM nome, corso NMIEZ "studenti.csv" A corso EGAL "Informatica" STAMM_ACCISI
```

**Derivazione**:
```
program
└── query
    ├── RIPIGLIAMM
    ├── column_list
    │   └── specific_columns
    │       ├── IDENTIFIER("nome")
    │       └── IDENTIFIER("corso")
    ├── NMIEZ
    ├── source
    │   └── STRING("studenti.csv")
    ├── where_clause
    │   ├── A
    │   └── condition
    │       ├── expression
    │       │   └── IDENTIFIER("corso")
    │       ├── comparison
    │       │   └── op_equal("EGAL")
    │       └── expression
    │           └── STRING("Informatica")
    └── STAMM_ACCISI
```

## 5. Proprietà della Grammatica

### 5.1 Ambiguità
La grammatica è **non ambigua**:
- Ogni query ha una sola derivazione possibile
- Gli operatori di confronto hanno la stessa precedenza (non serve precedenza, essendo usati solo in condizioni semplici)
- Non ci sono conflitti shift/reduce

### 5.2 Ricorsione
- **Non ricorsiva a sinistra**: La grammatica non contiene ricorsione a sinistra
- **Ricorsione a destra limitata**: Solo nella lista di colonne `identifier_list`

### 5.3 Complessità Parsing
- **Classe**: LL(1) / LR(1)
- **Parser suggerito**: LALR (Lark default)
- Tutte le produzioni possono essere determinate con 1 token di lookahead

## 6. First e Follow Set

### First Sets
```
FIRST(program) = {"RIPIGLIAMM"}
FIRST(query) = {"RIPIGLIAMM"}
FIRST(column_list) = {"*", IDENTIFIER}
FIRST(where_clause) = {"A"}
FIRST(condition) = {IDENTIFIER, NUMBER, STRING}
FIRST(expression) = {IDENTIFIER, NUMBER, STRING}
```

### Follow Sets
```
FOLLOW(program) = {$}
FOLLOW(query) = {$}
FOLLOW(column_list) = {"NMIEZ"}
FOLLOW(source) = {"A", "STAMM_ACCISI"}
FOLLOW(where_clause) = {"STAMM_ACCISI"}
FOLLOW(condition) = {"STAMM_ACCISI"}
```

## 7. Diagrammi Sintattici

### Query
```
──→ RIPIGLIAMM ──→ column_list ──→ NMIEZ ──→ source ──┬──→ where_clause ──┬──→ STAMM_ACCISI ──→
                                                       │                   │
                                                       └───────────────────┘
```

### Column List
```
       ┌──────────────┐
       │      ","     │
       ↓              │
──→ IDENTIFIER ───────┘──→
       ↑
       │
──→ "*" ──→
```

### Condition
```
──→ expression ──→ comparison ──→ expression ──→
```

## 8. Validazione Sintattica

### Query Valide ✓
```sql
RIPIGLIAMM * NMIEZ "file.csv" STAMM_ACCISI
RIPIGLIAMM nome NMIEZ "file.csv" STAMM_ACCISI
RIPIGLIAMM nome, cognome, eta NMIEZ "file.csv" STAMM_ACCISI
RIPIGLIAMM nome NMIEZ "file.csv" A eta CHIU ASSAI 18 STAMM_ACCISI
```

### Query Non Valide ✗
```sql
# Manca STAMM_ACCISI
RIPIGLIAMM nome NMIEZ "file.csv"

# Manca NMIEZ
RIPIGLIAMM nome "file.csv" STAMM_ACCISI

# Lista colonne vuota
RIPIGLIAMM NMIEZ "file.csv" STAMM_ACCISI

# WHERE senza condizione
RIPIGLIAMM nome NMIEZ "file.csv" A STAMM_ACCISI

# Operatore non valido
RIPIGLIAMM nome NMIEZ "file.csv" A eta > 18 STAMM_ACCISI
```

## 9. Estensioni Future

Possibili aggiunte alla sintassi:

### 9.1 Operatori Logici
```ebnf
condition ::= and_condition ("O" and_condition)*
and_condition ::= comparison ("E" comparison)*
```

### 9.2 Funzioni Aggregate
```ebnf
column_list ::= aggregate_func ("," aggregate_func)*
aggregate_func ::= "CUNTA" "(" IDENTIFIER ")"
                 | "SOMMA" "(" IDENTIFIER ")"
```

### 9.3 ORDER BY
```ebnf
query ::= "RIPIGLIAMM" column_list "NMIEZ" source 
          where_clause? 
          order_clause? 
          "STAMM_ACCISI"

order_clause ::= "METTL N'FILA" IDENTIFIER ("CRESCENN" | "CALANN")?
```
