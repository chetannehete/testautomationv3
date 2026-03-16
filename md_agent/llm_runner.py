"""
LLM Runner — Sends the master + child prompts to an LLM API and saves outputs.

Supports:
  - Google Gemini  (default)  — GEMINI_API_KEY
  - OpenAI GPT-4o             — OPENAI_API_KEY
  - Anthropic Claude          — ANTHROPIC_API_KEY

Usage from CLI:
  python -m md_agent execute output/ --provider gemini
  python -m md_agent execute output/ --dry-run
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════
#  DATA MODELS
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class StepResult:
    """Result of executing one child prompt step."""
    step_number: int
    child_file: str
    purpose: str
    llm_response: str
    extracted_files: List[Tuple[str, str]] = field(default_factory=list)  # (filename, content)
    success: bool = True
    error: Optional[str] = None


@dataclass
class SessionResult:
    """Result of the full LLM session."""
    project_name: str
    provider: str
    model: str
    steps: List[StepResult] = field(default_factory=list)
    session_log: str = ""


# ═══════════════════════════════════════════════════════════════════════
#  FILE EXTRACTION
# ═══════════════════════════════════════════════════════════════════════

# Maps fenced code block language → file extension
_LANG_EXT = {
    "java":     ".java",
    "kotlin":   ".kt",
    "markdown": ".md",
    "md":       ".md",
    "plantuml": ".puml",
    "puml":     ".puml",
    "bash":     ".sh",
    "shell":    ".sh",
    "sh":       ".sh",
    "yaml":     ".yaml",
    "yml":      ".yml",
    "json":     ".json",
    "xml":      ".xml",
    "properties": ".properties",
    "dockerfile": "Dockerfile",
}

_CODE_BLOCK_RE = re.compile(
    r"```(?P<lang>\w+)?\n(?P<code>.*?)```",
    re.DOTALL,
)

# Heuristics to guess a filename from the code content
_JAVA_CLASS_RE = re.compile(r"(?:class|interface|enum|record)\s+(\w+)")
_JAVA_PKG_RE = re.compile(r"^\s*package\s+([\w\.]+)\s*;", re.MULTILINE)
_PLANTUML_TITLE_RE = re.compile(r"@startuml\s+(\w+)")


def extract_code_blocks(
    response: str,
    step_number: int,
    purpose: str,
) -> List[Tuple[str, str]]:
    """
    Extract all fenced code blocks from an LLM response.
    Returns list of (filename, content) tuples.
    """
    results = []
    seen_names: dict[str, int] = {}

    for match in _CODE_BLOCK_RE.finditer(response):
        lang = (match.group("lang") or "").lower().strip()
        code = match.group("code").strip()

        if not code:
            continue

        ext = _LANG_EXT.get(lang, ".txt")

        # Try to infer a sensible filename
        filename = _infer_filename(lang, ext, code, step_number, seen_names)
        seen_names[filename] = seen_names.get(filename, 0) + 1
        if seen_names[filename] > 1:
            base, dot_ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
            filename = f"{base}_{seen_names[filename]}.{dot_ext}" if dot_ext else f"{base}_{seen_names[filename]}"

        results.append((filename, code))

    return results


def _infer_filename(lang: str, ext: str, code: str, step: int, seen: dict) -> str:
    """Try to produce a meaningful filename from code content, including standard project subdirectories."""
    prefix = f"step_{step:02d}_"

    if lang == "java":
        m_cls = _JAVA_CLASS_RE.search(code)
        cls_name = m_cls.group(1) if m_cls else "UnknownClass"
        
        m_pkg = _JAVA_PKG_RE.search(code)
        if m_pkg:
            pkg_path = m_pkg.group(1).replace(".", "/")
            return f"src/test/java/{pkg_path}/{prefix}{cls_name}{ext}"
        return f"src/test/java/{prefix}{cls_name}{ext}"

    if lang in ("plantuml", "puml"):
        m = _PLANTUML_TITLE_RE.search(code)
        name = m.group(1) if m else "c4_diagram"
        return f"docs/{prefix}{name}{ext}"

    if lang in ("bash", "shell", "sh"):
        return f"scripts/{prefix}run_commands{ext}"

    if lang in ("markdown", "md"):
        return f"docs/{prefix}documentation{ext}"

    if lang in ("yaml", "yml"):
        return f"deploy/{prefix}config{ext}"

    return f"{prefix}output{ext}"


# ═══════════════════════════════════════════════════════════════════════
#  LLM PROVIDER ADAPTERS
# ═══════════════════════════════════════════════════════════════════════

def _call_gemini(
    messages: List[dict],
    api_key: str,
    model: str,
) -> str:
    """Call Google Gemini via the google-generativeai SDK."""
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError(
            "google-generativeai is not installed.\n"
            "Run: pip install google-generativeai"
        )

    genai.configure(api_key=api_key)
    gemini_model = genai.GenerativeModel(model)

    # Convert message list to Gemini chat format
    chat = gemini_model.start_chat(history=[])

    response_text = ""
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            response = chat.send_message(content)
            response_text = response.text
        # assistant messages are handled by the chat history automatically

    return response_text


def _call_openai(
    messages: List[dict],
    api_key: str,
    model: str,
) -> str:
    """Call OpenAI via the openai SDK."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "openai is not installed.\n"
            "Run: pip install openai"
        )

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return response.choices[0].message.content


