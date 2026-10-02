"""Documentation generation service for architecture overviews, module docs, API specs, and READMEs."""

from typing import Any, Dict, List

from app.rag.llm import llm_client

DOC_SYSTEM_PROMPT = """You are CodeMind AI, a senior technical writer and software architect.
Generate precise, clean, professional Markdown documentation based strictly on the provided codebase files and AST metadata.

RULES:
1. Ground documentation strictly in actual repository content.
2. Mark missing or unverified information explicitly (e.g. `[Unverified Configuration]`) instead of inventing details.
3. Use formatted GitHub Flavored Markdown (headings, tables, callout blocks, code blocks).
4. Include clear instructions, prerequisites, and code examples where verified.
"""


class DocumentationService:
    """Generates structured documentation grounded in indexed codebase assets."""

    def __init__(self):
        self.llm = llm_client

    async def generate_doc(
        self,
        doc_type: str,  # "overview", "module", "api", "setup", "readme"
        context_files: List[Dict[str, Any]],
        repo_name: str = "Repository",
    ) -> Dict[str, Any]:
        """Generate documentation of a specified type."""
        files_summary = "\n".join([
            f"- File: {f.get('path')} ({f.get('language')}, {f.get('line_count', 0)} lines)"
            for f in context_files[:30]
        ])

        snippets = []
        for f in context_files[:8]:
            path = f.get("path", "")
            content = f.get("content", "")[:1200]
            snippets.append(f"### {path}\n```\n{content}\n```")

        snippets_text = "\n\n".join(snippets)

        type_instructions = {
            "overview": "Generate a comprehensive Repository Architecture Overview explaining the system structure, core components, and design patterns.",
            "module": "Generate Module & Package Documentation breaking down the key modules, their responsibilities, and exported interfaces.",
            "api": "Generate an API Reference detailing the endpoints, route handlers, models, and request/response structures found in the files.",
            "setup": "Generate verified Setup & Installation Instructions based on discovered configuration and dependency files.",
            "readme": "Generate a production-grade README.md with project overview, features, installation, usage, and architecture notes.",
        }

        instruction = type_instructions.get(doc_type, type_instructions["overview"])

        prompt = (
            f"Repository: {repo_name}\n"
            f"Documentation Type: {doc_type}\n\n"
            f"Indexed Files Summary:\n{files_summary}\n\n"
            f"Key File Extracts:\n{snippets_text}\n\n"
            f"Task: {instruction}\n\n"
            f"Format the result in beautiful, clear GitHub Flavored Markdown."
        )

        doc_content = await self.llm.generate(prompt=prompt, system_prompt=DOC_SYSTEM_PROMPT)

        return {
            "doc_type": doc_type,
            "repo_name": repo_name,
            "markdown_content": doc_content,
        }


doc_service = DocumentationService()
