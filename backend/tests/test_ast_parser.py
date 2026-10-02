"""Unit tests for Python AST parsing and deterministic static security rules."""

from app.repository.parser import (
    parse_generic_symbols,
    parse_python_ast,
    scan_regex_security_issues,
)


def test_python_ast_symbol_extraction():
    code = (
        "import os\n"
        "from typing import List\n\n"
        "class UserService:\n"
        "    \"\"\"Handles user operations.\"\"\"\n"
        "    async def create_user(self, username: str, email: str):\n"
        "        \"\"\"Create a new user.\"\"\"\n"
        "        return {'username': username}\n"
    )
    res = parse_python_ast(code)
    assert res["syntax_valid"] is True
    assert "os" in res["imports"]
    assert "typing.List" in res["imports"]

    symbols = res["symbols"]
    symbol_names = [s["name"] for s in symbols]
    assert "UserService" in symbol_names
    assert "create_user" in symbol_names


def test_python_ast_security_issue_detection():
    # Code with dangerous patterns
    vulnerable_code = (
        "import subprocess\n"
        "import pickle\n\n"
        "def unsafe_handler(payload, cmd):\n"
        "    data = pickle.loads(payload)\n"
        "    res = eval(cmd)\n"
        "    proc = subprocess.Popen(cmd, shell=True)\n"
        "    try:\n"
        "        risky_call()\n"
        "    except:\n"
        "        pass\n"
    )
    res = parse_python_ast(vulnerable_code)
    issues = res["security_issues"]

    titles = [i["title"] for i in issues]
    # Check that pickle.loads is flagged
    assert any("pickle.loads" in t for t in titles)
    # Check that eval() is flagged as Critical
    assert any("eval()" in t for t in titles)
    # Check that shell=True is flagged as High
    assert any("shell=True" in t for t in titles)
    # Check that bare except is flagged
    assert any("Bare Exception" in t for t in titles)


def test_generic_symbols_javascript():
    js_code = (
        "export function calculateTotal(items) {\n"
        "    return items.reduce((a, b) => a + b, 0);\n"
        "}\n\n"
        "export class OrderProcessor {\n"
        "}\n"
    )
    symbols = parse_generic_symbols(js_code, "javascript")
    names = [s["name"] for s in symbols]
    assert "calculateTotal" in names
    assert "OrderProcessor" in names


def test_regex_security_scanner():
    code = (
        "const apiKey = 'sk-1234567890abcdefghijklmnop';\n"
        "const query = 'SELECT * FROM users WHERE name = ' + userName;\n"
    )
    issues = scan_regex_security_issues(code, "test.js")
    categories = [i["category"] for i in issues]
    assert "Secrets Management" in categories
    assert "Injection" in categories
