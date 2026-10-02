"""Source code parsing: Python AST symbol extraction, multi-language symbols, and deterministic static security checks."""

import ast
import re
from typing import Any, Dict, List, Optional


class CodeSymbol:
    """Represents a code symbol (class, function, method, interface)."""
    def __init__(
        self,
        name: str,
        kind: str,
        start_line: int,
        end_line: int,
        docstring: Optional[str] = None,
        parameters: Optional[List[str]] = None,
        complexity: int = 1,
    ):
        self.name = name
        self.kind = kind
        self.start_line = start_line
        self.end_line = end_line
        self.docstring = docstring or ""
        self.parameters = parameters or []
        self.complexity = complexity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "docstring": self.docstring,
            "parameters": self.parameters,
            "complexity": self.complexity,
        }


class PythonASTVisitor(ast.NodeVisitor):
    """Visits Python AST nodes to extract classes, functions, and imports."""
    def __init__(self):
        self.symbols: List[CodeSymbol] = []
        self.imports: List[str] = []
        self.security_issues: List[Dict[str, Any]] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        mod = node.module or ""
        for alias in node.names:
            self.imports.append(f"{mod}.{alias.name}")
        self.generic_visit(node)

    def _calculate_complexity(self, node: ast.AST) -> int:
        complexity = 1
        for subnode in ast.walk(node):
            if isinstance(subnode, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler, ast.With)):
                complexity += 1
            elif isinstance(subnode, ast.BoolOp):
                complexity += len(subnode.values) - 1
        return complexity

    def visit_ClassDef(self, node: ast.ClassDef):
        docstring = ast.get_docstring(node) or ""
        start_line = node.lineno
        end_line = getattr(node, "end_lineno", start_line)
        complexity = self._calculate_complexity(node)

        self.symbols.append(
            CodeSymbol(
                name=node.name,
                kind="class",
                start_line=start_line,
                end_line=end_line,
                docstring=docstring,
                complexity=complexity,
            )
        )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._record_function(node, is_async=False)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._record_function(node, is_async=True)
        self.generic_visit(node)

    def _record_function(self, node: Any, is_async: bool):
        docstring = ast.get_docstring(node) or ""
        start_line = node.lineno
        end_line = getattr(node, "end_lineno", start_line)
        params = [arg.arg for arg in node.args.args]
        complexity = self._calculate_complexity(node)
        kind = "async_function" if is_async else "function"

        self.symbols.append(
            CodeSymbol(
                name=node.name,
                kind=kind,
                start_line=start_line,
                end_line=end_line,
                docstring=docstring,
                parameters=params,
                complexity=complexity,
            )
        )

    def visit_Call(self, node: ast.Call):
        # Deterministic check for eval/exec
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in ("eval", "exec"):
                self.security_issues.append({
                    "title": f"Insecure Execution via `{func_name}()`",
                    "severity": "Critical",
                    "category": "Code Injection",
                    "start_line": node.lineno,
                    "end_line": getattr(node, "end_lineno", node.lineno),
                    "explanation": f"Call to dynamic code evaluation function `{func_name}()` allows arbitrary code execution if supplied with untrusted inputs.",
                    "why_it_matters": "Attackers can achieve Remote Code Execution (RCE) on the server environment.",
                    "suggested_fix": f"Replace `{func_name}()` with safer parsing alternatives such as `ast.literal_eval()` or dedicated JSON/schema decoders.",
                    "verification_status": "Static AST Confirmed",
                })
        # Check for subprocess with shell=True
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in ("Popen", "run", "call", "check_output", "check_call"):
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        self.security_issues.append({
                            "title": "Subprocess Invocation with `shell=True`",
                            "severity": "High",
                            "category": "Command Injection",
                            "start_line": node.lineno,
                            "end_line": getattr(node, "end_lineno", node.lineno),
                            "explanation": "Spawning a subshell with `shell=True` exposes the application to command injection if argument strings contain unescaped user data.",
                            "why_it_matters": "Command injection enables attackers to execute arbitrary system shell commands.",
                            "suggested_fix": "Set `shell=False` and pass arguments as a list of strings instead of a concatenated shell command.",
                            "verification_status": "Static AST Confirmed",
                        })
            elif node.func.attr == "loads" and getattr(node.func.value, "id", None) == "pickle":
                self.security_issues.append({
                    "title": "Insecure Deserialization with `pickle.loads`",
                    "severity": "Critical",
                    "category": "Insecure Deserialization",
                    "start_line": node.lineno,
                    "end_line": getattr(node, "end_lineno", node.lineno),
                    "explanation": "Python's `pickle` module is not secure against erroneous or maliciously constructed data.",
                    "why_it_matters": "Arbitrary code execution can occur upon unpickling untrusted payload objects.",
                    "suggested_fix": "Use safe data serialization formats such as JSON or Protocol Buffers.",
                    "verification_status": "Static AST Confirmed",
                })
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        # Check for bare except: or empty pass
        if node.type is None:
            self.security_issues.append({
                "title": "Bare Exception Handling (`except:`)",
                "severity": "Medium",
                "category": "Error Handling",
                "start_line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "explanation": "A bare `except:` clause catches all exceptions including `SystemExit`, `KeyboardInterrupt`, and `MemoryError`.",
                "why_it_matters": "Hides critical operational failures, complicates debugging, and can prevent clean shutdown.",
                "suggested_fix": "Catch specific exception subclasses like `except Exception:` or more granular exceptions like `except ValueError:`.",
                "verification_status": "Static AST Confirmed",
            })
        elif len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            self.security_issues.append({
                "title": "Silenced Exception with Empty `pass`",
                "severity": "Low",
                "category": "Error Handling",
                "start_line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "explanation": "Silencing exceptions with `pass` without logging or telemetry causes silent failures.",
                "why_it_matters": "Errors go unnoticed in production and leave the system in an inconsistent state.",
                "suggested_fix": "Log the exception with `logger.exception()` or handle the fallback explicitly.",
                "verification_status": "Static AST Confirmed",
            })
        self.generic_visit(node)


