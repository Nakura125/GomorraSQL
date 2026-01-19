"""
Nodi dell'Abstract Syntax Tree (AST)
Strutture dati che rappresentano le query parsed
"""

from dataclasses import dataclass
from typing import List, Union, Optional, Tuple

# ==========================================
# Query Nodes
# ==========================================

@dataclass
class SelectQuery:
    """Rappresenta una query SELECT completa"""
    columns: Union[List[str], str]  # Lista colonne o "*"
    tables: List[str]                # Tabelle (FROM + JOIN)
    where: Optional['Condition'] = None

# ==========================================
# Condition Nodes
# ==========================================

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
