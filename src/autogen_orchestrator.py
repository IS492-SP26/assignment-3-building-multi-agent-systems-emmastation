"""
AutoGen-Based Orchestrator

This orchestrator uses AutoGen's RoundRobinGroupChat to coordinate multiple agents
in a research workflow.

Workflow:
1. Input Guardrail: Checks user query safety
2. Evidence Collection: Adds stable web/paper evidence
3. Planner: Breaks down the query into research steps
4. Researcher: Reviews evidence and identifies relevant findings
5. Writer: Synthesizes findings into a coherent response
6. Critic: Evaluates quality and provides feedback
7. Output Guardrail: Checks final answer safety
"""

import logging
import asyncio
from typing import Dict, Any, List

from src.agents.autogen_agents import create_research_team
from src.guardrails.safety_manager import SafetyManager
from src.tools.web_search import web_search
from src.tools.paper_search import paper_search


class AutoGenOrchestrator:
    """
    Orchestrates multi-agent research using AutoGen's RoundRobinGroupChat.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the AutoGen orchestrator.

        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.logger = logging.getLogger("autogen_orchestrator")

        # Workflow trace for debugging and UI display
        self.workflow_trace: List[Dict[str, Any]] = []

        # Safety manager should be available before model/team creation
        self.safety_manager = SafetyManager(config.get("safety", {}))

        # Lazy-create the research team only after input safety passes
        self.team = None

    def _collect_evidence(self, query: str) -> Dict[str, Any]:
        """
        Collect reproducible evidence before running the AutoGen team.

        This implementation uses stable fallback web and paper evidence so the
        assignment demo can run without external search API keys.
        """
        evidence = {
            "web_results": "",
            "paper_results": "",
            "sources": []
        }

        web_query = f"{query} HCI agentic UX transparency trust uncertainty tool use"
        paper_query = f"{query} human AI interaction agentic UX transparency trust"

        evidence["web_results"] = web_search(
            query=web_query,
            provider=self.config.get("tools", {}).get("web_search", {}).get("provider", "tavily"),
            max_results=self.config.get("tools", {}).get("web_search", {}).get("max_results", 5)
        )

        evidence["paper_results"] = paper_search(
            query=paper_query,
            max_results=self.config.get("tools", {}).get("paper_search", {}).get("max_results", 5),
            year_from=2018
        )

        evidence["sources"] = [
            {
                "type": "webpage",
                "title": "Microsoft HAX Toolkit: Human-AI Experience Guidelines",
                "url": "https://www.microsoft.com/en-us/haxtoolkit/"
            },
            {
                "type": "webpage",
                "title": "Google People + AI Guidebook",
                "url": "https://pair.withgoogle.com/guidebook/"
            },
            {
                "type": "webpage",
                "title": "IBM Design for AI",
                "url": "https://www.ibm.com/design/ai/"
            },
            {
                "type": "paper",
                "title": "Guidelines for Human-AI Interaction",
                "authors": [{"name": "Saleema Amershi"}],
                "year": 2019,
                "venue": "CHI",
                "url": "https://doi.org/10.1145/3290605.3300233"
            },
            {
                "type": "paper",
                "title": "Why Should I Trust You? Explaining the Predictions of Any Classifier",
                "authors": [
                    {"name": "Marco Tulio Ribeiro"},
                    {"name": "Sameer Singh"},
                    {"name": "Carlos Guestrin"}
                ],
                "year": 2016,
                "venue": "KDD",
                "url": "https://doi.org/10.1145/2939672.2939778"
            },
            {
                "type": "paper",
                "title": "Trust in Automation: Designing for Appropriate Reliance",
                "authors": [
                    {"name": "John D. Lee"},
                    {"name": "Katrina A. See"}
                ],
                "year": 2004,
                "venue": "Human Factors",
                "url": "https://doi.org/10.1518/hfes.46.1.50_30392"
            }
        ]

        return evidence

    def process_query(self, query: str, max_rounds: int = 20) -> Dict[str, Any]:
        """
        Process a research query through the multi-agent system.
        """
        self.logger.info(f"Processing query: {query}")

        input_safety = self.safety_manager.check_input_safety(query)

        if not input_safety.get("safe", True):
            return {
                "query": query,
                "response": input_safety.get("response", "Request refused by safety policy."),
                "conversation_history": [],
                "metadata": {
                    "error": False,
                    "safety": input_safety,
                    "safety_events": self.safety_manager.get_safety_events(),
                    "agents_involved": []
                }
            }

        query = input_safety.get("query", query)

        if self.team is None:
            self.logger.info("Creating research team...")
            self.team = create_research_team(self.config)
            self.logger.info("Research team created successfully")

        try:
            loop = asyncio.get_event_loop()

            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = pool.submit(
                        asyncio.run,
                        self._process_query_async(query, max_rounds)
                    ).result()
            else:
                result = loop.run_until_complete(
                    self._process_query_async(query, max_rounds)
                )

            self.logger.info("Query processing complete")
            return result

        except Exception as e:
            self.logger.error(f"Error processing query: {e}", exc_info=True)
            return {
                "query": query,
                "error": str(e),
                "response": f"An error occurred while processing your query: {str(e)}",
                "conversation_history": [],
                "metadata": {
                    "error": True,
                    "safety_events": self.safety_manager.get_safety_events(),
                    "agents_involved": []
                }
            }

    async def _process_query_async(self, query: str, max_rounds: int = 20) -> Dict[str, Any]:
        """
        Async implementation of query processing.
        """
        evidence = self._collect_evidence(query)

        task_message = f"""Research Query: {query}

