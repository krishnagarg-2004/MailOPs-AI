"""
MIPROv2 Optimizer and Compiler for MailOps AI.
Generates and tunes system instructions and few-shot demonstrations against gold email datasets.
"""

import json
import logging
from pathlib import Path
from typing import Any
import dspy

from backend.app.ai.optimization.signatures import EmailIntelligenceSignature
from backend.app.ai.optimization.metrics import mailops_composite_metric

logger = logging.getLogger(__name__)


class EmailExtractorModule(dspy.Module):
    """DSPy Module encapsulating the email intelligence extraction predictor."""

    def __init__(self):
        super().__init__()
        self.extract = dspy.Predict(EmailIntelligenceSignature)

    def forward(self, sender: str, subject: str, body: str):
        return self.extract(sender=sender, subject=subject, body=body)


def load_dataset(dataset_path: Path) -> list[dspy.Example]:
    """Loads and formats fixtures into DSPy Examples."""
    with open(dataset_path, "r", encoding="utf-8") as f:
        raw_samples = json.load(f)

    examples = []
    for s in raw_samples:
        ex = dspy.Example(
            sender=s.get("sender", "(Unknown)"),
            subject=s.get("subject", "(No Subject)"),
            body=s.get("body", ""),
            expected_intent=s.get("expected_intent", "OTHER"),
            expected_actions=s.get("expected_actions", []),
        ).with_inputs("sender", "subject", "body")
        examples.append(ex)
    return examples


def compile_mipro_prompt(
    dataset_path: Path,
    output_path: Path,
    num_candidates: int = 5,
    max_bootstrapped_demos: int = 2,
) -> dict[str, Any]:
    """
    Compiles an optimized prompt artifact using DSPy MIPROv2.
    Exports the tuned instructions and demonstrations to a standalone JSON file.
    """
    examples = load_dataset(dataset_path)
    if not examples:
        raise ValueError(f"No examples found in dataset: {dataset_path}")

    # Split into train and validation sets
    split_idx = max(1, len(examples) // 2)
    train_set = examples[:split_idx]
    val_set = examples[split_idx:]

    logger.info(f"Loaded {len(examples)} examples (Train: {len(train_set)}, Val: {len(val_set)})")

    # Initialize baseline module
    baseline = EmailExtractorModule()

    # Configure MIPROv2 teleprompter
    teleprompter = dspy.MIPROv2(
        metric=mailops_composite_metric,
        auto="light",
        num_candidates=num_candidates,
    )

    logger.info("Starting DSPy MIPROv2 compilation...")
    optimized_module = teleprompter.compile(
        baseline,
        trainset=train_set,
        valset=val_set,
        max_bootstrapped_demos=max_bootstrapped_demos,
        minibatch=False,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    optimized_module.save(str(output_path))
    logger.info(f"MIPRO compiled prompt successfully saved to {output_path}")

    return {
        "status": "success",
        "output_path": str(output_path),
        "train_size": len(train_set),
        "val_size": len(val_set),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    default_dataset = Path(__file__).resolve().parents[3] / "tests" / "evaluation" / "fixtures" / "email_samples.json"
    default_output = Path(__file__).resolve().parents[1] / "compiled_prompts.json"
    compile_mipro_prompt(default_dataset, default_output)
