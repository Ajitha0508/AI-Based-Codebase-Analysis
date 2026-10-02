"""Code review service combining deterministic static AST checks, regex heuristics, and LLM suggestions."""

import json
from typing import Any, Dict, List

from app.rag.llm import llm_client
from app.repository.parser import parse_python_ast, scan_regex_security_issues

CODE_REVIEW_SYSTEM_PROMPT = """You are CodeMind AI, a senior security engineer and code reviewer.
Review the provided code snippet or file for potential:
1. Architectural or logical errors
2. Concurrency or state-handling problems
3. Missing edge case validations
4. Inefficient algorithms or memory leaks
5. Maintainability and clean-code issues

STRICT GUIDELINES:
- Output your findings as a JSON array of objects.
- Each object MUST have:
  "title": Short descriptive title
  "severity": "Critical", "High", "Medium", or "Low"
  "category": e.g. "Logic", "Validation", "Performance", "Maintainability"
  "line_range": e.g. "15-22"
  "explanation": Clear technical explanation
  "why_it_matters": Business and security impact
  "suggested_fix": Concrete code remediation
- Do not claim findings are guaranteed vulnerabilities; label them as potential concerns.
- Require human review before applying fixes.
- Return ONLY valid JSON array. No markdown code fences around JSON if possible.
"""


class CodeReviewService:
    """Combines deterministic static analysis and LLM analysis for code review."""

    def __init__(self):
        self.llm = llm_client

    async def review_code(
        self,
        code: str,
        file_path: str,
        language: str = "python",
        enable_ai_suggestions: bool = True,
    ) -> Dict[str, Any]:
        """
        Run both static AST checks and LLM-assisted code review.
        """
        findings: List[Dict[str, Any]] = []

        # 1. Deterministic Static AST analysis (for Python)
        if language == "python":
            ast_res = parse_python_ast(code)
            for issue in ast_res.get("security_issues", []):
                start_l = issue.get("start_line", 1)
                end_l = issue.get("end_line", start_l)
                findings.append({
                    "title": issue["title"],
                    "severity": issue["severity"],
                    "category": issue["category"],
                    "file_path": file_path,
                    "line_range": f"{start_l}-{end_l}",
                    "explanation": issue["explanation"],
                    "why_it_matters": issue["why_it_matters"],
                    "suggested_fix": issue["suggested_fix"],
                    "verification_status": issue["verification_status"],
                    "human_review_required": True,
                })

        # 2. Deterministic Regex security heuristics (all languages)
        regex_issues = scan_regex_security_issues(code, file_path)
        for issue in regex_issues:
            start_l = issue.get("start_line", 1)
            end_l = issue.get("end_line", start_l)
            findings.append({
                "title": issue["title"],
                "severity": issue["severity"],
                "category": issue["category"],
                "file_path": file_path,
                "line_range": f"{start_l}-{end_l}",
                "explanation": issue["explanation"],
                "why_it_matters": issue["why_it_matters"],
                "suggested_fix": issue["suggested_fix"],
                "verification_status": issue["verification_status"],
                "human_review_required": True,
            })

        # 3. AI Suggestions (if enabled)
        if enable_ai_suggestions:
            prompt = (
                f"File: {file_path}\nLanguage: {language}\n\n"
                f"```\n{code[:4000]}\n```\n\n"
                f"Analyze this code and provide review findings as a JSON array."
            )
            try:
                ai_output = await self.llm.generate(prompt=prompt, system_prompt=CODE_REVIEW_SYSTEM_PROMPT)
                clean_json_str = ai_output.strip()
                if clean_json_str.startswith("```json"):
                    clean_json_str = clean_json_str[7:]
                if clean_json_str.startswith("```"):
                    clean_json_str = clean_json_str[3:]
                if clean_json_str.endswith("```"):
                    clean_json_str = clean_json_str[:-3]

                parsed_ai = json.loads(clean_json_str.strip())
                if isinstance(parsed_ai, list):
                    for item in parsed_ai:
                        findings.append({
                            "title": item.get("title", "Review Finding"),
                            "severity": item.get("severity", "Medium"),
                            "category": item.get("category", "Code Quality"),
                            "file_path": file_path,
                            "line_range": str(item.get("line_range", "N/A")),
                            "explanation": item.get("explanation", ""),
                            "why_it_matters": item.get("why_it_matters", ""),
                            "suggested_fix": item.get("suggested_fix", ""),
                            "verification_status": "AI Review Suggestion",
                            "human_review_required": True,
                        })
            except Exception:
                # If LLM response isn't strict JSON or offline, static checks are already preserved
                pass

        # Severity breakdown
        counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for f in findings:
            sev = f.get("severity", "Low")
            if sev in counts:
                counts[sev] += 1

        return {
            "file_path": file_path,
            "language": language,
            "total_findings": len(findings),
            "severity_counts": counts,
            "findings": findings,
            "human_review_notice": (
                "IMPORTANT: Findings are automated indicators for human review. "
                "Always verify context and test thoroughly before making changes."
            ),
        }


review_service = CodeReviewService()
