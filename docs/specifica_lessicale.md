# Specifica Lessicale - GomorraSQL

## 1. Parole Chiave (Keywords)

Le seguenti parole riservate costituiscono il vocabolario del linguaggio:

| Token | Lessema | Significato SQL | Descrizione |
|-------|---------|-----------------|-------------|
| `RIPIGLIAMM` | RIPIGLIAMM | SELECT | Proiezione di colonne |
| `NMIEZ` | NMIEZ | FROM | Sorgente dati (file CSV) |
| `A` | A | WHERE | Clausola di filtro |
| `STAMM_ACCISI` | STAMM_ACCISI | ; | Terminatore di query |

## 2. Operatori di Confronto

| Token | Lessema | Significato | Descrizione |
|-------|---------|-------------|-------------|
| `EGAL` | EGAL | = | Uguaglianza |
| `NON E COSA` | NON E COSA | ≠, != | Disuguaglianza |
| `CHIU ASSAI` | CHIU ASSAI | > | Maggiore |
| `CHIU POC` | CHIU POC | < | Minore |
| `EGAL O CHIU` | EGAL O CHIU | ≥ | Maggiore o uguale |
| `EGAL O POC` | EGAL O POC | ≤ | Minore o uguale |

## 3. Simboli Speciali

| Token | Lessema | Descrizione |
|-------|---------|-------------|
| `COMMA` | , | Separatore di colonne |
| `ASTERISK` | * | Selezione di tutte le colonne |

## 4. Identificatori

**Pattern**: `[a-zA-Z_][a-zA-Z0-9_]*`

Gli identificatori sono utilizzati per:
- Nomi di colonne (es. `nome`, `cognome`, `eta`)
- Riferimenti a campi del CSV

**Regole**:
- Iniziano con una lettera (maiuscola o minuscola) o underscore
- Possono contenere lettere, cifre e underscore
- Case-sensitive
- Non possono coincidere con parole chiave

**Esempi validi**: `nome`, `eta`, `data_nascita`, `ID_utente`

**Esempi non validi**: `3nome`, `RIPIGLIAMM`, `cognome-utente`

## 5. Letterali

### 5.1 Stringhe (STRING)

**Pattern**: `"[^"]*"`

Sequenze di caratteri racchiuse tra doppi apici.

**Esempi**:
- `"guaglioni.csv"`
- `"Mario"`
- `"Via Toledo 123"`

### 5.2 Numeri (NUMBER)

**Pattern**: `[0-9]+(\.[0-9]+)?`

Numeri interi o decimali.

**Esempi**:
- `18` (intero)
- `25.5` (decimale)
- `100`
- `3.14159`

**Note**: 
- Supporto opzionale per numeri negativi con prefisso `-`
- I decimali usano il punto `.` come separatore

## 6. Whitespace e Commenti

### 6.1 Whitespace

I seguenti caratteri sono considerati whitespace e ignorati dal lexer:
- Spazio ` `
- Tab `\t`
- Newline `\n`
- Carriage return `\r`

### 6.2 Commenti (Estensione Opzionale)

Non previsti nella versione base, ma possono essere aggiunti:

```
// Commento singola linea (stile C++)
/* Commento
   multi-linea */
```

## 7. Tabella Riassuntiva Token

```
TOKEN_TYPE          REGEX/PATTERN                    PRIORITÀ
─────────────────────────────────────────────────────────────
RIPIGLIAMM          "RIPIGLIAMM"                     1 (keyword)
NMIEZ               "NMIEZ"                          1 (keyword)
A                   "A"                              1 (keyword)
STAMM_ACCISI        "STAMM_ACCISI"                   1 (keyword)
EGAL                "EGAL"                           2 (operator)
NON_E_COSA          "NON E COSA"                     2 (operator)
CHIU_ASSAI          "CHIU ASSAI"                     2 (operator)
CHIU_POC            "CHIU POC"                       2 (operator)
EGAL_O_CHIU         "EGAL O CHIU"                    2 (operator)
EGAL_O_POC          "EGAL O POC"                     2 (operator)
COMMA               ","                              3 (symbol)
ASTERISK            "*"                              3 (symbol)
STRING              "[^"]*"                          4 (literal)
NUMBER              [0-9]+(\.[0-9]+)?                5 (literal)
IDENTIFIER          [a-zA-Z_][a-zA-Z0-9_]*           6 (identifier)
WHITESPACE          [ \t\n\r]+                       7 (ignored)
```

## 8. Note Implementative

### 8.1 Gestione Ambiguità

Gli operatori multi-parola (es. `NON E COSA`, `CHIU ASSAI`) richiedono attenzione nel lexer:
- Devono essere riconosciuti come token singoli
- La presenza di spazi interni richiede un pattern specifico o tokenizzazione multi-step

### 8.2 Ordine di Matching

Il lexer deve rispettare la priorità:
1. Keywords (più lungo prima: `STAMM_ACCISI` prima di `A`)
2. Operatori multi-parola
3. Simboli speciali
4. Letterali
5. Identificatori (ultima opzione per evitare match con keyword)

### 8.3 Esempi di Tokenizzazione

**Input**:
```sql
RIPIGLIAMM nome, eta NMIEZ "dati.csv" A eta CHIU ASSAI 18 STAMM_ACCISI
```

**Output Tokens**:
```
[RIPIGLIAMM] [IDENTIFIER:nome] [COMMA] [IDENTIFIER:eta] [NMIEZ] 
[STRING:"dati.csv"] [A] [IDENTIFIER:eta] [CHIU_ASSAI] [NUMBER:18] 
[STAMM_ACCISI]
```

## 9. Estensioni Future

Possibili aggiunte al lessico:
- Operatori logici: `E` (AND), `O` (OR), `NUN` (NOT)
- Operatori aritmetici: `+`, `-`, `*`, `/`
- Funzioni aggregate: `CUNTA` (COUNT), `SOMMA` (SUM)
- Join: `APPICCECA` (JOIN)
