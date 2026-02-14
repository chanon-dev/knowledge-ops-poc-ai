"""Sub-agent integration: CrewAI research agent and AutoGen code analysis."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AnalyzerAgent:
    """Deep-dive analysis agent for complex errors and multi-step reasoning."""

    async def analyze(self, query: str, context: str, error_logs: str | None = None) -> str:
        """Perform deep analysis on complex issues."""
        from app.services.llm.ollama_client import OllamaClient

        client = OllamaClient()
        system_prompt = """You are an expert analyzer agent. Your job is to:
1. Break down complex problems into smaller components
2. Analyze root causes step by step
3. Consider multiple potential causes
4. Provide detailed, actionable solutions

Format your response with clear sections: Analysis, Root Cause, Solution, Prevention."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nProblem:\n{query}"},
        ]

        if error_logs:
            messages.append({"role": "user", "content": f"Error Logs:\n{error_logs}"})

        try:
            response = await client.chat(messages, model="mistral:7b")
            return response
        except Exception as e:
            logger.error(f"Analyzer agent failed: {e}")
            return f"Analysis unavailable: {e}"


class ResearcherAgent:
    """Research agent that searches external documentation and knowledge bases."""

    async def research(self, query: str, sources: list[str] | None = None) -> str:
        """Research a topic using available knowledge."""
        from app.services.llm.ollama_client import OllamaClient

        client = OllamaClient()
        system_prompt = """You are a research agent. Your job is to:
1. Provide comprehensive information about the topic
2. Reference relevant documentation and best practices
3. Include step-by-step instructions when applicable
4. Cite sources when possible

Be thorough but concise."""

        source_context = ""
        if sources:
            source_context = f"\n\nAvailable documentation sources:\n" + "\n".join(f"- {s}" for s in sources)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Research this topic:\n{query}{source_context}"},
        ]

        try:
            response = await client.chat(messages, model="mistral:7b")
            return response
        except Exception as e:
            logger.error(f"Researcher agent failed: {e}")
            return f"Research unavailable: {e}"


class CodeReviewAgent:
    """Code analysis agent that identifies bugs, misconfigurations, and suggests fixes."""

    async def analyze_code(self, code: str, language: str = "auto", query: str = "") -> dict:
        """Analyze code snippet for bugs, security issues, and improvements."""
        from app.services.llm.ollama_client import OllamaClient

        client = OllamaClient()
        system_prompt = """You are an expert code reviewer. Analyze the provided code and respond with JSON format:
{
    "language": "detected language",
    "issues": [
        {"severity": "critical|warning|info", "line": null, "description": "issue description", "fix": "suggested fix"}
    ],
    "security_concerns": ["list of security issues"],
    "suggestions": ["list of improvement suggestions"],
    "fixed_code": "corrected code if applicable"
}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Language: {language}\nQuery: {query}\n\nCode:\n```\n{code}\n```"},
        ]

        try:
            response = await client.chat(messages, model="mistral:7b")
            # Try to parse as JSON, fall back to raw text
            import json
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {"raw_analysis": response, "issues": [], "suggestions": []}
        except Exception as e:
            logger.error(f"Code review agent failed: {e}")
            return {"error": str(e), "issues": [], "suggestions": []}


class SubAgentOrchestrator:
    """Orchestrate sub-agents based on department configuration."""

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.analyzer = AnalyzerAgent()
        self.researcher = ResearcherAgent()
        self.code_reviewer = CodeReviewAgent()

    async def run(self, query: str, context: str, agent_type: str = "auto") -> dict:
        """Run the appropriate sub-agent based on query type."""
        if agent_type == "auto":
            agent_type = self._detect_type(query)

        results = {"agent_type": agent_type}

        if agent_type == "analyzer":
            results["analysis"] = await self.analyzer.analyze(query, context)
        elif agent_type == "researcher":
            results["research"] = await self.researcher.research(query)
        elif agent_type == "code_review":
            code = self._extract_code(query)
            results["code_review"] = await self.code_reviewer.analyze_code(code, query=query)
        else:
            results["analysis"] = await self.analyzer.analyze(query, context)

        return results

    def _detect_type(self, query: str) -> str:
        q = query.lower()
        code_indicators = ["```", "def ", "function ", "class ", "import ", "var ", "const ", "let "]
        if any(ind in q for ind in code_indicators):
            return "code_review"
        error_indicators = ["error", "exception", "traceback", "failed", "crash", "bug"]
        if any(ind in q for ind in error_indicators):
            return "analyzer"
        return "researcher"

    def _extract_code(self, query: str) -> str:
        if "```" in query:
            parts = query.split("```")
            if len(parts) >= 3:
                return parts[1].strip()
        return query
