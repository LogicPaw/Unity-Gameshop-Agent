"""Load the project-local domain skill into the model prompt."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = PROJECT_ROOT / "skills/unity-virtual-shop-config"


def load_shop_skill() -> str:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    domain_rules = (SKILL_ROOT / "references/domain-rules.md").read_text(
        encoding="utf-8"
    )
    return f"{skill}\n\n---\n\n{domain_rules}"
