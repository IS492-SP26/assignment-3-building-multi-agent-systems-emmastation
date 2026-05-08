# Sample Final Answer

## Query

What are key UX design principles for agentic AI interfaces?

## Final Synthesized Answer

Key UX design principles for agentic AI interfaces include transparency, planning visibility, user control, uncertainty communication, evidence traceability, and safety-aware feedback. Because agentic AI systems can plan, use tools, and take multi-step actions, users need more than a final answer. They need enough visibility into the system’s reasoning process, evidence base, and limitations to decide when to trust the system and when to intervene.

First, agentic interfaces should make the system’s current goal and plan visible. The interface should show what the agent is trying to do, which step it is currently working on, and what it plans to do next. This helps users understand the system’s behavior and reduces the feeling that the AI is acting as a black box. This principle aligns with human-AI interaction guidelines that emphasize setting expectations and making system capabilities clear (Amershi et al., 2019).

Second, agentic interfaces should explain tool use and evidence sources. If an agent uses search, code execution, files, or external APIs, the interface should communicate what tool was used and why. In AgentUX-MAS, the UI displays collected web and academic evidence, sources, and citations so users can inspect the basis of the final answer. This supports evidence traceability and helps users evaluate whether the response is grounded in credible information.

Third, agentic systems should communicate uncertainty and limitations. AI agents may produce confident-looking responses even when evidence is incomplete or when the system relies on fallback sources. The interface should clearly indicate when live search is unavailable, when evidence is representative rather than live, and when claims should be treated as design guidance rather than definitive conclusions. This is important because users often calibrate trust based on how clearly a system communicates its reliability and limits (Lee & See, 2004).

Fourth, users should retain control over the agent workflow. Good agentic UX should allow users to inspect intermediate outputs, revise the query, stop the workflow, or decide whether to accept a recommendation. In a multi-agent system, showing agent traces can help users understand how the Planner, Researcher, Writer, and Critic contributed to the final answer. This makes the process more inspectable and supports accountability.

Finally, agentic interfaces should make safety decisions visible. If a request is refused or sanitized, the system should briefly explain the safety category without exposing harmful details. In AgentUX-MAS, unsafe requests such as prompt injection or manipulative agent-design requests are blocked by the input guardrail before reaching the agent workflow. The UI then displays the refusal message and the triggered safety event. This supports safer interaction while still giving the user feedback about why the system did not proceed.

Overall, effective agentic AI interfaces should not only produce useful answers; they should also help users understand the agent’s plan, evidence, uncertainty, and safety boundaries. These principles are especially important for research assistants and other high-trust settings where users need to evaluate both the final response and the process that produced it.

## Sources

1. Amershi, S., Weld, D., Vorvoreanu, M., Fourney, A., Nushi, B., Collisson, P., Suh, J., Iqbal, S., Bennett, P. N., Inkpen, K., Teevan, J., Kikin-Gil, R., & Horvitz, E. (2019). *Guidelines for human-AI interaction*. Proceedings of the 2019 CHI Conference on Human Factors in Computing Systems. https://doi.org/10.1145/3290605.3300233

2. Lee, J. D., & See, K. A. (2004). *Trust in automation: Designing for appropriate reliance*. Human Factors, 46(1), 50–80. https://pubmed.ncbi.nlm.nih.gov/15151155/

3. Ribeiro, M. T., Singh, S., & Guestrin, C. (2016). *“Why should I trust you?” Explaining the predictions of any classifier*. Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining. https://doi.org/10.1145/2939672.2939778

4. Yang, Q., Steinfeld, A., Rosé, C. P., & Zimmerman, J. (2020). *Re-examining whether, why, and how human-AI interaction is uniquely difficult to design*. Proceedings of the 2020 CHI Conference on Human Factors in Computing Systems. https://doi.org/10.1145/3313831.3376301

5. Microsoft HAX Toolkit: Human-AI Experience Guidelines. https://www.microsoft.com/en-us/haxtoolkit/

6. Google People + AI Guidebook. https://pair.withgoogle.com/guidebook/