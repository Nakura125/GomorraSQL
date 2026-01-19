# 🚀 Comandi Utili - GomorraSQL

Guida rapida ai comandi per esecuzione, testing e debugging del compilatore GomorraSQL.

---

## ▶️ Esecuzione Query

### Query da File
```bash
# SELECT semplice
uv run python main.py queries/01_select_simple.gsql

# Query con confronto (equal)
uv run python main.py queries/08_comparison_equal.gsql

# Esegui tutte le query di esempio
uv run python run_all_examples.py
```

### Query Inline (da Terminale)
```bash
# SELECT inline
uv run python main.py "RIPIGLIAMMO nome MMIEZ 'A \"guaglioni.csv\""

# SELECT con WHERE
uv run python main.py "RIPIGLIAMMO nome, zona MMIEZ 'A \"guaglioni.csv\" arò eta > 18"

# Query complessa con AND
uv run python main.py "RIPIGLIAMMO nome MMIEZ 'A \"guaglioni.csv\" arò eta > 18 E zona = \"Scampia\""

# Query con NULL check
uv run python main.py "RIPIGLIAMMO nome MMIEZ 'A \"guaglioni.csv\" arò nome nun è nisciun"

# Query con JOIN
uv run python main.py "RIPIGLIAMMO nome, token MMIEZ 'A \"guaglioni.csv\" pesc e pesc \"lexer.csv\""
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
# Mostra LLVM IR per query specifica
uv run python main.py queries/08_comparison_equal.gsql 2>&1 | grep -A 50 "LLVM IR GENERATO"

# Mostra IR per query con WHERE complessa
uv run python main.py "RIPIGLIAMMO nome MMIEZ 'A \"guaglioni.csv\" arò eta > 18 E zona = \"Scampia\"" 2>&1 | grep -A 50 "LLVM IR"
```

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

### Metriche Progetto
```bash
# Conta linee di codice
find src/ -name "*.py" -exec wc -l {} + | tail -1

# Conta test
grep -r "^def test_" tests/ | wc -l

# Lista tutti i test
pytest --collect-only tests/
```

---

## 📦 Installazione e Setup

### Prima Installazione
```bash
# Clona repository
git clone https://github.com/Nakura125/PostGomSQL.git
cd PostGomSQL

# Installa dipendenze con uv
uv sync

# Verifica installazione
uv run python --version
uv pip list
```

### Verifica Funzionamento
```bash
# Test quick check
uv run pytest tests/test_compiler.py::test_select_all_no_where -v

# Esegui query di test
uv run python main.py queries/01_select_simple.gsql

# Esegui tutte le query
uv run python run_all_examples.py
```

---

## 🛠️ Sviluppo

### Formattazione e Linting
```bash
# Formatta codice con black (se installato)
black src/ tests/

# Linting con flake8
flake8 src/ tests/

# Type checking con mypy
mypy src/
```

### Watch Mode
```bash
# Riesegui test automaticamente su modifiche (richiede pytest-watch)
uv pip install pytest-watch
ptw tests/ -- -v
```

---

## 🧹 Pulizia

### Rimuovi Cache
```bash
# Rimuovi __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} +

# Rimuovi cache pytest e coverage
rm -rf .pytest_cache .coverage htmlcov/

# Pulizia completa
rm -rf .venv __pycache__ .pytest_cache .coverage htmlcov/
find . -type d -name "__pycache__" -exec rm -rf {} +
```

### Reset Ambiente
```bash
# Reset completo e reinstallazione
rm -rf .venv
uv sync
uv run pytest tests/ -v
```

---

## 🔗 Collegamenti Utili

- **Repository**: https://github.com/Nakura125/PostGomSQL
- **Documentazione Completa**: [docs/SPECIFICA_COMPLETA.md](docs/SPECIFICA_COMPLETA.md)
- **README**: [README.md](README.md)

---

## 💡 Workflow Consigliato

### 1. Sviluppo Feature
```bash
# Esegui query di test
uv run python main.py "RIPIGLIAMMO nome MMIEZ 'A \"guaglioni.csv\""

# Controlla LLVM IR generato
uv run python main.py queries/08_comparison_equal.gsql 2>&1 | grep -A 50 "LLVM IR GENERATO"

# Esegui test correlati
uv run pytest tests/test_compiler.py -v
```

### 2. Pre-Commit
```bash
# Esegui tutti i test
uv run pytest tests/ -v

# Verifica coverage
uv run pytest tests/ --cov=src --cov-report=term-missing -v 2>&1 | head -80

# Esegui tutti gli esempi
uv run python run_all_examples.py
```

### 3. Debugging Problema
```bash
# Test specifico con traceback
uv run pytest tests/test_compiler.py::test_problematico -v --tb=long

# Query problematica con stderr
uv run python main.py "query problematica" 2>&1

# Analizza IR generato
uv run python main.py queries/problematica.gsql 2>&1 | grep -A 100 "LLVM IR"
```

---

**Ultimo Aggiornamento**: 18 gennaio 2026
