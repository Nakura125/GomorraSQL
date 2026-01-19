# 🍕 GomorraSQL - Query di Esempio

Questa cartella contiene **10 query di esempio** che dimostrano tutte le funzionalità di GomorraSQL.

## 📋 Indice Query

| File | Descrizione | Funzionalità Dimostrate |
|------|-------------|-------------------------|
| `01_select_simple.gsql` | SELECT base con WHERE | SELECT, FROM, WHERE, operatore > |
| `02_where_complex.gsql` | WHERE con AND/OR | Operatori logici E/O, parentesi |
| `03_join_cartesian.gsql` | JOIN semplice | pesc e pesc (JOIN), prodotto cartesiano |
| `04_join_with_where.gsql` | JOIN + filtro | JOIN + WHERE combinati |
| `05_join_inner.gsql` | INNER JOIN simulato | Confronto colonna-colonna, disambiguazione |
| `06_null_check_is_null.gsql` | IS NULL | Operatore "è nisciun" |
| `07_null_check_is_not_null.gsql` | IS NOT NULL | Operatore "nun è nisciun" |
| `08_comparison_equal.gsql` | Confronto = | Uguaglianza esatta |
| `09_comparison_not_equal.gsql` | Confronto <> | Diverso da |
| `10_join_advanced.gsql` | Query complessa | JOIN + WHERE complesso + match colonne |

---

## 🚀 Come Eseguire le Query

### Metodo 1: Da riga di comando
```bash
# Singola query
uv run python main.py queries/01_select_simple.gsql

# Esegui tutte le query
for file in queries/*.gsql; do
    echo "=== $file ==="
    uv run python main.py "$file"
    echo ""
done

# Oppure usa lo script dedicato
uv run python run_all_examples.py
```

### Metodo 2: Script Python
```python
from src.compiler import GomorraCompiler

compiler = GomorraCompiler(data_dir="data")

# Esegui query da file
results = compiler.run_file("queries/05_join_inner.gsql")

# Stampa risultati
for row in results:
    print(row)
```

---

## 📊 Dataset Disponibili

### `guaglioni.csv`
```csv
nome,zona,eta
Ciro,Secondigliano,35
Genny,Scampia,19
O_Track,Centro,17
SangueBlu,Forcella,25
```

### `ruoli.csv`
```csv
id,nome,ruolo
1,Ciro,Boss
2,Genny,Boss
3,O_Track,Soldato
4,SangueBlu,Capodecina
```

### `guaglioni_null.csv`
```csv
nome,zona,eta
Ciro,Secondigliano,35
Genny,,19
O_Track,Centro,17
Patrizia,,
```
(Contiene valori NULL/vuoti per testare "è nisciun")

---

## 💡 Esempi di Output

### Query 1 - SELECT semplice
```bash
$ uv run python main.py queries/01_select_simple.gsql

--- ESECUZIONE QUERY ---
✓ Query eseguita: 3 righe restituite

Risultati:
{'nome': 'Ciro', 'eta': '35'}
{'nome': 'Genny', 'eta': '19'}
{'nome': 'SangueBlu', 'eta': '25'}
```

### Query 5 - INNER JOIN
```bash
$ uv run python main.py queries/05_join_inner.gsql

--- ESECUZIONE QUERY ---
✓ Query eseguita: 4 righe restituite

Risultati:
{'nome': 'Ciro', 'nome_2': 'Ciro', 'zona': 'Secondigliano', 'ruolo': 'Boss'}
{'nome': 'Genny', 'nome_2': 'Genny', 'zona': 'Scampia', 'ruolo': 'Boss'}
{'nome': 'O_Track', 'nome_2': 'O_Track', 'zona': 'Centro', 'ruolo': 'Soldato'}
{'nome': 'SangueBlu', 'nome_2': 'SangueBlu', 'zona': 'Forcella', 'ruolo': 'Capodecina'}
```

### Query 6 - NULL check
```bash
$ uv run python main.py queries/06_null_check_is_null.gsql

--- ESECUZIONE QUERY ---
✓ Query eseguita: 2 righe restituite

Risultati:
{'nome': 'Genny', 'zona': '', 'eta': '19'}
{'nome': 'Patrizia', 'zona': '', 'eta': ''}
```

---

## 🎯 Funzionalità Testate

| Funzionalità | Query di Test |
|--------------|---------------|
| SELECT base | 01, 08, 09 |
| WHERE semplice | 01, 04 |
| WHERE complesso (AND/OR) | 02, 10 |
| JOIN (prodotto cartesiano) | 03 |
| JOIN + WHERE | 04 |
| JOIN con match colonne | 05, 10 |
| IS NULL | 06 |
| IS NOT NULL | 07 |
| Operatori comparazione | 01-10 (tutti) |
| Disambiguazione colonne | 05, 10 |

---

## 📝 Note Tecniche

1. **Type Inference**: Il compilatore analizza automaticamente i tipi CSV (int, float, string)
2. **Generators**: JOIN scalabile con memoria O(1) grazie a Python generators
3. **Fallback**: Se JIT LLVM fallisce, usa esecuzione Python automatica
4. **LLVM IR**: Ogni query genera codice IR ottimizzato (`icmp` per int, `fcmp` per float)

---

## 🔬 Per Sviluppatori

### Vedere l'LLVM IR generato
Modifica `main.py` per stampare l'IR:
```python
compiler = GomorraCompiler(data_dir="data")
results = compiler.run_file("queries/01_select_simple.gsql")

# Stampa IR
print(compiler.codegen.module)
```

### Debug mode
Aggiungi `verbose=True` al compiler per vedere tutti gli step della pipeline:
```python
compiler = GomorraCompiler(data_dir="data", verbose=True)
```

---

## ✅ Validazione

Tutte le query sono testate nella suite di test:
```bash
# Esegui test completo
uv run pytest tests/ -v --cov=src

# 19 test totali, 100% success rate
```
