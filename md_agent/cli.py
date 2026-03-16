"""
CLI entry point for the MD Agent.

Commands:
    python -m md_agent orchestrate <path>    # Full prompt orchestration (NEW)
    python -m md_agent generate <path>       # Legacy: both test cases + docs
    python -m md_agent testcases <path>      # Legacy: test cases only
    python -m md_agent docs <path>           # Legacy: documentation only
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import click

from md_agent.java_parser import discover_java_files, parse_java_file


@click.group()
@click.version_option(version="2.0.0")
def cli():
    """MD Agent — Prompt Orchestration System for Spring Boot Microservices.

    Analyzes Java/Spring Boot codebases and generates structured LLM prompts
    for test cases, documentation, C4 architecture diagrams, and run arguments.
    """
    pass


# ═══════════════════════════════════════════════════════════════════════
#  PRIMARY COMMAND: orchestrate
# ═══════════════════════════════════════════════════════════════════════

@cli.command()
@click.argument("path")
@click.option("--output-dir", "-o", default="output", help="Output directory for generated prompt files")
@click.option("--project-name", "-n", default=None, help="Project name (auto-detected if omitted)")
@click.option("--recursive/--no-recursive", "-r/-R", default=True, help="Recursively scan directories")
def orchestrate(path, output_dir, project_name, recursive):
    """Run the full Prompt Orchestration System.

    Analyzes a Spring Boot codebase and generates targeted LLM prompts
    for unit tests, integration tests, E2E tests, documentation,
    C4 architecture diagrams, and run arguments.
    """
    from md_agent.orchestrator import PromptOrchestrator

    java_files = discover_java_files(path, recursive=recursive)
    if not java_files:
        click.secho(f"[WARN] No .java files found at: {path}", fg="yellow")
        sys.exit(1)

    click.echo(f"[*] Found {len(java_files)} Java file(s)")

    # Parse all files
    all_classes = []
    for jf in java_files:
        click.echo(f"  [-] Parsing: {Path(jf).name}")
        try:
            classes = parse_java_file(jf)
            all_classes.extend(classes)
        except Exception as e:
            click.secho(f"     [X] Parse error: {e}", fg="red")

    if not all_classes:
        click.secho("[WARN] No Java classes found after parsing.", fg="yellow")
        sys.exit(1)

    click.echo(f"\n[*] Parsed {len(all_classes)} class(es) total")

    # Auto-detect project name from path
    if not project_name:
        project_name = Path(path).resolve().name
        if project_name in (".", "src", "main", "java"):
            project_name = Path(path).resolve().parent.name

    # Run orchestrator
    click.echo(f"\n[*] Running Prompt Orchestrator for: {project_name}")
    click.echo("-" * 50)

    orchestrator = PromptOrchestrator(project_name=project_name)

    # Step 1: Analyze
    click.echo("\n[*] Step 1: Analyzing codebase...")
    analysis = orchestrator.analyze(all_classes)
    features = analysis.features
    click.echo(f"   Controllers: {features.controller_count}")
    click.echo(f"   Services:    {features.service_count}")
    click.echo(f"   Repositories:{features.repository_count}")
    click.echo(f"   Entities:    {features.entity_count}")
    click.echo(f"   Database:    {'[OK] ' + ', '.join(features.database_types) if features.has_database else '[FAIL]'}")
    click.echo(f"   Messaging:   {'[OK] Kafka' if features.has_kafka else '[OK] RabbitMQ' if features.has_rabbitmq else '[FAIL]'}")
    click.echo(f"   Security:    {'[OK]' if features.has_security else '[FAIL]'}")

    # Step 2: Plan
    click.echo("\n[*] Step 2: Planning execution...")
    plan = orchestrator.plan_execution()
    click.echo(f"   Conditions evaluated: {len(plan.conditions_met)}")
    for cond, met in plan.conditions_met.items():
        status = click.style("[OK]", fg="green") if met else click.style("[FAIL]", fg="red")
        click.echo(f"   {status} {cond}")
    click.echo(f"   Prompts to generate: {len(plan.execution_order)}")
    for i, pt in enumerate(plan.execution_order, 1):
        click.echo(f"     {i}. {pt.value}")

    # Step 3: Generate
    click.echo("\n[*] Step 3: Generating prompts...")
    prompts = orchestrator.generate_prompts()
    for p in prompts:
        click.secho(f"   [+] {p.prompt_type.value}: {p.purpose}", fg="green")

    # Step 4: Write
    click.echo(f"\n[*] Step 4: Writing output to {output_dir}/...")
    written = orchestrator.write_output(output_dir)
    for filename, filepath in written.items():
        click.echo(f"   [-] {filename}")

    click.echo(f"\n{'=' * 50}")
    click.secho(
        f"[OK] Done! Generated {len(prompts)} prompt(s) + orchestration report -> {output_dir}/",
        fg="bright_green", bold=True,
    )


# ═══════════════════════════════════════════════════════════════════════
#  NEW COMMAND: execute
# ═══════════════════════════════════════════════════════════════════════

@cli.command()
@click.argument("prompts_dir", default="output")
@click.option("--provider", "-p", default="gemini",
              type=click.Choice(["gemini", "openai", "anthropic"], case_sensitive=False),
              help="LLM provider to use (default: gemini)")
@click.option("--model", "-m", default=None,
              help="Model name (default: gemini-3-flash-preview / gpt-4o / claude-3-5-sonnet)")
@click.option("--api-key", "-k", default=None, envvar="LLM_API_KEY",
              help="API key (falls back to GEMINI/OPENAI/ANTHROPIC_API_KEY env vars)")
@click.option("--generated-dir", "-g", default="generated",
              help="Directory to save generated files (default: ./generated)")
@click.option("--step", "-s", default=None, type=int,
              help="Run only this step number (e.g. --step 1). Omit to run all.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Preview session without calling the LLM API")
@click.option("--delay", default=2.0, type=float,
              help="Seconds to wait between steps (default: 2.0, reduce for faster models)")
def execute(prompts_dir, provider, model, api_key, generated_dir, step, dry_run, delay):
    """Run the master prompt through an LLM and save generated artifacts.

    \b
    Examples:
      python -m md_agent execute output/ --dry-run
      python -m md_agent execute output/ --provider gemini
      python -m md_agent execute output/ --provider openai --step 1
    """
    from md_agent.llm_runner import LLMRunner, DryRunLLMRunner

    # ── Resolve API keys per provider ──
    _env_vars = {
        "gemini":    "GEMINI_API_KEY",
        "openai":    "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    resolved_key = api_key or os.environ.get(_env_vars.get(provider, ""), "")

    click.echo(f"\n[*] MD Agent — LLM Execution Engine")
    click.echo("-" * 50)

    if dry_run:
        click.secho("  Mode: DRY RUN (no LLM calls)", fg="yellow")
        runner = DryRunLLMRunner()
    else:
        if not resolved_key:
            click.secho(
                f"[WARN] No API key found for provider '{provider}'.\n"
                f"   Set ${_env_vars[provider]} or pass --api-key",
                fg="red",
            )
            sys.exit(1)
        click.secho(f"  Provider: {provider.upper()}", fg="cyan")
        try:
            runner = LLMRunner(
                provider=provider,
                api_key=resolved_key,
                model=model,
                delay_between_steps=delay,
            )
            click.echo(f"  Model:    {runner.model}")
        except (ValueError, ImportError) as e:
            click.secho(f"[X] {e}", fg="red")
            sys.exit(1)

    click.echo(f"  Prompts:  {prompts_dir}/")
    click.echo(f"  Output:   {generated_dir}/")
    if step:
        click.echo(f"  Step:     {step:02d} only")
    click.echo("-" * 50)

    # ── Progress callbacks ──
    def on_step_start(step_num, filename):
        click.echo(f"\n[*] Step {step_num:02d} -> {filename}")

    def on_step_done(result):
        if result.success:
            if result.extracted_files:
                for fname, _ in result.extracted_files:
                    click.secho(f"   [-] Saved: {fname}", fg="green")
            else:
                click.secho(f"   [WARN] No code blocks extracted", fg="yellow")
            click.secho(f"   [OK] Step {result.step_number:02d} complete", fg="bright_green")
        else:
            click.secho(f"   [FAIL] Step {result.step_number:02d} failed: {result.error}", fg="red")

    # ── Run session ──
    try:
        session = runner.run(
            prompts_dir=prompts_dir,
            generated_dir=generated_dir,
            only_step=step,
            on_step_start=on_step_start,
            on_step_done=on_step_done,
        )
    except FileNotFoundError as e:
        click.secho(f"[X] {e}", fg="red")
        sys.exit(1)
    except Exception as e:
        click.secho(f"[FAIL] Session failed: {e}", fg="red")
        sys.exit(1)

    # ── Final summary ──
    total = len(session.steps)
    ok = sum(1 for s in session.steps if s.success)
    failed = total - ok
    artifacts = sum(len(s.extracted_files) for s in session.steps)

    click.echo(f"\n{'=' * 50}")
    click.secho(
        f"[OK] Session complete! {ok}/{total} steps succeeded, "
        f"{artifacts} artifact(s) saved -> {generated_dir}/",
        fg="bright_green", bold=True,
    )
    if failed:
        click.secho(f"[WARN] {failed} step(s) failed -- check session_log.md", fg="yellow")

    # Print step summary table
    click.echo("\n[*] Step Summary:")
    click.echo("  " + "-" * 60)
    click.echo(f"  {'Step':<6} {'Status':<8} {'Files':<6} {'Purpose'}")
    click.echo("  " + "-" * 60)
    for s in session.steps:
        status = "[OK]" if s.success else "[FAIL]"
        files = str(len(s.extracted_files))
        purpose_short = s.purpose[:46] + ".." if len(s.purpose) > 46 else s.purpose
        click.echo(f"  {s.step_number:02d}     {status:<8} {files:<6} {purpose_short}")
    click.echo("  " + "-" * 60)


