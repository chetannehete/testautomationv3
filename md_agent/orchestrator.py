"""
Master Prompt Orchestrator

Controls the execution flow of the nested prompt generation system:
  1. Accepts parsed Java classes as input
  2. Runs Spring Boot pattern detection
  3. Evaluates conditional rules to determine which prompts to generate
  4. Builds the OrchestrationPlan with execution order
  5. Generates ONE prompt per type via prompt_templates (generic, reusable)
  6. Writes prompt files + orchestration report to output directory

DESIGN: Each prompt type produces exactly ONE output file.
For example, there is ONE unit_test_prompt.md that covers ALL testable
classes, not one per class.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from md_agent.models import (
    ClassInfo,
    CodebaseAnalysis,
    ComponentType,
    GeneratedPrompt,
    OrchestrationPlan,
    ProjectFeatures,
    PromptType,
)
from md_agent.spring_detector import analyze_codebase
from md_agent.prompt_templates import (
    build_unit_test_prompt,
    build_integration_test_prompt,
    build_e2e_test_prompt,
    build_documentation_prompt,
    build_c4_architecture_prompt,
    build_run_arguments_prompt,
    build_master_orchestrator_prompt,
)


# ======================================================================
#  ORCHESTRATOR
# ======================================================================

class PromptOrchestrator:
    """
    Master Prompt Orchestrator.

    Analyzes a Spring Boot codebase and generates ONE generic prompt
    per prompt type based on detected patterns and conditional rules.
    """

    def __init__(self, project_name: str = "project"):
        self.project_name = project_name
        self.analysis: Optional[CodebaseAnalysis] = None
        self.plan: Optional[OrchestrationPlan] = None
        self.generated_prompts: List[GeneratedPrompt] = []
        self.master_prompt: Optional[GeneratedPrompt] = None

    def analyze(self, classes: List[ClassInfo]) -> CodebaseAnalysis:
        """Step 1: Analyze the codebase and detect Spring Boot patterns."""
        self.analysis = analyze_codebase(classes, project_name=self.project_name)
        return self.analysis

    def plan_execution(self) -> OrchestrationPlan:
        """Step 2: Evaluate conditions and build the orchestration plan."""
        if not self.analysis:
            raise RuntimeError("Call analyze() before plan_execution()")

        features = self.analysis.features
        conditions: Dict[str, bool] = {}
        prompts_to_gen: List[PromptType] = []

        # -- Condition: Unit tests -- always if there are non-test classes --
        has_testable = any(
            c.component_type not in (ComponentType.TEST, ComponentType.UNKNOWN)
            for c in self.analysis.components
        )
        conditions["has_testable_classes"] = has_testable
        if has_testable:
            prompts_to_gen.append(PromptType.UNIT_TEST)

        # -- Condition: Integration tests (API / DB / Messaging) --
        has_integration_targets = (
            features.has_rest_controllers or
            features.has_database or
            features.has_messaging
        )
        conditions["has_rest_controllers"] = features.has_rest_controllers
        conditions["has_database"] = features.has_database
        conditions["has_messaging"] = features.has_messaging
        if has_integration_targets:
            prompts_to_gen.append(PromptType.INTEGRATION_TEST)

        # -- Condition: E2E tests -- if controllers and services exist --
        has_full_stack = features.controller_count > 0 and features.service_count > 0
        conditions["has_full_stack"] = has_full_stack
        if has_full_stack:
            prompts_to_gen.append(PromptType.E2E_TEST)

        # -- Condition: Documentation -- always --
        conditions["always_generate_docs"] = True
        prompts_to_gen.append(PromptType.DOCUMENTATION)

        # -- Condition: C4 diagrams -- if multiple component types exist --
        distinct_types = len(set(
            c.component_type for c in self.analysis.components
            if c.component_type not in (ComponentType.UNKNOWN, ComponentType.TEST)
        ))
        conditions["has_multiple_component_types"] = distinct_types >= 2
        if distinct_types >= 2:
            prompts_to_gen.append(PromptType.C4_ARCHITECTURE)

        # -- Condition: Run arguments -- always --
        conditions["always_generate_run_args"] = True
        prompts_to_gen.append(PromptType.RUN_ARGUMENTS)

        # Deduplicate while preserving order
        seen = set()
        ordered = []
        for pt in prompts_to_gen:
            if pt not in seen:
                seen.add(pt)
                ordered.append(pt)

        # Define execution order (tests first, then docs, then diagrams)
        priority = {
            PromptType.UNIT_TEST: 1,
            PromptType.INTEGRATION_TEST: 2,
            PromptType.E2E_TEST: 3,
            PromptType.DOCUMENTATION: 4,
            PromptType.C4_ARCHITECTURE: 5,
            PromptType.RUN_ARGUMENTS: 6,
        }
        ordered.sort(key=lambda pt: priority.get(pt, 99))

        self.plan = OrchestrationPlan(
            project_name=self.project_name,
            features=features,
            prompts_to_generate=ordered,
            conditions_met=conditions,
            execution_order=ordered,
        )
        return self.plan

    def generate_prompts(self) -> List[GeneratedPrompt]:
        """
        Step 3: Generate ONE prompt per prompt type.

        Each prompt type produces a single, generic, reusable prompt
        covering ALL relevant components for that type.
        """
        if not self.plan or not self.analysis:
            raise RuntimeError("Call plan_execution() before generate_prompts()")

        self.generated_prompts = []

        for prompt_type in self.plan.execution_order:
            if prompt_type == PromptType.UNIT_TEST:
                self._generate_unit_test_prompt()
            elif prompt_type == PromptType.INTEGRATION_TEST:
                self._generate_integration_test_prompt()
            elif prompt_type == PromptType.E2E_TEST:
                self._generate_e2e_prompt()
            elif prompt_type == PromptType.DOCUMENTATION:
                self._generate_documentation_prompt()
            elif prompt_type == PromptType.C4_ARCHITECTURE:
                self._generate_c4_prompt()
            elif prompt_type == PromptType.RUN_ARGUMENTS:
                self._generate_run_args_prompt()

        return self.generated_prompts

    def generate_master_prompt(self) -> GeneratedPrompt:
        """Step 3b: Generate the master/root orchestrator prompt."""
        if not self.generated_prompts or not self.analysis:
            raise RuntimeError("Call generate_prompts() before generate_master_prompt()")

        child_filenames = [
            f"{i:02d}_{p.prompt_type.value}_prompt.md"
            for i, p in enumerate(self.generated_prompts, start=1)
        ]
        self.master_prompt = build_master_orchestrator_prompt(
            self.analysis, self.generated_prompts, child_filenames
        )
        return self.master_prompt

    def write_output(self, output_dir: str) -> Dict[str, str]:
        """
        Step 4: Write all generated prompts, the master orchestrator prompt,
        and the orchestration report to the output directory.

        Output structure:
            00_master_prompt.md          <- Root prompt
            00_orchestration_report.md   <- Feature detection summary
            01_unit_test_prompt.md       <- ONE single unit test prompt
            02_integration_test_prompt.md
            03_e2e_test_prompt.md
            04_documentation_prompt.md
            05_c4_architecture_prompt.md
            06_run_arguments_prompt.md

        Returns a dict mapping filename -> absolute path.
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        written: Dict[str, str] = {}

        # Pre-compute child filenames
        child_filenames = [
            f"{i:02d}_{p.prompt_type.value}_prompt.md"
            for i, p in enumerate(self.generated_prompts, start=1)
        ]

        # Generate master prompt (if not already done)
        if self.master_prompt is None:
            self.generate_master_prompt()

        # Write master orchestrator prompt
        master_path = out / "00_master_prompt.md"
        master_path.write_text(
            self._format_master_prompt_file(self.master_prompt), encoding="utf-8"
        )
        written["00_master_prompt.md"] = str(master_path.resolve())

        # Write orchestration report
        report_path = out / "00_orchestration_report.md"
        report_path.write_text(self._build_report(), encoding="utf-8")
        written["00_orchestration_report.md"] = str(report_path.resolve())

        # Write each child prompt as a numbered .md file
        for i, (prompt, filename) in enumerate(zip(self.generated_prompts, child_filenames), start=1):
            filepath = out / filename
            filepath.write_text(
                self._format_prompt_file(prompt, step_number=i, total_steps=len(self.generated_prompts)),
                encoding="utf-8",
            )
            written[filename] = str(filepath.resolve())

        return written

    def run(
        self,
        classes: List[ClassInfo],
        output_dir: str,
    ) -> Dict[str, str]:
        """
        Full pipeline: analyze -> plan -> generate -> generate_master -> write.
        Returns dict of written file paths.
        """
        self.analyze(classes)
        self.plan_execution()
        self.generate_prompts()
        self.generate_master_prompt()
        return self.write_output(output_dir)

    # -- Internal prompt generators (ONE call per type) -----------------

    def _generate_unit_test_prompt(self):
        """Generate ONE unit test prompt covering ALL testable components."""
        testable = [
            comp for comp in self.analysis.components
            if comp.component_type not in (
                ComponentType.TEST, ComponentType.UNKNOWN,
                ComponentType.DTO, ComponentType.ENTITY
            )
            and comp.class_info.methods
        ]
        if testable:
            prompt = build_unit_test_prompt(testable, self.analysis)
            self.generated_prompts.append(prompt)

    def _generate_integration_test_prompt(self):
        """Generate ONE integration test prompt covering ALL integration targets."""
        features = self.analysis.features

        # Collect all components that need integration tests
        integration_targets = []
        for comp in self.analysis.components:
            if comp.component_type in (ComponentType.REST_CONTROLLER, ComponentType.CONTROLLER):
                integration_targets.append(comp)
            elif comp.component_type == ComponentType.REPOSITORY and features.has_database:
                integration_targets.append(comp)
            elif comp.component_type in (ComponentType.MESSAGING_LISTENER, ComponentType.MESSAGING_PRODUCER) and features.has_messaging:
                integration_targets.append(comp)

        if integration_targets:
            prompt = build_integration_test_prompt(integration_targets, self.analysis)
            self.generated_prompts.append(prompt)

    def _generate_e2e_prompt(self):
        """Generate a single E2E test prompt for the whole project."""
        prompt = build_e2e_test_prompt(self.analysis)
        self.generated_prompts.append(prompt)

    def _generate_documentation_prompt(self):
        """Generate documentation prompt for the whole project."""
        prompt = build_documentation_prompt(self.analysis)
        self.generated_prompts.append(prompt)

    def _generate_c4_prompt(self):
        """Generate C4 architecture diagram prompt."""
        prompt = build_c4_architecture_prompt(self.analysis)
        self.generated_prompts.append(prompt)

    def _generate_run_args_prompt(self):
        """Generate run arguments prompt."""
        prompt = build_run_arguments_prompt(self.analysis)
        self.generated_prompts.append(prompt)

    # -- Report & formatting (NO EMOJIS) --------------------------------

    def _build_report(self) -> str:
        """Build the orchestration report markdown. No emojis."""
        features = self.analysis.features
        plan = self.plan

        # Conditions table
        cond_rows = []
        for cond, met in plan.conditions_met.items():
            status = "MET" if met else "NOT MET"
            cond_rows.append(f"| {cond} | {status} |")
        cond_table = "\n".join(cond_rows)

        # Prompt summary
        prompt_rows = []
        for i, p in enumerate(self.generated_prompts, 1):
            targets_str = ", ".join(p.target_classes[:3])
            if len(p.target_classes) > 3:
                targets_str += "..."
            prompt_rows.append(
                f"| {i} | {p.prompt_type.value} | {p.purpose} | {targets_str} |"
            )
        prompt_table = "\n".join(prompt_rows)

        # Component inventory
        comp_rows = []
        for comp in self.analysis.components:
            cls = comp.class_info
            comp_rows.append(
                f"| {cls.name} | {comp.component_type.value} | {len(cls.methods)} | {len(comp.endpoints)} | {len(comp.dependencies)} |"
            )
        comp_table = "\n".join(comp_rows)

        return f"""# Orchestration Report -- {self.project_name}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Classes Analyzed:** {features.total_classes}
**Total Prompts Generated:** {len(self.generated_prompts)}

---

## Project Feature Detection

| Feature | Status |
|---------|--------|
| REST Controllers | {'Yes' if features.has_rest_controllers else 'No'} ({features.controller_count}) |
| Database / JPA | {'Yes' if features.has_database else 'No'} ({', '.join(features.database_types) if features.database_types else '-'}) |
| Messaging | {'Kafka' if features.has_kafka else 'RabbitMQ' if features.has_rabbitmq else 'No'} |
| Security | {'Yes' if features.has_security else 'No'} |
| Scheduling | {'Yes' if features.has_scheduling else 'No'} |
| Caching | {'Yes' if features.has_caching else 'No'} |
| Validation | {'Yes' if features.has_validation else 'No'} |
| Feign Client | {'Yes' if features.has_feign_client else 'No'} |
| Circuit Breaker | {'Yes' if features.has_circuit_breaker else 'No'} |
| Exception Handling | {'Yes' if features.has_exception_handling else 'No'} |

---

## Conditional Execution Rules

| Condition | Result |
|-----------|--------|
{cond_table}

---

## Component Inventory

| Class | Type | Methods | Endpoints | Dependencies |
|-------|------|---------|-----------|--------------|
{comp_table}

---

## Generated Prompts ({len(self.generated_prompts)} total)

| # | Type | Purpose | Target Classes |
|---|------|---------|----------------|
{prompt_table}

---

## Execution Order

{chr(10).join(f'{i}. **{pt.value}**' for i, pt in enumerate(plan.execution_order, 1))}

---

*Generated by MD Agent Prompt Orchestrator v2.0*
"""

    def _format_master_prompt_file(self, prompt: GeneratedPrompt) -> str:
        """Format the master orchestrator prompt as a standalone markdown file."""
        return f"""# MASTER ORCHESTRATOR PROMPT

> **Role:** Root of the nested prompt hierarchy -- invokes all child prompts sequentially.
> **Project:** {self.project_name}
> **Child Prompts:** {len(self.generated_prompts)}

---

{prompt.template_body}

---

*Generated by MD Agent Prompt Orchestrator v2.0 -- Master Prompt*
"""

    def _format_prompt_file(self, prompt: GeneratedPrompt, step_number: int = 0, total_steps: int = 0) -> str:
        """Format a single child GeneratedPrompt as a standalone markdown file."""
        hard_rules_md = "\n".join(
            f"- **[{r.id}]** {r.description}" for r in prompt.hard_rules
        )
        soft_rules_md = "\n".join(
            f"- **[{r.id}]** {r.description}" for r in prompt.soft_rules
        )
        steps_md = "\n".join(prompt.execution_steps)
        targets = ", ".join(prompt.target_classes) if prompt.target_classes else "Project-level"

        # Build the chain context header
        invoked_by_header = ""
        if step_number > 0:
            prev_link = f"`{(step_number - 1):02d}_..._prompt.md`" if step_number > 1 else "*(first step)*"
            next_link = f"`{(step_number + 1):02d}_..._prompt.md`" if step_number < total_steps else "*(last step)*"
            invoked_by_header = f"""---

## Chain Context

| Field | Value |
|-------|-------|
| **Invoked By** | `00_master_prompt.md` |
| **Step** | {step_number:02d} of {total_steps:02d} |
| **Previous Step** | {prev_link} |
| **Next Step** | {next_link} |

Once this step is complete, output: `[STEP {step_number:02d} COMPLETE] -- [one-line summary]` and proceed to Step {step_number + 1:02d}.

---

"""

        return f"""# Prompt: Step {step_number:02d}/{total_steps:02d} -- {prompt.prompt_type.value.upper().replace('_', ' ')}

{invoked_by_header}## Purpose
{prompt.purpose}

## Conditional Trigger
> {prompt.conditional_trigger}

## Target Classes
{targets}

---

## Hard Rules (Mandatory)
{hard_rules_md}

## Soft Rules (Recommended)
{soft_rules_md}

---

## Execution Steps
{steps_md}

---

## Prompt Template

{prompt.template_body}

---

*Generated by MD Agent Prompt Orchestrator v2.0*
"""