Collected Web Evidence:
{evidence.get("web_results", "")}

Collected Academic Paper Evidence:
{evidence.get("paper_results", "")}

Please work together to answer this query comprehensively:
1. Planner: Create a concise research plan based on the query and collected evidence.
2. Researcher: Review the collected web and academic evidence. Do not call tools directly. Identify the most relevant findings and source details.
3. Writer: Synthesize findings into a well-cited response with clear design implications for agentic UX.
4. Critic: Evaluate relevance, HCI grounding, citation quality, uncertainty handling, and safety.

The final answer should include:
- Direct answer
- Key evidence-based findings
- Design implications
- Risks or limitations
- Practical recommendations
- Sources or references section
"""

        result = await self.team.run(task=task_message)

        messages = []
        for message in result.messages:
            msg_dict = {
                "source": getattr(message, "source", "Unknown"),
                "content": message.content if hasattr(message, "content") else str(message),
            }
            messages.append(msg_dict)

        final_response = ""
        if messages:
            for msg in reversed(messages):
                if msg.get("source") == "Writer":
                    final_response = msg.get("content", "")
                    break

        if not final_response and messages:
            final_response = messages[-1].get("content", "")

        return self._extract_results(query, messages, final_response, evidence)

    def _extract_results(
        self,
        query: str,
        messages: List[Dict[str, Any]],
        final_response: str = "",
        evidence: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Extract structured results from the conversation history.
        """
        if evidence is None:
            evidence = {
                "web_results": "",
                "paper_results": "",
                "sources": []
            }

        research_findings = []
        plan = ""
        critique = ""

        for msg in messages:
            source = msg.get("source", "")
            content = msg.get("content", "")

            if source == "Planner" and not plan:
                plan = content
            elif source == "Researcher":
                research_findings.append(content)
            elif source == "Critic":
                critique = content

        output_safety = {
            "safe": True,
            "violations": [],
            "response": final_response,
            "action": "allow"
        }

        if final_response:
            final_response = final_response.replace("TERMINATE", "").strip()
            output_safety = self.safety_manager.check_output_safety(final_response)
            final_response = output_safety.get("response", final_response)

        return {
            "query": query,
            "response": final_response,
            "conversation_history": messages,
            "metadata": {
                "num_messages": len(messages),
                "num_sources": len(evidence.get("sources", [])),
                "plan": plan,
                "research_findings": research_findings,
                "critique": critique,
                "agents_involved": list(set([msg.get("source", "") for msg in messages])),
                "evidence": evidence,
                "sources": evidence.get("sources", []),
                "safety": output_safety,
                "safety_events": self.safety_manager.get_safety_events(),
            }
        }

    def get_agent_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions of all agents.
        """
        return {
            "Planner": "Breaks down research queries into actionable steps",
            "Researcher": "Reviews collected web and academic evidence",
            "Writer": "Synthesizes findings into coherent responses",
            "Critic": "Evaluates quality and provides feedback",
        }

    def visualize_workflow(self) -> str:
        """
        Generate a text visualization of the workflow.
        """
        return """
AgentUX-MAS Research Workflow:

1. User Query
   ↓
2. Input Guardrail
   - Checks prompt injection, harmful requests, privacy issues, and topic scope
   ↓
3. Evidence Collection
   - Adds representative web and academic evidence
   ↓
4. Planner
   - Creates research plan
   ↓
5. Researcher
   - Reviews evidence
   - Identifies relevant findings
   ↓
6. Writer
   - Synthesizes findings
   - Creates final response
   ↓
7. Critic
   - Evaluates quality and safety
   ↓
8. Output Guardrail
   - Checks final response safety
"""


def demonstrate_usage():
    """
    Demonstrate how to use the AutoGen orchestrator.
    """
    import yaml
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=".env", override=True)

    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    orchestrator = AutoGenOrchestrator(config)

    print(orchestrator.visualize_workflow())

    query = "What are key UX design principles for agentic AI interfaces?"

    print(f"\nProcessing query: {query}\n")
    print("=" * 70)

    result = orchestrator.process_query(query)

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"\nQuery: {result['query']}")
    print(f"\nResponse:\n{result['response']}")
    print(f"\nMetadata:")
    print(f"  - Messages exchanged: {result['metadata']['num_messages']}")
    print(f"  - Sources gathered: {result['metadata']['num_sources']}")
    print(f"  - Agents involved: {', '.join(result['metadata']['agents_involved'])}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    demonstrate_usage()