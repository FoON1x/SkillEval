"""Export the FastAPI OpenAPI schema to a JSON file (for TS type generation)."""

import json
import sys
from pathlib import Path

from skill_eval.app import create_app
from skill_eval.store.repository import Store

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("openapi.json")
app = create_app(store=Store.in_memory())
out.write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2), encoding="utf-8")
print(f"exported openapi to {out}")
