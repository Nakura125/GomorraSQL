"""
Visitor Pattern per AST
Base class per implementare operazioni su nodi AST
"""

from abc import ABC, abstractmethod
from .ast_nodes import SelectQuery, Comparison, NullCheck, LogicOp, Condition


class ASTVisitor(ABC):
    """Visitor astratto per navigare l'AST"""
    
    @abstractmethod
    def visit_select_query(self, node: SelectQuery):
        """Visita nodo SelectQuery"""
        pass
    
    @abstractmethod
    def visit_comparison(self, node: Comparison):
        """Visita nodo Comparison"""
        pass
    
    @abstractmethod
    def visit_null_check(self, node: NullCheck):
        """Visita nodo NullCheck"""
        pass
    
    @abstractmethod
    def visit_logic_op(self, node: LogicOp):
        """Visita nodo LogicOp"""
        pass
    
    def visit(self, node):
        """Dispatcher che chiama il metodo visit appropriato"""
        if isinstance(node, SelectQuery):
            return self.visit_select_query(node)
        elif isinstance(node, Comparison):
            return self.visit_comparison(node)
        elif isinstance(node, NullCheck):
            return self.visit_null_check(node)
        elif isinstance(node, LogicOp):
            return self.visit_logic_op(node)
        else:
            raise TypeError(f"Tipo di nodo non supportato: {type(node)}")
