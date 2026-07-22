"""Shared package metadata and Markdown frontmatter parsing."""
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
    return (yaml.safe_load(m.group(1)) or {}), m.group(2)