def _call_anthropic(
    messages: List[dict],
    api_key: str,
    model: str,
) -> str:
    """Call Anthropic Claude via the anthropic SDK."""
    try:
        import anthropic
    except ImportError:
        raise ImportError(
            "anthropic is not installed.\n"
            "Run: pip install anthropic"
        )

    client = anthropic.Anthropic(api_key=api_key)

    # Separate system messages from user/assistant
    system_content = ""
    filtered = []
    for msg in messages:
        if msg["role"] == "system":
            system_content = msg["content"]
        else:
            filtered.append(msg)

    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=system_content or "You are a senior software engineer.",
        messages=filtered,
    )
    return response.content[0].text


# ═══════════════════════════════════════════════════════════════════════
#  PROVIDER DEFAULTS
# ═══════════════════════════════════════════════════════════════════════

_PROVIDER_DEFAULTS = {
    "gemini":    ("gemini-3-flash-preview",   "GEMINI_API_KEY",    _call_gemini),
    "openai":    ("gpt-4o",           "OPENAI_API_KEY",    _call_openai),
    "anthropic": ("claude-3-5-sonnet-20241022", "ANTHROPIC_API_KEY", _call_anthropic),
}


# ═══════════════════════════════════════════════════════════════════════
#  MAIN RUNNER CLASS
# ═══════════════════════════════════════════════════════════════════════

class LLMRunner:
    """
    Drives the full nested prompt session through an LLM.

      1. Sends the master prompt as the opening message
      2. Iterates through each child prompt file
      3. Sends each child's content as a follow-up turn
      4. Extracts code blocks from each response
      5. Saves every artifact to generated_dir
    """

    def __init__(
        self,
        provider: str = "gemini",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        delay_between_steps: float = 2.0,
    ):
        if provider not in _PROVIDER_DEFAULTS:
            raise ValueError(
                f"Unknown provider '{provider}'. "
                f"Choose from: {list(_PROVIDER_DEFAULTS.keys())}"
            )

        default_model, env_var, call_fn = _PROVIDER_DEFAULTS[provider]
        self.provider = provider
        self.model = model or default_model
        self.api_key = api_key or os.environ.get(env_var, "")
        self._call_fn = call_fn
        self.delay = delay_between_steps

        if not self.api_key:
            raise ValueError(
                f"No API key found for provider '{provider}'.\n"
                f"Set the {env_var} environment variable or pass --api-key."
            )

    def run(
        self,
        prompts_dir: str,
        generated_dir: str,
        only_step: Optional[int] = None,
        on_step_start=None,   # callback(step_num, filename)
        on_step_done=None,    # callback(StepResult)
    ) -> SessionResult:
        """
        Execute the full session.

        Args:
            prompts_dir:   Directory with 00_master_prompt.md + child files
            generated_dir: Where to write extracted artifacts
            only_step:     If set, run only this step number (1-based)
            on_step_start: Optional progress callback
            on_step_done:  Optional completion callback
        """
        prompts_path = Path(prompts_dir)
        gen_path = Path(generated_dir)
        gen_path.mkdir(parents=True, exist_ok=True)

        # Load master prompt
        master_file = prompts_path / "00_master_prompt.md"
        if not master_file.exists():
            raise FileNotFoundError(
                f"Master prompt not found: {master_file}\n"
                "Run 'python -m md_agent orchestrate <path>' first."
            )
        master_content = master_file.read_text(encoding="utf-8")

        # Load all child prompt files in order
        child_files = sorted(
            f for f in prompts_path.glob("[0-9][0-9]_*_prompt.md")
            if not f.name.startswith("00_")
        )

        if not child_files:
            raise FileNotFoundError(f"No child prompt files found in: {prompts_dir}")

        # Detect project name from master prompt
        project_name = _extract_project_name(master_content)

        # Build conversation history
        # System message sets the role, master prompt is the first user turn
        conversation: List[dict] = [
            {
                "role": "system",
                "content": (
                    "You are a senior software engineer, QA lead, and architect. "
                    "You generate compilable, production-quality Java code, "
                    "Markdown documentation, and PlantUML diagrams. "
                    "Always follow the hard rules specified in the prompt exactly."
                ),
            },
            {
                "role": "user",
                "content": (
                    master_content
                    + "\n\nAcknowledge you have read the master prompt and the "
                    "invocation chain. State which Step you will start with. "
                    "Do not generate anything yet — just confirm."
                ),
            },
        ]

        result = SessionResult(
            project_name=project_name,
            provider=self.provider,
            model=self.model,
        )
        log_lines: List[str] = [
            f"# Session Log — {project_name}",
            f"Provider: {self.provider} | Model: {self.model}",
            "---",
        ]

        # Turn 1: Master prompt orientation
        orientation = self._call(conversation)
        conversation.append({"role": "assistant", "content": orientation})
        log_lines += [
            "## Orientation",
            orientation,
            "---",
        ]

        # Turns 2–N: one per child prompt
        for child_path in child_files:
            step_match = re.match(r"^(\d+)", child_path.name)
            step_num = int(step_match.group(1)) if step_match else 0

            if only_step is not None and step_num != only_step:
                continue

            if on_step_start:
                on_step_start(step_num, child_path.name)

            child_content = child_path.read_text(encoding="utf-8")
            purpose = _extract_purpose(child_content)

            # Build the follow-up turn
            user_turn = (
                f"## Executing Step {step_num:02d}\n\n"
                f"Below is the full content of `{child_path.name}`. "
                f"Follow ALL hard rules exactly and generate the required output.\n\n"
                f"---\n\n{child_content}\n\n---\n\n"
                f"Generate the complete output for Step {step_num:02d} now."
            )
            conversation.append({"role": "user", "content": user_turn})

            step_result = StepResult(
                step_number=step_num,
                child_file=child_path.name,
                purpose=purpose,
                llm_response="",
            )

            try:
                response = self._call(conversation)
                conversation.append({"role": "assistant", "content": response})

                step_result.llm_response = response
                step_result.extracted_files = extract_code_blocks(
                    response, step_num, purpose
                )

                # Save extracted files
                for fname, content in step_result.extracted_files:
                    out_file = gen_path / fname
                    # Ensure the nested directory exists (e.g., src/test/java/...)
                    out_file.parent.mkdir(parents=True, exist_ok=True)
                    out_file.write_text(content, encoding="utf-8")

            except Exception as exc:
                step_result.success = False
                step_result.error = str(exc)
                step_result.llm_response = f"ERROR: {exc}"

            result.steps.append(step_result)

            log_lines += [
                f"## Step {step_num:02d} — {purpose}",
                f"**File:** `{child_path.name}`",
                "",
                step_result.llm_response,
                "",
                "---",
            ]

            if on_step_done:
                on_step_done(step_result)

            # Polite delay to avoid rate limiting
            if self.delay > 0:
                time.sleep(self.delay)

        # Final summary request
        if only_step is None and result.steps:
            conversation.append({
                "role": "user",
                "content": (
                    "All steps are complete. Please produce the final session summary table "
                    "as specified in the master prompt (Step | Child File | Output Artifact | Status)."
                ),
            })
            summary = self._call(conversation)
            log_lines += ["## Final Summary", summary, "---"]
            result.session_log = "\n".join(log_lines)

            # Save session log
            log_path = gen_path / "session_log.md"
            log_path.write_text(result.session_log, encoding="utf-8")

        return result

    def _call(self, messages: List[dict]) -> str:
        """Dispatch to the correct provider's API."""
        return self._call_fn(messages, self.api_key, self.model)


