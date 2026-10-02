"""Unit test generation service for Python (pytest) and JavaScript (Jest)."""

from typing import Any, Dict, Optional

from app.rag.llm import llm_client
from app.repository.parser import parse_python_ast

UNIT_TEST_SYSTEM_PROMPT = """You are CodeMind AI, a senior test automation engineer specializing in pytest and test-driven development.
Given a source code snippet or function, generate a comprehensive, runnable unit test suite.

RULES:
1. For Python, write tests using `pytest`. Use pytest fixtures and parameterization (`@pytest.mark.parametrize`) where applicable.
2. For JavaScript/TypeScript, write tests using `Jest` (`describe`, `test`, `expect`).
3. Include tests for:
   - Happy paths (standard inputs and expected outputs)
   - Edge cases (empty strings, zero, boundary values, None/null)
   - Invalid inputs (wrong types, out-of-range arguments)
   - Exception handling (verifying expected exceptions are raised)
4. Do not invent modules or classes that do not exist.
5. Provide the code inside a standard markdown code block.
6. Clearly list required dependencies, mocks, and setup assumptions before or after the code.
"""


class UnitTestService:
    """Generates comprehensive unit test suites based on actual implementation."""

    def __init__(self):
        self.llm = llm_client

    async def generate_tests(
        self,
        code: str,
        file_path: str,
        target_symbol: Optional[str] = None,
        language: str = "python",
    ) -> Dict[str, Any]:
        """Generate unit tests for a specific function/class or entire file."""
        framework = "pytest" if language == "python" else "jest"

        # AST symbols summary
        symbols = []
        if language == "python":
            ast_data = parse_python_ast(code)
            symbols = ast_data.get("symbols", [])

        prompt = (
            f"File: {file_path}\n"
            f"Language: {language}\n"
            f"Test Framework: {framework}\n"
            f"Target Symbol: {target_symbol or 'All functions in file'}\n\n"
            f"Source Code:\n```\n{code[:4000]}\n```\n\n"
            f"Generate unit tests covering happy paths, edge cases, invalid inputs, and exceptions."
        )

        test_output = await self.llm.generate(prompt=prompt, system_prompt=UNIT_TEST_SYSTEM_PROMPT)

        return {
            "file_path": file_path,
            "language": language,
            "framework": framework,
            "target_symbol": target_symbol,
            "generated_test_code": test_output,
            "discovered_symbols": [s["name"] for s in symbols],
            "assumptions": [
                f"Tests use {framework} test runner.",
                "External network/database calls should be mocked using unittest.mock or pytest-mock.",
                "Ensure imports match your project layout.",
            ],
            "execution_note": "Generated tests should be reviewed and verified by a developer prior to execution.",
        }


test_service = UnitTestService()
