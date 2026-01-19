"""
Parser: Analisi Sintattica
Carica la grammatica e genera l'AST dal codice GomorraSQL
"""

from lark import Lark, UnexpectedInput
from pathlib import Path
from .transformer import ToAstTransformer


class GomorraParser:
    """Parser principale per GomorraSQL"""
    
    def __init__(self, grammar_file: str = None):
        """
        Inizializza il parser con la grammatica
        
        Args:
            grammar_file: Path al file .lark (default: gomorrasql_grammar.txt nella root)
        """
        if grammar_file is None:
            # Cerca la grammatica nella directory del progetto
            project_root = Path(__file__).parent.parent
            grammar_file = project_root / "gomorrasql_grammar.txt"
        
        try:
            with open(grammar_file, "r") as f:
                grammar_text = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"ERRORE: Non trovo il file della grammatica '{grammar_file}'"
            )
        
        # Crea il parser Lark
        self.parser = Lark(grammar_text, start='start', parser='lalr')
        self.transformer = ToAstTransformer()
    
    def parse(self, code: str):
        """
        Esegue il parsing del codice GomorraSQL
        
        Args:
            code: Stringa contenente la query GomorraSQL
            
        Returns:
            AST (SelectQuery) se il parsing ha successo, None altrimenti
        """
        print(f"--- ANALISI SINTATTICA IN CORSO ---")
        
        try:
            # 1. Parsing (genera Parse Tree)
            parse_tree = self.parser.parse(code)
            
            # 2. Trasformazione (Parse Tree → AST)
            print(f"--- TRASFORMAZIONE IN AST ---")
            ast = self.transformer.transform(parse_tree)
            
            return ast
            
        except UnexpectedInput as e:
            # Gestione errori sintattici
            print(f"ERRORE SINTATTICO: C'è qualcosa che non va alla riga {e.line}, colonna {e.column}.")
            print(f"Contesto: {e.get_context(code)}")
            return None


def parse_file(filepath: str, grammar_file: str = None):
    """
    Utility per fare il parsing di un file GomorraSQL
    
    Args:
        filepath: Path al file .gsql
        grammar_file: Path alla grammatica (opzionale)
        
    Returns:
        AST parsed
    """
    with open(filepath, 'r') as f:
        code = f.read()
    
    parser = GomorraParser(grammar_file)
    return parser.parse(code)
