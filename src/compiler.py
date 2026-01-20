"""
Compiler: Pipeline Completa
Coordina tutte le fasi: parsing → semantic analysis → execution
"""

from .parser import GomorraParser
from .semantic_analyzer import SemanticAnalyzer, SemanticError
from .llvm_codegen import LLVMCodeGenerator
from typing import List, Dict, Any


class GomorraCompiler:
    """Compilatore completo per GomorraSQL"""
    
    def __init__(self, grammar_file: str = None, data_dir: str = "data", optimize: bool = True):
        """
        Inizializza il compilatore
        
        Args:
            grammar_file: Path alla grammatica (opzionale)
            data_dir: Directory con i file CSV
            optimize: Se True, applica ottimizzazioni LLVM IR (default: True)
        """
        self.parser = GomorraParser(grammar_file)
        self.semantic_analyzer = SemanticAnalyzer(data_dir)
        self.codegen = LLVMCodeGenerator(data_dir, optimize=optimize)
    
    def compile_and_run(self, code: str) -> List[Dict[str, Any]]:
        """
        Esegue la pipeline completa: parsing → analisi → esecuzione
        
        Args:
            code: Query GomorraSQL
            
        Returns:
            Risultati della query
            
        Raises:
            SyntaxError: Errore di sintassi nel parsing
            SemanticError: Errore semantico nell'analisi
        """
        # 1. Parsing (solleva SyntaxError se fallisce)
        ast = self.parser.parse(code)
        
        # 2. Analisi Semantica (solleva SemanticError se fallisce)
        self.semantic_analyzer.analyze(ast)
        
        # 3. Esecuzione con LLVM Code Generator
        results = self.codegen.generate_and_execute(ast)
        
        return results
    
    def run_file(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Esegue una query da file
        
        Args:
            filepath: Path al file .gsql
            
        Returns:
            Risultati della query
        """
        with open(filepath, 'r') as f:
            code = f.read()
        
        return self.compile_and_run(code)