# ═══════════════════════════════════════════════════════════════════════
#  DRY RUN RUNNER
# ═══════════════════════════════════════════════════════════════════════

class DryRunLLMRunner:
    """
    A no-op runner that prints what would be sent without calling any API.
    Useful for verifying the session structure before spending API credits.
    """

    def run(
        self,
        prompts_dir: str,
        generated_dir: str,
        only_step: Optional[int] = None,
        on_step_start=None,
        on_step_done=None,
    ) -> SessionResult:
        prompts_path = Path(prompts_dir)

        master_file = prompts_path / "00_master_prompt.md"
        master_content = master_file.read_text(encoding="utf-8") if master_file.exists() else ""
        project_name = _extract_project_name(master_content)

        child_files = sorted(
            f for f in prompts_path.glob("[0-9][0-9]_*_prompt.md")
            if not f.name.startswith("00_")
        )

        result = SessionResult(
            project_name=project_name,
            provider="dry-run",
            model="none",
        )

        for child_path in child_files:
            step_match = re.match(r"^(\d+)", child_path.name)
            step_num = int(step_match.group(1)) if step_match else 0

            if only_step is not None and step_num != only_step:
                continue

            if on_step_start:
                on_step_start(step_num, child_path.name)

            child_content = child_path.read_text(encoding="utf-8")
            purpose = _extract_purpose(child_content)

            step_result = StepResult(
                step_number=step_num,
                child_file=child_path.name,
                purpose=purpose,
                llm_response="[DRY RUN — LLM not called]",
                success=True,
            )
            result.steps.append(step_result)

            if on_step_done:
                on_step_done(step_result)

        return result


# ═══════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════

def _extract_project_name(master_content: str) -> str:
    """Extract project name from master prompt header."""
    m = re.search(r"\*\*Project:\*\*\s+(.+)", master_content)
    return m.group(1).strip() if m else "project"


def _extract_purpose(child_content: str) -> str:
    """Extract the Purpose line from a child prompt file."""
    m = re.search(r"^## Purpose\s*\n(.+)", child_content, re.MULTILINE)
    return m.group(1).strip() if m else "Unknown"
