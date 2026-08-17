"""Shared package metadata and Markdown frontmatter parsing."""
import json
import re

import yaml

SYSTEM_SKILLS = {"founder-os-init", "founder-os-doctor", "context-load",
                 "guardrails", "state-integrity", "ingestion-gate",
                 "setup-cadences", "skill-forge"}
UNIVERSAL_SKILLS = {"guardrails", "state-integrity", "ingestion-gate"}
# Skills that belong to no agent by design, because running them as a subagent
# is denied by construction. setup-cadences edits the founder's crontab;
# skill-forge writes `_local/` and installs outside the workspace, and the
# ownership guard denies every subagent that directory (extensibility.md).
STANDALONE_SKILLS = {"setup-cadences", "skill-forge"}


def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        raise ValueError("%s: missing YAML frontmatter" % path)
    data = yaml.safe_load(m.group(1))
    if data is None:
        data = {}
    elif not isinstance(data, dict):
        raise ValueError(
            "%s: YAML frontmatter must be a mapping or null (got %s)"
            % (path, type(data).__name__)
        )
    return data, m.group(2)


def parse_skill_writes(frontmatter):
    """Return a skill's declared paths from list or PromptScript string metadata."""
    if "metadata" not in frontmatter:
        return []
    metadata = frontmatter["metadata"]
    if not isinstance(metadata, dict):
        return None
    if "writes" not in metadata:
        return []

    writes = metadata["writes"]
    if isinstance(writes, list):
        return writes if all(isinstance(item, str) for item in writes) else None
    if not isinstance(writes, str):
        return None

    try:
        decoded = json.loads(writes)
    except json.JSONDecodeError:
        return [writes]
    if not isinstance(decoded, list):
        return None
    return decoded if all(isinstance(item, str) for item in decoded) else None
