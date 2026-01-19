# Report sull'Utilizzo dell'Intelligenza Artificiale

**Progetto**: GomorraSQL Compiler  
**Autore**: Angelo Alberico  
**Matricola**: NF22500104  
**Corso**: Implementazione di Linguaggi di Programmazione  
**Data**: Gennaio 2026

---

## 1. Introduzione

Durante lo sviluppo del compilatore **GomorraSQL**, l'intelligenza artificiale (GitHub Copilot) è stata utilizzata come strumento di supporto in tutte le fasi del progetto, dalla progettazione alla documentazione finale.

---

## 2. Tipologie di Utilizzo

### 2.1 Sviluppo Codice

L'AI ha assistito nella scrittura del codice per tutti i moduli principali del compilatore sia in formato Agent che formato inline:
- **Backend LLVM**: Generazione IR parametrico, type inference
- **Semantic Analyzer**: Validazione query, type checking, disambiguazione JOIN
- **Bug fixing**: Identificazione e risoluzione rapida di problemi critici (es. non-determinismo parametri con `set()` → `dict.fromkeys()`)


### 2.2 Generazione delle Specifiche

L'AI ha assistito nella creazione della documentazione tecnica:
- `SPECIFICA_COMPLETA.md`: Struttura documento, tabelle comparative, esempi LLVM IR
- `README.md`: Formattazione e organizzazione contenuti


### 2.3 Generazione di Test

L'AI ha assistito nella generazione della test suite in maniera guidata:
- Test unitari per parser, semantic analyzer, LLVM codegen
- Test per edge cases (NULL checks, JOIN, type inference)
- Test end-to-end con file CSV reali
- **Risultato finale**: 19 test, 82.39% coverage


### 2.4 Spiegazioni di Argomenti Tecnici

L'AI ha fornito spiegazioni approfondite su temi complessi:
- **ARM64 Architecture**: Crash MCJIT dovuto a W^X memory protection e cache incoherency (D-Cache/I-Cache)
---

## 3. Efficacia e Vantaggi
- **Code coverage**: 82.39%
- **Best practices**: Type hints, docstrings, error handling, logging strutturato
- **Testing**: 19 test funzionanti al primo tentativo


---

## 4. Inconvenienti e Limitazioni
- **Allucinazioni API**: Suggerimenti di API inesistenti richiedono verifica con documentazione ufficiale
- **Context window limitato**: File >500 righe richiedono ri-lettura frequente
- **Debugging multi-step**: Problemi complessi (es. crash MCJIT ARM64) richiedono guida umana



