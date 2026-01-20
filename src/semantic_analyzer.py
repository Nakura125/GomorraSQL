"""
Semantic Analyzer: Analisi Semantica
Valida che l'AST sia semanticamente corretto
"""

import csv
from pathlib import Path
from typing import Set, Dict, List
from .ast_nodes import SelectQuery, Comparison, NullCheck, LogicOp


class SemanticError(Exception):
    """Errore semantico nella query"""
    pass


class SemanticAnalyzer:
    """Analizzatore semantico per GomorraSQL"""
    
    def __init__(self, data_dir: str = "data"):
        """
        Inizializza l'analyzer
        
        Args:
            data_dir: Directory contenente i file CSV
        """
        self.data_dir = Path(data_dir)
        self.table_schemas: Dict[str, Set[str]] = {}
    
    def _load_table_schema(self, table_name: str) -> Set[str]:
        """Carica le colonne di una tabella CSV"""
        if table_name in self.table_schemas:
            return self.table_schemas[table_name]
        
        csv_path = self.data_dir / table_name
        
        if not csv_path.exists():
            raise SemanticError(f"Tabella '{table_name}' non trovata")
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                columns = set(next(reader))
                self.table_schemas[table_name] = columns
                return columns
        except Exception as e:
            raise SemanticError(f"Errore leggendo la tabella '{table_name}': {e}")
    
    def analyze(self, ast: SelectQuery) -> bool:
        """
        Analizza semanticamente l'AST
        
        Args:
            ast: AST da validare
            
        Returns:
            True se valido
            
        Raises:
            SemanticError: se ci sono errori semantici
        """
        # 1. Carica schemi delle tabelle
        all_columns: Set[str] = set()
        disambiguated_columns: Set[str] = set()  # Colonne con suffissi _2
        
        for i, table in enumerate(ast.tables):
            columns = self._load_table_schema(table)
            
            # Se è JOIN, aggiungi anche versioni disambiguate
            if len(ast.tables) > 1 and i > 0:
                for col in columns:
                    if col in all_columns:
                        # Colonna duplicata, aggiungi versione con suffisso
                        disambiguated_columns.add(f"{col}_2")
            
            all_columns.update(columns)
        
        # Aggiungi colonne disambiguate
        all_columns.update(disambiguated_columns)
        
        # 2. Valida proiezione (SELECT)
        if ast.columns != "*":
            for col in ast.columns:
                if col not in all_columns:
                    raise SemanticError(
                        f"Colonna '{col}' non esiste nelle tabelle: {ast.tables}"
                    )
        
        # 3. Valida condizioni WHERE
        if ast.where:
            self._validate_condition(ast.where, all_columns)
        
        return True
    
    def _validate_condition(self, condition, available_columns: Set[str]):
        """Valida ricorsivamente le condizioni"""
        if isinstance(condition, Comparison):
            # Valida colonna sinistra
            if condition.left not in available_columns:
                raise SemanticError(
                    f"Colonna '{condition.left}' non esiste nella WHERE"
                )
            
            # Valida colonna destra se è un identificatore
            if isinstance(condition.right, str) and condition.right not in available_columns:
                # Potrebbe essere un valore stringa, non un errore
                pass
        
        elif isinstance(condition, NullCheck):
            if condition.column not in available_columns:
                raise SemanticError(
                    f"Colonna '{condition.column}' non esiste nel NULL check"
                )
        
        elif isinstance(condition, LogicOp):
            for cond in condition.conditions:
                self._validate_condition(cond, available_columns)
