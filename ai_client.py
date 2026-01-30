from groq import Groq

from config import Config


SYSTEM_PROMPT_TEMPLATE = """\
You are {company_name} Internal Assistant, an AI-powered chatbot for company employees. \
You help with four main areas:

## YOUR CAPABILITIES

### 1. Company Q&A
Answer questions about company policies, HR procedures, IT guidelines, and onboarding \
processes. Base your answers ONLY on the provided company documents when available. \
If no relevant document is provided, say so clearly and suggest who to contact.

### 2. Document Summarization
When an employee shares a document, provide clear structured summaries with key points, \
action items, and important dates. You can also answer specific questions about shared documents.

### 3. IT Helpdesk
Guide employees through common IT issues step-by-step:
- Password resets and account recovery
- VPN setup and troubleshooting
- Software installation and licensing
- Email and calendar configuration
- Hardware troubleshooting basics
Always suggest contacting IT support for issues beyond your scope.

### 4. General Assistant
Help with professional tasks:
- Draft and refine emails
- Brainstorm ideas
- Writing and editing assistance
- Meeting agenda preparation
- Process documentation

## RULES
- Be professional but approachable.
- Never fabricate company policies. If you lack information, say "I don't have that \
information in my knowledge base. Please contact the relevant department."
- Keep responses concise unless the employee asks for detail.
- For sensitive topics (termination, legal, medical), always direct to HR or the appropriate department.
- Never share information about other employees.
- Format responses with markdown for readability (headers, bullet points, bold).\
{knowledge_context_section}"""

KNOWLEDGE_CONTEXT_SECTION = """

## COMPANY KNOWLEDGE BASE
The following are excerpts from company documents relevant to the employee's question. \
Base your answer on these documents when applicable. Cite the document name when referencing \
specific information.

{context}"""


class AIClient:
    """Wrapper around the Groq Python SDK for Llama API calls."""

    def __init__(self):
        if not Config.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY environment variable is not set. "
                "Set it with: export GROQ_API_KEY='your-key-here'"
            )
        self._client = Groq(api_key=Config.GROQ_API_KEY)
        self.model = Config.GROQ_MODEL
        self.max_tokens = Config.MAX_TOKENS

    def build_system_prompt(self, knowledge_context=""):
        """Construct the system prompt with optional knowledge base context."""
        if knowledge_context:
            kb_section = KNOWLEDGE_CONTEXT_SECTION.format(context=knowledge_context)
        else:
            kb_section = ""

        return SYSTEM_PROMPT_TEMPLATE.format(
            company_name=Config.COMPANY_NAME,
            knowledge_context_section=kb_section,
        )

    def send_message(self, conversation_history, user_message, knowledge_context=""):
        """Send a message to Groq and return the assistant response.

        Args:
            conversation_history: List of {"role": "user"|"assistant", "content": str}.
            user_message: The new user message.
            knowledge_context: Optional document context for RAG injection.

        Returns:
            The assistant's response text.
        """
        system_prompt = self.build_system_prompt(knowledge_context)

        messages = [{"role": "system", "content": system_prompt}] + list(conversation_history) + [
            {"role": "user", "content": user_message}
        ]

        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=messages,
        )

        return response.choices[0].message.content

    def summarize_document(self, document_text, user_query=""):
        """Summarize a document or answer questions about it.

        Args:
            document_text: The full extracted text of the document.
            user_query: Optional specific question about the document.

        Returns:
            Summary or answer string from Groq.
        """
        if user_query:
            prompt = (
                f"Based on the following document, answer this question: "
                f"{user_query}\n\n---\nDOCUMENT:\n{document_text}"
            )
        else:
            prompt = (
                f"Provide a clear, structured summary of the following document. "
                f"Include key points, main topics, and any action items.\n\n"
                f"---\nDOCUMENT:\n{document_text}"
            )

        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": "You are a document analysis assistant. Provide clear, accurate summaries and answers."},
                {"role": "user", "content": prompt},
            ],
        )

        return response.choices[0].message.content
