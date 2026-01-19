from lark import Lark, UnexpectedInput, UnexpectedToken, Transformer, Token
from dataclasses import dataclass
from typing import List, Union, Optional

# ==========================================
# 1. Nodi AST (Strutture Dati)
# ==========================================

@dataclass
class SelectQuery:
    """Rappresenta una query SELECT completa"""
    columns: Union[List[str], str]  # Lista colonne o "*"
    tables: List[str]                # Tabelle (FROM + JOIN)
    where: Optional['Condition'] = None

@dataclass
class Condition:
    """Condizione generica (base class)"""
    pass

@dataclass
class Comparison(Condition):
    """Confronto: column OP value"""
    left: str
    operator: str
    right: Union[str, int, float, bool]

@dataclass
class NullCheck(Condition):
    """Controllo NULL: column IS [NOT] NULL"""
    column: str
    is_null: bool  # True = IS NULL, False = IS NOT NULL

@dataclass
class LogicOp(Condition):
    """Operatore logico: AND/OR"""
    operator: str  # 'AND' o 'OR'
    conditions: List[Condition]

# ==========================================
# 2. Transformer (Parse Tree → AST)
# ==========================================

class ToAstTransformer(Transformer):
    """Trasforma il Parse Tree verboso in un AST pulito"""
    
    def start(self, items):
        """start: select_stmt"""
        return items[0]
    
    def select_stmt(self, items):
        """select_stmt: SELECT_KW projection from_clause [where_clause]"""
        # items[0] = Token SELECT_KW (da scartare)
        # items[1] = projection
        # items[2] = from_clause
        # items[3] = where_clause (opzionale)
        
        projection = items[1]
        from_clause = items[2]
        where = items[3] if len(items) > 3 else None
        
        return SelectQuery(
            columns=projection,
            tables=from_clause,
            where=where
        )
    
    def projection(self, items):
        """projection: select_all | column_list"""
        return items[0]
    
    def select_all(self, items):
        """projection: ALL_COLS -> '*'"""
        return "*"
    
    def column_list(self, items):
        """column_list: column_ref ("," column_ref)*"""
        return items  # Lista di stringhe (nomi colonne)
    
    def column_ref(self, items):
        """column_ref: identifier"""
        return items[0]
    
    def identifier(self, items):
        """identifier: CNAME"""
        return str(items[0])
    
    def from_clause(self, items):
        """from_clause: FROM_KW table_ref join_clause*"""
        # items[0] = Token FROM_KW (da scartare)
        # items[1+] = tabelle
        return [item for item in items[1:] if item is not None]
    
    def join_clause(self, items):
        """join_clause: JOIN_KW table_ref"""
        # Ritorna solo il nome della tabella (salta JOIN_KW)
        return items[0] if items else None
    
    def table_ref(self, items):
        """table_ref: identifier | ESCAPED_STRING"""
        table_name = str(items[0])
        # Rimuove le virgolette se presenti
        return table_name.strip('"')
    
    def where_clause(self, items):
        """where_clause: WHERE_KW condition"""
        # items[0] = Token WHERE_KW (da scartare)
        # items[1] = condizione
        return items[1]
    
    def comparison(self, items):
        """comparison: identifier COMP_OP value | identifier COMP_OP identifier"""
        left = items[0]
        operator = str(items[1])
        right = items[2]
        
        return Comparison(left=left, operator=operator, right=right)
    
    def is_null(self, items):
        """null_check: identifier IS_KW NULL_KW"""
        column = items[0]
        return NullCheck(column=column, is_null=True)
    
    def is_not_null(self, items):
        """null_check: identifier IS_NOT_KW NULL_KW"""
        column = items[0]
        return NullCheck(column=column, is_null=False)
    
    def logic_term(self, items):
        """Gestisce condizioni AND"""
        if len(items) == 1:
            return items[0]
        return LogicOp(operator='AND', conditions=items)
    
    def condition(self, items):
        """Gestisce condizioni OR"""
        if len(items) == 1:
            return items[0]
        return LogicOp(operator='OR', conditions=items)
    
    def value(self, items):
        """value: ESCAPED_STRING | SIGNED_NUMBER | "true" | "false" """
        val = items[0]
        
        # Conversione tipo appropriato
        if isinstance(val, Token):
            if val.type == 'ESCAPED_STRING':
                return str(val).strip('"')
            elif val.type == 'SIGNED_NUMBER':
                # Converte in int o float
                num_str = str(val)
                return int(num_str) if '.' not in num_str else float(num_str)
        
        # Gestione booleani
        val_str = str(val).lower()
        if val_str == 'true':
            return True
        elif val_str == 'false':
            return False
        
        return val

# ==========================================
# 3. Funzione Principale
# ==========================================

def genera_ast(file_grammatica, codice_gomorra):
    """
    Carica la grammatica da file e genera l'AST per il codice fornito.
    """
    # 1. Caricamento della Grammatica (Specifiche Sintattiche)
    try:
        with open(file_grammatica, "r") as f:
            grammar_text = f.read()
    except FileNotFoundError:
        print(f"ERRORE: Non trovo il file della grammatica '{file_grammatica}'")
        return None

    # 2. Creazione del Parser (Il motore che usa la tua grammatica)
    # start='start' indica la regola iniziale definita nel tuo file .lark
    # parser='lalr' è l'algoritmo di parsing veloce consigliato da Lark
    parser = Lark(grammar_text, start='start', parser='lalr')

    print(f"--- ANALISI SINTATTICA IN CORSO ---")
    
    try:
        # 3. Generazione del Parse Tree
        parse_tree = parser.parse(codice_gomorra)
        
        # 4. Trasformazione in AST semplificato
        print(f"--- TRASFORMAZIONE IN AST ---")
        transformer = ToAstTransformer()
        ast = transformer.transform(parse_tree)
        
        return ast

    except UnexpectedInput as e:
        # Gestione errori come richiesto dai requisiti di robustezza
        print(f"ERRORE SINTATTICO: C'è qualcosa che non va alla riga {e.line}, colonna {e.column}.")
        print(f"Contesto: {e.get_context(codice_gomorra)}")
        return None

# --- TEST ---
if __name__ == "__main__":
    # Assicurati di avere il file 'gomorra.lark' nella stessa cartella
    FILE_GRAMMATICA = "gomorrasql_grammar.txt"
    
    # Una query di esempio conforme alla tua grammatica
    QUERY_TEST = """
    RIPIGLIAMMO nome, eta 
    MMIEZ 'A "guaglioni.csv" 
    arò eta > 18 
    """
    

    ast = genera_ast(FILE_GRAMMATICA, QUERY_TEST)

    if ast:
        print("\n--- AST SEMPLIFICATO ---")
        print(ast)
        print("\n--- DETTAGLI ---")
        print(f"Colonne: {ast.columns}")
        print(f"Tabelle: {ast.tables}")
        if ast.where:
            print(f"Condizione WHERE: {ast.where}")