
## ▶️ Esecuzione Query

### Query da File
```bash
# SELECT semplice (ottimizzazioni abilitate di default)
uv run python main.py queries/01_select_simple.gsql

# Query con confronto - mostra LLVM IR ottimizzato
uv run python main.py --show-ir queries/02_where_complex.gsql

# Query senza ottimizzazioni (per debug)
uv run python main.py --show-ir --no-optimize queries/02_where_complex.gsql

# Esegui tutte le query di esempio
uv run python run_all_examples.py
```

### Query Inline (da Terminale)
```bash
# SELECT inline (ottimizzato di default)
uv run python main.py "RIPIGLIAMMO nome MMIEZ 'A \"guaglioni.csv\""

# SELECT con WHERE - mostra LLVM IR ottimizzato
uv run python main.py --show-ir "RIPIGLIAMMO nome, zona MMIEZ 'A \"guaglioni.csv\" arò eta > 18"

# Query complessa senza ottimizzazioni (debug)
uv run python main.py --show-ir --no-optimize "RIPIGLIAMMO nome MMIEZ 'A \"guaglioni.csv\" arò eta > 18 E zona = \"Scampia\""

# Query con NULL check
uv run python main.py "RIPIGLIAMMO nome MMIEZ 'A \"guaglioni.csv\" arò nome nun è nisciun"

# Query con JOIN
uv run python main.py "RIPIGLIAMMO nome, token MMIEZ 'A \"guaglioni.csv\" pesc e pesc \"lexer.csv\""
```

### Esecuzione con JIT LLVM (Sperimentale)
```bash
# Abilita JIT compilation (instabile su ARM64)
GOMORRASQL_ENABLE_JIT=1 uv run python main.py queries/08_comparison_equal.gsql

# NOTA: Il JIT è disabilitato di default su ARM64 (Apple Silicon)
# perché può causare crash. Usa solo per sperimentazione.
```

---

## 🧪 Testing

### Test Completi
```bash
# Esegui tutti i test con output verboso
uv run pytest tests/ -v

# Test con coverage completo
uv run pytest tests/ --cov=src --cov-report=term-missing -v

# Test con coverage (prime 80 righe output)
uv run pytest tests/ --cov=src --cov-report=term-missing -v 2>&1 | head -80
```

### Test Specifici
```bash
# Test compiler (11 test)
uv run pytest tests/test_compiler.py -v

# Test scalabilità generators (3 test)
uv run pytest tests/test_generators.py -v

# Test type inference (5 test)
uv run pytest tests/test_type_inference.py -v
```

### Test Singolo
```bash
# Esegui test specifico per nome
uv run pytest tests/test_compiler.py::test_select_all_no_where -v

# Test con keyword matching
uv run pytest tests/ -k "null" -v

# Test con output dettagliato (print statements)
uv run pytest tests/ -v -s
```

---

## 🔍 Debug e Analisi

### Visualizza LLVM IR Generato
```bash
# Mostra LLVM IR ottimizzato (default)
uv run python main.py --show-ir queries/08_comparison_equal.gsql

# Mostra IR senza ottimizzazioni (per debug)
uv run python main.py --show-ir --no-optimize queries/08_comparison_equal.gsql

# Mostra IR per query inline
uv run python main.py --show-ir "RIPIGLIAMMO nome MMIEZ 'A \"guaglioni.csv\" arò eta > 18 E zona = \"Scampia\""
```

### Note sulle Ottimizzazioni
**Le ottimizzazioni LLVM IR sono abilitate di default** in tutte le esecuzioni del main.

- **Default**: Ottimizzazioni **ON** (module verification, target init)
- **Testing**: Ottimizzazioni **OFF** (`optimize=False` nei test per IR predicibile)
- **Disabilita**: Usa flag `--no-optimize` per debug



### Analizza Type Inference
```bash
# Esegui query e vedi tipi inferiti (se logging abilitato)
uv run python main.py queries/01_select_simple.gsql 2>&1 | grep -i "type"

# Analizza tipi per CSV specifico
uv run python -c "
from src.llvm_codegen import LLVMCodeGenerator
codegen = LLVMCodeGenerator()
types = codegen._analyze_csv_types('guaglioni.csv')
for col, typ in types.items():
    print(f'{col}: {typ.__name__}')
"
```

### Debug Errori
```bash
# Mostra tutti gli errori (stderr)
uv run python main.py queries/invalid.gsql 2>&1

# Test con traceback completo
uv run pytest tests/ -v --tb=long

# Test con pdb debugger su failure
uv run pytest tests/ --pdb
```

---

## 📊 Coverage e Report

### Genera Report Coverage
```bash
# Report testuale completo
uv run pytest tests/ --cov=src --cov-report=term-missing

# Report HTML interattivo
uv run pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html

# Report JSON (per CI/CD)
uv run pytest tests/ --cov=src --cov-report=json
cat coverage.json
```

