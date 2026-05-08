"""
Run batch evaluation for AgentUX-MAS.

Usage:
    python run_evaluation.py
"""

import asyncio
import json
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.autogen_orchestrator import AutoGenOrchestrator
from src.evaluation.evaluator import SystemEvaluator


async def main():
    load_dotenv(dotenv_path=".env", override=True)

    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    orchestrator = AutoGenOrchestrator(config)
    evaluator = SystemEvaluator(config, orchestrator=orchestrator)

    # Create a smaller evaluation subset to keep runtime manageable
    with open("data/example_queries.json", "r") as f:
        all_queries = json.load(f)

    sample_queries = all_queries[:3]

    Path("outputs").mkdir(exist_ok=True)
    sample_path = "outputs/eval_sample_queries.json"

    with open(sample_path, "w") as f:
        json.dump(sample_queries, f, indent=2)

    report = await evaluator.evaluate_system(sample_path)

    with open("outputs/latest_evaluation.json", "w") as f:
        json.dump(report, f, indent=2)

    print("\nEvaluation complete.")
    print(f"Total queries: {report.get('summary', {}).get('total_queries', 0)}")
    print(f"Successful: {report.get('summary', {}).get('successful', 0)}")
    print(f"Failed: {report.get('summary', {}).get('failed', 0)}")
    print(f"Overall average score: {report.get('scores', {}).get('overall_average', 0.0):.3f}")
    print("\nSaved to outputs/latest_evaluation.json")


if __name__ == "__main__":
    asyncio.run(main())