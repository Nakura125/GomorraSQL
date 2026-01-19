# GomorraSQL - Compilatore SQL in Dialetto Napoletano

**GomorraSQL** è un Domain Specific Language (DSL) dichiarativo ispirato a SQL con sintassi in dialetto napoletano. Questo progetto implementa un **compilatore completo** che genera LLVM IR per ottimizzare l'esecuzione delle query WHERE su file CSV.

**Autore**: Angelo Alberico  
**Matricola**: NF22500104  
**Corso**: Implementazione di Linguaggi di Programmazione  
**Anno Accademico**: 2025/2026

---

## Documentazione Aggiuntiva

**📄 [SPECIFICA_COMPLETA.md](docs/SPECIFICA_COMPLETA.md)**

**📄 [REPORT_AI.md](docs/AI_USAGE_REPORT.md)**

## 🚀 Quick Start

### Installazione
```bash
# Clona repository
git clone <repository-url>

# Installa dipendenze con uv
uv sync
```

### Esecuzione Test
```bash
# Tutti i test (20 totali)
uv run pytest tests/ -v

# Con coverage report
uv run pytest tests/ -v --cov=src --cov-report=term-missing

# Test specifici
uv run pytest tests/test_compiler.py -v        # 11 test compiler
uv run pytest tests/test_generators.py -v      # 3 test generators
uv run pytest tests/test_type_inference.py -v  # 6 test type inference
```


## 📊 Test Suite

### Test Compiler (`test_compiler.py` - 11 test)
```python
def test_select_all_no_where()         # SELECT senza WHERE
def test_select_with_where()           # SELECT con condizione
def test_select_with_null_check()      # NULL check (feedback #4)
def test_join_query()                  # JOIN tra tabelle
def test_lexer_error_invalid_char()    # Errore lessicale
def test_parser_error_missing_token()  # Errore sintattico
def test_semantic_error_column()       # Colonna inesistente
def test_semantic_error_table()        # Tabella inesistente
def test_llvm_ir_generation()          # Generazione IR
def test_where_clause_comparison()     # Operatori comparazione
def test_null_check_operations()       # Operatori NULL
```

### Test Scalabilità (`test_generators.py` - 3 test)
```python
def test_generator_scalability()       # 500K righe JOIN
def test_generator_memory_efficiency() # Uso memoria ridotto
def test_csv_columns_reading()         # Lettura header-only
```

### Test Type Inference (`test_type_inference.py` - 5 test)
```python
def test_type_inference_integer()      # Inferenza interi
def test_type_inference_float()        # Inferenza float
def test_type_inference_string()       # Inferenza stringhe
def test_type_inference_mixed()        # Tipi misti
def test_type_inference_null_values()  # Gestione NULL
```

**Esecuzione**:
```bash
# Tutti i test con coverage
uv run pytest tests/ -v --cov=src --cov-report=term-missing

# Test specifici
uv run pytest tests/test_compiler.py -v
uv run pytest tests/test_generators.py -v
uv run pytest tests/test_type_inference.py -v
```

---

## 📝 Sintassi GomorraSQL

### Parole Chiave
| SQL Standard | GomorraSQL | Esempio |
|--------------|------------|---------|
| `SELECT`     | `RIPIGLIAMMO` | `RIPIGLIAMMO nome, eta` |
| `FROM`       | `MMIEZ 'A` | `MMIEZ 'A "guaglioni.csv"` |
| `WHERE`      | `arò` | `arò eta > 18` |
| `JOIN`       | `pesc e pesc` | `pesc e pesc "ruoli.csv"` |
| `AND`        | `E` | `arò eta > 18 E zona = "Scampia"` |
| `OR`         | `O` | `arò nome = "Ciro" O eta < 25` |
| `IS NULL`    | `è nisciun` | `arò zona è nisciun` |
| `IS NOT NULL`| `nun è nisciun` | `arò nome nun è nisciun` |

### Operatori
- **Comparazione**: `>`, `<`, `>=`, `<=`, `=`, `<>`, `!=`
- **Logici**: `E` (AND), `O` (OR)
- **NULL**: `è nisciun` (IS NULL), `nun è nisciun` (IS NOT NULL)

### Esempi Query

#### 1. SELECT Semplice
```sql
RIPIGLIAMMO nome, eta
MMIEZ 'A "guaglioni.csv"
```

#### 2. SELECT con WHERE
```sql
RIPIGLIAMMO nome, zona
MMIEZ 'A "guaglioni.csv"
arò eta > 18
```

#### 3. Operatori Logici
```sql
RIPIGLIAMMO nome
MMIEZ 'A "guaglioni.csv"
arò (eta > 18 E zona = "Scampia") O nome = "Ciro"
```

#### 4. JOIN tra Tabelle
```sql
RIPIGLIAMMO nome, nome_2, ruolo
MMIEZ 'A "guaglioni.csv"
pesc e pesc "ruoli.csv"
arò nome = nome_2
```

#### 5. NULL Check
```sql
-- IS NULL
RIPIGLIAMMO nome
MMIEZ 'A "guaglioni.csv"
arò zona è nisciun

-- IS NOT NULL
RIPIGLIAMMO nome, eta
MMIEZ 'A "guaglioni.csv"
arò nome nun è nisciun
```

#### 6. Query Complessa
```sql
RIPIGLIAMMO guaglioni.nome, lexer.token, lexer.line
MMIEZ 'A "guaglioni.csv"
pesc e pesc "lexer.csv"
arò guaglioni.eta > 18 E lexer.line < 100
```

---
## 🔗 Collegamenti Utili

### Repository e Documentazione
- **GitHub**: [github.com/Nakura125/GomorraSQL](https://github.com/Nakura125/GomorraSQL)
- **Specifica Completa**: [docs/SPECIFICA_COMPLETA.md](docs/SPECIFICA_COMPLETA.md)
- **Presentazione Beamer**: Slide LaTeX nella repository

### Riferimenti Tecnici
- **LLVM Language Reference**: [llvm.org/docs/LangRef.html](https://llvm.org/docs/LangRef.html)
- **llvmlite Documentation**: [llvmlite.readthedocs.io](https://llvmlite.readthedocs.io/)
- **Lark Parser**: [lark-parser.readthedocs.io](https://lark-parser.readthedocs.io/)

### Progetto Originale
- **Gomorra-SQL (Java)**: [github.com/aurasphere/gomorra-sql](https://github.com/aurasphere/gomorra-sql)

---

## 📧 Contatti

**Angelo Alberico**  
Matricola: NF22500104  
GitHub: [@Nakura125](https://github.com/Nakura125)

---

## 📄 Licenza

Questo progetto è sviluppato per scopi didattici nel corso di **Implementazione di Linguaggi di Programmazione** presso l'Università degli Studi di Salerno.

Il progetto originale Gomorra-SQL (Java) è distribuito sotto licenza MIT da [Donato Rimenti](https://github.com/aurasphere).

---

**Fine Documento** - Ultima modifica: Gennaio 2026

---

## 👥 Autore
Angelo Alberico - Progetto Linguaggi e Compilatori

---

