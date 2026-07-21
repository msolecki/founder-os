"""Shared package metadata and Markdown frontmatter parsing."""
import re

import yaml

SYSTEM_SKILLS = {"founder-os-init", "founder-os-doctor", "context-load",
                 "guardrails", "state-integrity", "ingestion-gate",
                 "setup-cadences"}
UNIVERSAL_SKILLS = {"guardrails", "state-integrity", "ingestion-gate"}
STANDALONE_SKILLS = {"setup-cadences"}


def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        raise ValueError("%s: missing YAML frontmatter" % path)
    return (yaml.safe_load(m.group(1)) or {}), m.group(2)
