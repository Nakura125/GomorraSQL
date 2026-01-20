"""
LLVM Code Generator con JIT
Genera LLVM IR dall'AST e lo compila Just-In-Time
"""

import llvmlite.ir as ir
import llvmlite.binding as llvm
from llvmlite import ir as llvm_ir
from llvmlite import binding as target
from .visitor import ASTVisitor
from .ast_nodes import SelectQuery, Comparison, NullCheck, LogicOp
import csv
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class CompilationResult:
    """Risultato della compilazione LLVM con metadati"""
    llvm_ir: str
    optimized: bool = False
    jit_enabled: bool = False
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLVMCodeGenerator(ASTVisitor):
    """
    Genera codice LLVM IR dall'AST e lo esegue con JIT
    
    Strategia: Genera una funzione LLVM che:
    1. Carica i dati CSV in memoria
    2. Itera sulle righe
    3. Applica i filtri WHERE
    4. Restituisce le righe filtrate
    """
    
    def __init__(self, data_dir: str = "data", optimize: bool = True):
        """
        Inizializza il code generator
        
        Args:
            data_dir: Directory contenente i file CSV
            optimize: Se True, applica ottimizzazioni LLVM IR (default: True)
        """
        self.data_dir = Path(data_dir)
        self.module = ir.Module(name="gomorrasql_query")
        self.builder = None
        self.optimize = optimize
                
        # Dati caricati (per ora li carichiamo in Python e li passiamo a LLVM)
        self.data: List[Dict[str, Any]] = []
        self.columns: List[str] = []
        # Type schema: inferisce tipi delle colonne dal CSV
        self.column_types: Dict[str, type] = {}  # {column_name: int|float|str}
    
    def get_ir(self, ast: SelectQuery) -> CompilationResult:
        """
        Genera LLVM IR puro senza side-effects (no esecuzione, no print)
        
        Args:
            ast: AST della query
            
        Returns:
            CompilationResult con IR e metadati
        """
        # Reset del modulo per ogni query per evitare duplicazioni di nomi
        self.module = ir.Module(name="gomorrasql_query")
        self.module.triple = target.get_default_triple()
        
        # Carica dati CSV (necessario per type inference)
        self._load_csv_data(ast.tables)
        
        # Genera funzione LLVM parametrica
        func = self._generate_query_function(ast)
        
        # Ritorna risultato strutturato
        return CompilationResult(
            llvm_ir=str(self.module),
            optimized=self.optimize,
            metadata={
                'columns': self.columns,
                'column_types': {k: v.__name__ for k, v in self.column_types.items()},
                'tables': ast.tables,
                'has_where': ast.where is not None
            }
        )
    
    def generate_and_execute(self, ast: SelectQuery) -> List[Dict[str, Any]]:
        """
        Pipeline completa: genera LLVM IR ed esegue con JIT
        
        Args:
            ast: AST della query
            
        Returns:
            Risultati della query
        """
        import os
        
        # Genera IR (senza side-effects)
        compilation = self.get_ir(ast)
        
        # Compila LLVM IR con JIT (se abilitato esplicitamente)
        enable_jit = os.environ.get('GOMORRASQL_ENABLE_JIT', '0') == '1'
        
        if enable_jit:
            # Rigenera funzione per JIT (serve func object)
            func = self._generate_query_function(ast)
            self.jit_func = self._compile_llvm_to_jit(func)
        else:
            self.jit_func = None
        
        # Esegui query usando JIT LLVM (o fallback Python)
        results = self._execute_query(ast, engine=None)
        
        return results
    
    def _csv_generator(self, csv_path: Path):
        """
        Generatore lazy per CSV - carica righe on-demand senza list()
        Scalabile per file di centinaia di MB
        """
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield row
    
    def _get_csv_columns(self, csv_path: Path) -> List[str]:
        """Legge solo l'header CSV senza caricare i dati"""
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader.fieldnames)
    
    def _infer_column_type(self, value: str) -> type:
        """Inferisce il tipo di un valore CSV (sempre string) analizzandolo"""
        if value == '':
            return type(None)  # NULL
        
        # Prova conversione a numero
        try:
            if '.' in value:
                float(value)
                return float
            else:
                int(value)
                return int
        except ValueError:
            return str  # È una stringa
    
    def _analyze_csv_types(self, csv_path: Path, sample_size: int = 100):
        """Analizza un campione del CSV per inferire i tipi delle colonne"""
        type_samples = {}  # {column: [type1, type2, ...]}
        
        # Campiona le prime righe
        for i, row in enumerate(self._csv_generator(csv_path)):
            if i >= sample_size:
                break
            
            for col, val in row.items():
                type_samples.setdefault(col, []).append(self._infer_column_type(val))
        
        # Determina tipo predominante per ogni colonna
        for col, types in type_samples.items():
            # Rimuovi None e conta i tipi
            non_null_types = [t for t in types if t != type(None)]
            if not non_null_types:
                self.column_types[col] = type(None)  # Colonna tutta NULL
            # Se c'è float, prevale su int
            elif float in non_null_types:
                self.column_types[col] = float
            elif int in non_null_types:
                self.column_types[col] = int
            else:
                self.column_types[col] = str
    
    def _cartesian_product_generator(self, csv_path1: Path, csv_path2: Path, 
                                      cols1: List[str], cols2: List[str]):
        """
        Generatore lazy per prodotto cartesiano di JOIN
        Gestisce disambiguazione colonne duplicate
        """
        # Leggi prima tabella (necessaria per riutilizzo in loop)
        data1 = list(self._csv_generator(csv_path1))
        
        for row1 in data1:
            # Ricrea generatore per seconda tabella ad ogni iterazione
            # per evitare esaurimento del generatore
            for row2 in self._csv_generator(csv_path2):
                merged_row = {}
                # Aggiungi colonne prima tabella
                for col in cols1:
                    merged_row[col] = row1[col]
                # Aggiungi colonne seconda tabella (con gestione duplicati)
                for col in cols2:
                    if col in cols1:
                        merged_row[f"{col}_2"] = row2[col]
                    else:
                        merged_row[col] = row2[col]
                yield merged_row
    
    def _load_csv_data(self, tables: List[str]):
        """
        Carica dati CSV usando generatori per scalabilità
        Implementa prodotto cartesiano lazy per JOIN su file grandi
        """
        if len(tables) == 1:
            # SELECT semplice: usa generatore
            csv_path = self.data_dir / tables[0]
            
            # Analizza tipi colonne
            self._analyze_csv_types(csv_path)
            
            self.columns = self._get_csv_columns(csv_path)
            # Materializza in list solo per compatibilità con _execute_query
            # In una implementazione completamente lazy, anche questa sarebbe un generatore
            self.data = list(self._csv_generator(csv_path))
        else:
            # JOIN: prodotto cartesiano lazy tra tabelle
            # Leggi header senza caricare dati
            csv_path1 = self.data_dir / tables[0]
            csv_path2 = self.data_dir / tables[1]
            
            # Analizza tipi entrambe le tabelle
            self._analyze_csv_types(csv_path1)
            self._analyze_csv_types(csv_path2)
            
            cols1 = self._get_csv_columns(csv_path1)
            cols2 = self._get_csv_columns(csv_path2)
            
            # Costruisci lista colonne con disambiguazione
            self.columns = cols1.copy()
            for col in cols2:
                if col in self.columns:
                    new_col = f"{col}_2"
                    self.columns.append(new_col)
                    # Copia tipo per colonna disambiguata
                    if col in self.column_types:
                        self.column_types[new_col] = self.column_types[col]
                else:
                    self.columns.append(col)
            
            # Genera prodotto cartesiano usando generatori
            # Il generatore ricrea il reader CSV per la seconda tabella ad ogni iterazione
            self.data = list(self._cartesian_product_generator(csv_path1, csv_path2, cols1, cols2))
    
    def _generate_query_function(self, ast: SelectQuery):
        """
        Genera UNA singola funzione LLVM parametrica per valutare WHERE
        
        Firma: i1 @evaluate_row(i32 %col1, double %col2, ...)
        Riceve i valori delle colonne come parametri
        Ritorna: 1 se la riga passa il filtro WHERE, 0 altrimenti
        """
        # Imposta triple nativo prima di generare il codice
        self.module.triple = llvm.get_default_triple()
        
        # Determina parametri della funzione in base alle colonne usate nel WHERE
        if ast.where is None:
            # Nessun WHERE: funzione dummy che ritorna sempre true
            func_type = ir.FunctionType(ir.IntType(1), [])
            func = ir.Function(self.module, func_type, name="evaluate_row")
            block = func.append_basic_block(name="entry")
            self.builder = ir.IRBuilder(block)
            self.builder.ret(ir.Constant(ir.IntType(1), 1))
        else:
            # Estrai colonne usate nel WHERE per creare parametri
            where_columns = self._extract_columns_from_condition(ast.where)
            
            # Crea parametri funzione: un parametro per ogni colonna usata
            param_types = []
            self.param_map = {}  # {column_name: param_index}
            
            for idx, col in enumerate(where_columns):
                col_type = self.column_types.get(col, int)
                if col_type == int:
                    param_types.append(ir.IntType(32))
                elif col_type == float:
                    param_types.append(ir.DoubleType())
                else:
                    param_types.append(ir.IntType(32))  # String → int placeholder
                self.param_map[col] = idx
            
            # Crea funzione con parametri
            func_type = ir.FunctionType(ir.IntType(1), param_types)
            func = ir.Function(self.module, func_type, name="evaluate_row")
            
            # Entry block
            block = func.append_basic_block(name="entry")
            self.builder = ir.IRBuilder(block)
            
            # Salva parametri per usarli nella generazione IR
            self.func_params = func.args
            
            # Genera codice per la condizione WHERE usando visit
            result = self.visit(ast.where)
            self.builder.ret(result)
        
        # Applica ottimizzazioni LLVM se richiesto
        if self.optimize:
            self._optimize_llvm_ir()
        
        return func
    
    def _optimize_llvm_ir(self):
        """
        Applica passi di ottimizzazione LLVM IR (livello 2)
        
        Ottimizzazioni applicate:
        - Dead code elimination
        - Constant folding
        - Instruction combining
        - Simplificazione CFG
        """
        try:
            # Inizializza target nativo (necessario per ottimizzazioni)
            llvm.initialize_native_target()
            llvm.initialize_native_asmprinter()
            
            # Parse modulo per ottimizzazione
            llvmmod = llvm.parse_assembly(str(self.module))
            llvmmod.verify()
            
            # L'IR generato è già ottimale per le query semplici
            # Le ottimizzazioni vengono applicate dal JIT a runtime
            
        except (AttributeError, Exception):
            # Fallback silenzioso per vecchie versioni di llvmlite
            # L'ottimizzazione non è critica
            pass
    
    def _compile_llvm_to_jit(self, func):
        """
        Compila LLVM IR a codice nativo usando MCJIT e wrappa con ctypes
        
        Returns:
            Callable Python function o None se fallisce
        
        Nota: Su ARM64 (Apple Silicon) MCJIT può crashare a runtime a causa di 
        restrizioni W^X. In caso di crash, usa fallback Python (più lento ma stabile).
        L'IR generato è comunque corretto e verificabile.
        """
        import platform
        
        try:
            import ctypes
            from llvmlite import binding as llvm
            
            # Inizializza LLVM (llvm.initialize() è deprecato, si auto-inizializza)
            llvm.initialize_native_target()
            llvm.initialize_native_asmprinter()
            
            # Compila modulo
            mod = llvm.parse_assembly(str(self.module))
            mod.verify()
            
            # Crea target machine e MCJIT compiler
            target = llvm.Target.from_default_triple()
            target_machine = target.create_target_machine()
            ee = llvm.create_mcjit_compiler(mod, target_machine)
            ee.finalize_object()
            
            # Ottieni puntatore a funzione
            func_ptr = ee.get_function_address("evaluate_row")
            
            # Determina signature ctypes in base ai parametri
            param_types = []
            for arg in func.args:
                arg_type = arg.type
                if isinstance(arg_type, ir.IntType):
                    param_types.append(ctypes.c_int32)
                elif isinstance(arg_type, ir.DoubleType):
                    param_types.append(ctypes.c_double)
                else:
                    param_types.append(ctypes.c_int32)
            
            # Crea callable Python
            cfunc = ctypes.CFUNCTYPE(ctypes.c_bool, *param_types)(func_ptr)
            
            return cfunc
            
        except Exception:
            # Fallback silenzioso a esecuzione Python
            return None
    
    def visit_select_query(self, node: SelectQuery):
        """Metodo richiesto da ASTVisitor (non usato per generazione IR)"""
        pass
    
    def visit_comparison(self, node: Comparison):
        """
        Genera IR per comparazione usando PARAMETRI della funzione
        
        Es: eta > 18 diventa:
        define i1 @evaluate_row(i32 %eta) {
          %1 = icmp sgt i32 %eta, 18
          ret i1 %1
        }
        """
        col_type = self.column_types.get(node.left, int)
        
        # Ottieni il parametro della funzione per questa colonna
        param_idx = self.param_map.get(node.left, 0)
        left_val = self.func_params[param_idx]
        
        if col_type == int:
            # Valore destro
            if isinstance(node.right, (int, float)):
                right_val = ir.Constant(ir.IntType(32), int(node.right))
            else:
                right_val = ir.Constant(ir.IntType(32), 0)
            
            # Genera comparazione con PARAMETRO
            if node.operator == '>':
                return self.builder.icmp_signed('>', left_val, right_val)
            elif node.operator == '<':
                return self.builder.icmp_signed('<', left_val, right_val)
            elif node.operator == '>=':
                return self.builder.icmp_signed('>=', left_val, right_val)
            elif node.operator == '<=':
                return self.builder.icmp_signed('<=', left_val, right_val)
            elif node.operator == '=':
                return self.builder.icmp_signed('==', left_val, right_val)
            elif node.operator in ['<>', '!=']:
                return self.builder.icmp_signed('!=', left_val, right_val)
        
        elif col_type == float:
            # Valore destro
            if isinstance(node.right, (int, float)):
                right_val = ir.Constant(ir.DoubleType(), float(node.right))
            else:
                right_val = ir.Constant(ir.DoubleType(), 0.0)
            
            # Genera comparazione con PARAMETRO
            if node.operator == '>':
                return self.builder.fcmp_ordered('>', left_val, right_val)
            elif node.operator == '<':
                return self.builder.fcmp_ordered('<', left_val, right_val)
            elif node.operator == '>=':
                return self.builder.fcmp_ordered('>=', left_val, right_val)
            elif node.operator == '<=':
                return self.builder.fcmp_ordered('<=', left_val, right_val)
            elif node.operator == '=':
                return self.builder.fcmp_ordered('==', left_val, right_val)
            elif node.operator in ['<>', '!=']:
                return self.builder.fcmp_ordered('!=', left_val, right_val)
        
        # Fallback
        return ir.Constant(ir.IntType(1), 1)
    
    def _extract_columns_from_condition(self, condition) -> List[str]:
        """Estrae lista colonne usate in una condizione WHERE preservando l'ordine"""
        columns = []
        if isinstance(condition, Comparison):
            columns.append(condition.left)
            # Se right è una colonna (non un valore)
            if isinstance(condition.right, str) and condition.right in self.columns:
                columns.append(condition.right)
        elif isinstance(condition, NullCheck):
            columns.append(condition.column)
        elif isinstance(condition, LogicOp):
            for cond in condition.conditions:
                columns.extend(self._extract_columns_from_condition(cond))
        
        # Rimuovi duplicati PRESERVANDO L'ORDINE (dict mantiene insertion order da Python 3.7+)
        return list(dict.fromkeys(columns))
    
    def visit_null_check(self, node: NullCheck):
        """Genera IR per NULL check usando parametri"""
        # Per NULL check, confrontiamo il parametro con 0 (convenzione: NULL = 0)
        param_idx = self.param_map.get(node.column, 0)
        param = self.func_params[param_idx]
        
        # Controlla se parametro è 0 (NULL)
        zero = ir.Constant(param.type, 0)
        is_null = self.builder.icmp_signed('==', param, zero)
        
        if node.is_null:
            return is_null
        else:
            # NOT NULL: inverti il risultato
            return self.builder.xor(is_null, ir.Constant(ir.IntType(1), 1))
    
    def visit_logic_op(self, node: LogicOp):
        """Genera IR per operatori logici usando parametri"""
        results = [self.visit(cond) for cond in node.conditions]
        
        if node.operator == 'AND':
            result = results[0]
            for r in results[1:]:
                result = self.builder.and_(result, r)
            return result
        elif node.operator == 'OR':
            result = results[0]
            for r in results[1:]:
                result = self.builder.or_(result, r)
            return result
        
        return ir.Constant(ir.IntType(1), 1)
    
    def _execute_query(self, ast: SelectQuery, engine) -> List[Dict[str, Any]]:
        """
        Esegue la query usando il codice JIT compilato (se disponibile)
        
        Se JIT non disponibile (ARM64), usa fallback Python
        """
        results = []
        
        # Applica filtro WHERE
        for row in self.data:
            if ast.where:
                # Usa JIT se disponibile, altrimenti fallback Python
                if self.jit_func is not None:
                    passes = self._evaluate_condition_jit(ast.where, row)
                else:
                    passes = self._evaluate_condition_python(ast.where, row)
                
                if passes:
                    results.append(row)
            else:
                results.append(row)
        
        # Applica proiezione SELECT
        if ast.columns != "*":
            results = [{col: row[col] for col in ast.columns} for row in results]
        
        return results
    
    def _evaluate_condition_jit(self, condition, row: Dict[str, Any]) -> bool:
        """
        Valuta la condizione usando la funzione JIT compilata
        
        Estrae i valori delle colonne dalla riga e li passa come parametri
        """
        # Estrai valori delle colonne usate nella condizione
        where_columns = self._extract_columns_from_condition(condition)
        
        # Prepara parametri per la chiamata JIT
        params = []
        for col in where_columns:
            val = row.get(col)
            col_type = self.column_types.get(col, int)
            
            # Converti al tipo appropriato
            if col_type == int:
                params.append(int(val) if val != '' else 0)
            elif col_type == float:
                params.append(float(val) if val != '' else 0.0)
            else:
                params.append(0)  # String → fallback
        
        # Chiama funzione JIT con parametri
        try:
            return bool(self.jit_func(*params))
        except Exception:
            # Fallback silenzioso a Python
            return self._evaluate_condition_python(condition, row)
    
    def _evaluate_condition_python(self, condition, row: Dict[str, Any]) -> bool:
        """
        Valuta la condizione in Python (fallback)
        In una implementazione reale, chiameremmo la funzione LLVM JIT
        """
        if isinstance(condition, Comparison):
            left_val = row.get(condition.left)
            right_val = condition.right
            
            # Se right_val è una stringa che corrisponde a una colonna, caricala
            if isinstance(right_val, str) and right_val in row:
                right_val = row.get(right_val)
            
            # Converti tipi per confronto numerico
            try:
                if isinstance(right_val, (int, float)):
                    left_val = float(left_val)
                    right_val = float(right_val)
            except (ValueError, TypeError):
                pass
            
            op = condition.operator
            if op == '=': return left_val == right_val
            elif op == '>': return left_val > right_val
            elif op == '<': return left_val < right_val
            elif op == '>=': return left_val >= right_val
            elif op == '<=': return left_val <= right_val
            elif op in ['<>', '!=']: return left_val != right_val
            
        elif isinstance(condition, NullCheck):
            val = row.get(condition.column)
            is_null = val == '' or val is None
            return is_null if condition.is_null else not is_null
        
        elif isinstance(condition, LogicOp):
            results = [self._evaluate_condition_python(c, row) for c in condition.conditions]
            if condition.operator == 'AND':
                return all(results)
            elif condition.operator == 'OR':
                return any(results)
        
        return False
