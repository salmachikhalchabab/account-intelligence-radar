import os
import json
from datetime import datetime


def build_markdown(company_name: str, data: dict) -> str:
    """Converts structured JSON report into a readable Markdown summary."""

    lines = [f"# Account Intelligence Report: {company_name}",
             f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n"]

    def render(obj, depth=2):
        """Recursively render dict/list into Markdown."""
        result = ""
        heading = "#" * min(depth, 6)

        if isinstance(obj, dict):
            for key, value in obj.items():
                label = key.replace("_", " ").title()
                if isinstance(value, (dict, list)):
                    result += f"\n{heading} {label}\n"
                    result += render(value, depth + 1)
                else:
                    result += f"- **{label}:** {value}\n"

        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    result += render(item, depth)
                else:
                    result += f"- {item}\n"

        return result

    lines.append(render(data))
    return "\n".join(lines)


def save_report(company_name: str, data: dict) -> dict:
    """
    Saves the report as both JSON and Markdown.
    Returns a dict with both file paths.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = company_name.replace(" ", "_")

    os.makedirs("reports", exist_ok=True)

    # JSON
    json_path = f"reports/{safe_name}_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Markdown
    md_path = f"reports/{safe_name}_{timestamp}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(build_markdown(company_name, data))

    print(f"✓ JSON saved:     {json_path}")
    print(f"✓ Markdown saved: {md_path}")

    return {"json": json_path, "markdown": md_path}