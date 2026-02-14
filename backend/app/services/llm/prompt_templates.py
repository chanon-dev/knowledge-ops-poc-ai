DEFAULT_SYSTEM_PROMPT = """You are "KnowledgeOps", an AI assistant for enterprise knowledge management.
Answer questions accurately based on the provided context. If you're not sure, say so.
Always cite your sources when the information comes from the knowledge base."""

DEPARTMENT_PROMPTS = {
    "it-ops": "You are an IT operations expert specializing in server, network, and infrastructure troubleshooting. Provide step-by-step solutions and reference relevant documentation.",
    "hr": "You are an HR expert specializing in company policies, benefits, and employee onboarding. Provide clear, policy-compliant answers.",
    "legal": "You are a legal expert specializing in contracts, compliance, and corporate governance. Always include disclaimers about seeking professional legal advice for critical matters.",
    "finance": "You are a finance expert specializing in budgeting, accounting, and financial reporting. Be precise with numbers and reference relevant financial policies.",
    "engineering": "You are a software engineering expert specializing in development practices, code review, and technical architecture. Provide practical, actionable advice.",
}


def get_system_prompt(department_config: dict) -> str:
    custom = department_config.get("system_prompt")
    if custom:
        return custom
    return DEFAULT_SYSTEM_PROMPT


def build_rag_prompt(
    query: str,
    context: str,
    system_prompt: str,
) -> list[dict]:
    messages = [
        {"role": "system", "content": system_prompt},
    ]

    if context:
        messages.append(
            {
                "role": "system",
                "content": f"Use the following knowledge base context to answer the user's question. Cite sources when applicable.\n\n{context}",
            }
        )

    messages.append({"role": "user", "content": query})

    return messages


def build_confidence_prompt(query: str, answer: str) -> str:
    return f"""Rate the confidence of the following answer on a scale of 0.0 to 1.0.
Consider: accuracy, completeness, relevance to the question, and whether the answer is based on provided context.

Question: {query}

Answer: {answer}

Respond with ONLY a number between 0.0 and 1.0, nothing else."""
