"""
Transformer: Parse Tree → AST
Converte l'albero verboso di Lark in strutture dati pulite
"""

from lark import Transformer, Token
from .ast_nodes import SelectQuery, Comparison, NullCheck, LogicOp


class ToAstTransformer(Transformer):
    """Trasforma il Parse Tree verboso in un AST pulito"""
    
    def start(self, items):
        """start: select_stmt"""
        return items[0]
    
    def select_stmt(self, items):
        """select_stmt: SELECT_KW projection from_clause [where_clause]"""
        
        
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
        return [item for item in items[1:] if item is not None]
    
    def join_clause(self, items):
        """join_clause: JOIN_KW table_ref"""
        return items[1] if len(items) > 1 else None
    
    def table_ref(self, items):
        """table_ref: identifier | ESCAPED_STRING"""
        table_name = str(items[0])
        # Rimuove le virgolette se presenti
        return table_name.strip('"')
    
    def where_clause(self, items):
        """where_clause: WHERE_KW condition"""
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
        # Filtra via i token AND_KW, mantieni solo le condizioni
        conditions = [item for item in items if not isinstance(item, Token)]
        if len(conditions) == 1:
            return conditions[0]
        return LogicOp(operator='AND', conditions=conditions)
    
    def condition(self, items):
        """Gestisce condizioni OR"""
        # Filtra via i token OR_KW, mantieni solo le condizioni
        conditions = [item for item in items if not isinstance(item, Token)]
        if len(conditions) == 1:
            return conditions[0]
        return LogicOp(operator='OR', conditions=conditions)
    
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