def parse_python_ast(code: str) -> Dict[str, Any]:
    """Parse Python source code and return symbols, imports, and deterministic security findings."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {
            "syntax_valid": False,
            "error": str(e),
            "symbols": [],
            "imports": [],
            "security_issues": [],
        }

    visitor = PythonASTVisitor()
    visitor.visit(tree)

    return {
        "syntax_valid": True,
        "error": None,
        "symbols": [s.to_dict() for s in visitor.symbols],
        "imports": visitor.imports,
        "security_issues": visitor.security_issues,
    }


def parse_generic_symbols(code: str, language: str) -> List[Dict[str, Any]]:
    """Generic regex-based symbol extractor for JavaScript, TypeScript, Java, Go, etc."""
    symbols = []
    lines = code.splitlines()

    # Function and class regex patterns
    patterns = {
        "javascript": [
            (re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_$]+)\s*\((.*?)\)"), "function"),
            (re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\((.*?)\)\s*=>"), "arrow_function"),
            (re.compile(r"^\s*(?:export\s+)?class\s+([a-zA-Z0-9_$]+)"), "class"),
        ],
        "typescript": [
            (re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_$]+)\s*\((.*?)\)"), "function"),
            (re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\((.*?)\)\s*=>"), "arrow_function"),
            (re.compile(r"^\s*(?:export\s+)?class\s+([a-zA-Z0-9_$]+)"), "class"),
            (re.compile(r"^\s*(?:export\s+)?interface\s+([a-zA-Z0-9_$]+)"), "interface"),
            (re.compile(r"^\s*(?:export\s+)?type\s+([a-zA-Z0-9_$]+)\s*="), "type"),
        ],
        "java": [
            (re.compile(r"^\s*(?:public|private|protected|static|final|\s)+\s+(?:class|interface|enum)\s+([a-zA-Z0-9_]+)"), "class"),
            (re.compile(r"^\s*(?:public|private|protected|static|final|\s)+[\w<>\[\]]+\s+([a-zA-Z0-9_]+)\s*\((.*?)\)\s*(?:throws\s+[\w,\s]+)?\s*\{?"), "method"),
        ],
        "go": [
            (re.compile(r"^func\s+(?:\(.*?\)\s+)?([a-zA-Z0-9_]+)\s*\("), "function"),
            (re.compile(r"^type\s+([a-zA-Z0-9_]+)\s+struct"), "struct"),
            (re.compile(r"^type\s+([a-zA-Z0-9_]+)\s+interface"), "interface"),
        ],
    }

    lang_patterns = patterns.get(language, [])
    for line_idx, line in enumerate(lines, start=1):
        for pattern, kind in lang_patterns:
            match = pattern.search(line)
            if match:
                name = match.group(1)
                symbols.append({
                    "name": name,
                    "kind": kind,
                    "start_line": line_idx,
                    "end_line": line_idx,
                    "docstring": "",
                    "parameters": [],
                    "complexity": 1,
                })
                break

    return symbols


def scan_regex_security_issues(code: str, file_path: str) -> List[Dict[str, Any]]:
    """Scan source code across any language using deterministic security heuristics."""
    issues = []
    lines = code.splitlines()

    # Regex heuristic patterns
    patterns = [
        (
            re.compile(r"""(?:password|secret|api[_-]?key|access[_-]?token)\s*=\s*['"][a-zA-Z0-9_\-\.]{8,}['"]""", re.IGNORECASE),
            "Hardcoded Credential or Token Detected",
            "Critical",
            "Secrets Management",
            "Credentials and private tokens hardcoded directly in source code.",
            "Secrets committed to source control can be extracted by unauthorized users.",
            "Extract secret values into environment variables or a secure secret manager (e.g. AWS Secrets Manager, HashiCorp Vault)."
        ),
        (
            re.compile(r"""(SELECT|INSERT|UPDATE|DELETE)\s+.*?\+\s*[\w\.]+""", re.IGNORECASE),
            "Potential SQL Injection via String Concatenation",
            "High",
            "Injection",
            "SQL query is constructed using dynamic string concatenation instead of parameterized placeholders.",
            "Allows attackers to inject malicious SQL clauses and tamper with or exfiltrate database records.",
            "Use parameterized queries, prepared statements, or an ORM like SQLAlchemy."
        ),
        (
            re.compile(r"""http:\/\/(?!localhost|127\.0\.0\.1|0\.0\.0\.0)[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}""", re.IGNORECASE),
            "Insecure HTTP Transmission",
            "Low",
            "Transport Security",
            "Unencrypted HTTP URL found in source code.",
            "Traffic over unencrypted HTTP can be intercepted or manipulated via man-in-the-middle (MITM) attacks.",
            "Upgrade endpoint to HTTPS protocol."
        ),
    ]

    for line_idx, line in enumerate(lines, start=1):
        for regex, title, severity, category, explanation, why, fix in patterns:
            if regex.search(line):
                issues.append({
                    "title": title,
                    "severity": severity,
                    "category": category,
                    "file_path": file_path,
                    "start_line": line_idx,
                    "end_line": line_idx,
                    "explanation": explanation,
                    "why_it_matters": why,
                    "suggested_fix": fix,
                    "verification_status": "Static Heuristic Confirmed",
                })

    return issues
