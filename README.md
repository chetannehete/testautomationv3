# MD Agent — Prompt Orchestration System for Spring Boot Microservices

> **Automatically analyze Java/Spring Boot codebases and generate highly structured, reusable LLM prompts for test cases, documentation, C4 architecture diagrams, and run arguments.**

## 🎯 Overview (v2.0)

MD Agent has been redesigned in v2.0 to be a **Master Prompt Orchestrator**. Instead of generating final code directly (or generating hundreds of tiny per-class prompts), it generates exactly **ONE generic, highly robust execution prompt per task type**.

It does this by:
1. **Parsing** Java source files building an extended AST (now supporting Java 14+ records, Java 17+ sealed classes, inner classes, and full annotation value extraction).
2. **Detecting** Spring Boot architectural patterns (Controllers, Services, Repositories, Messaging, Security, etc.).
3. **Evaluating** conditional rules to determine which prompt types are needed.
4. **Generating** ONE generic prompt per type (e.g. one `unit_test_prompt.md`), each containing:
    - A comprehensive Class Inventory table
    - Strict, class-agnostic Hard Rules
    - Recommended Soft Rules
    - A step-by-step execution plan
    - A universal template string for the LLM to process every class in the inventory
5. **Orchestrating** the entire flow with a `00_master_prompt.md` that instructs the LLM to execute the child prompts sequentially.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the full prompt orchestration system
python -m md_agent orchestrate samples/ -o test_output_v2 -n MyProject
```

## 📋 Commands

| Command | Description |
|---------|-------------|
| `orchestrate <path>` | **Primary.** Analyze codebase and generate all prompt files |
| `execute <path>` | Process the generated prompts using an LLM (requires API keys) |

*(Note: Legacy commands `generate`, `testcases`, and `docs` have been removed in v2.0).*

### `orchestrate` Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output-dir` | `-o` | `./output` | Output directory for prompt files |
| `--project-name` | `-n` | auto | Project name (auto-detected from path) |
| `--recursive` | `-r` | `True` | Scan directories recursively |

## 🏗 Architecture & Prompt System

```
┌─────────────────────────────────────────────────────────────┐
│                   Master Prompt Orchestrator                 │
│                                                             │
│  ┌──────────┐   ┌──────────────┐   ┌───────────────────┐   │
│  │ Enhanced │──▶│  Spring Boot │──▶│  Conditional Rule │   │
│  │ Parser   │   │  Detector    │   │  Evaluator        │   │
│  └──────────┘   └──────────────┘   └───────────────────┘   │
│                                            │                │
│             Generates strictly ONE file per Prompt Type     │
│                    ┌───────────────────────┼───────┐        │
│                    ▼           ▼           ▼       ▼        │
│              ┌──────────┐ ┌────────┐ ┌────────┐ ┌──────┐   │
│              │Unit Test │ │  Integ │ │  Doc   │ │ C4   │   │
│              │ Prompt   │ │  Test  │ │ Prompt │ │Prompt│   │
│              └──────────┘ └────────┘ └────────┘ └──────┘   │
│                    │           │           │       │        │
│                    ▼           ▼           ▼       ▼        │
│            01_unit_test...  02_integ...  03_doc... 04_c4... │
└───────────────────────────────▲─────────────────────────────┘
                                │
                      00_master_prompt.md (Drives all child tasks)
```

## 🛠 Enhanced Rule System

MD Agent v2.0 introduces over 40 new explicit Hard and Soft Rules across all prompt types to ensure the LLM output is extremely high quality, robust, and safe.

| Prompt Type | Key Hard Rules Enforced |
|-------------|-------------------------|
| **Global** | Must output compilable code, strictly sequential steps, Google Java formatting. |
| **Unit Tests** | AAA pattern, `@DisplayName`, Test class name matching exactly, specific Mockito stubbing/verification rules. |
| **Integration** | `@SpringBootTest` / `@WebMvcTest` depending on slice, TestContainers for external DBs, validate proper JSON error responses. |
| **E2E Tests** | Must verify *database state* after HTTP requests, test idempotency, use unique test data. |
| **Documentation**| Specific Markdown hierarchy, include Mermaid data flow diagrams, curl examples for every endpoint. |
| **C4 Diagrams** | PlantUML syntax required, Context, Container, and Component diagrams, show async messaging with dashed arrows. |
| **Run Arguments**| Include Graceful Shutdown configs, JVM tuning, Spring profile bindings, Docker/K8s examples. |

*(All rule outputs are strictly text-based. Emojis have been explicitly banned from the prompt output logic for cleaner parsing).*

## 🔍 Enhanced Java Parser Capabilities

The `java_parser.py` has been upgraded to handle modern Java and complex Spring patterns:
- **Java 14+ Records:** Detects `record` definitions.
- **Java 17+ Sealed Classes:** Detects `sealed`, `non-sealed`, and `permits` clauses.
- **Inner Classes:** Recursively parses nested class hierarchies.
- **Generic Types:** Extracts generic parameters (e.g. `<T extends Comparable<T>>`).
- **Annotation Values:** Correctly extracts values like `@RequestMapping("/api/v1")` and `@Value("${app.config}")` without relying purely on naming heuristics.
- **Initializers & Interfaces:** Detects `static {}` blocks and `default` interface methods.

## 📊 Output

After running `orchestrate`, the output directory contains the generic execution prompts:

```
test_output_v2/
├── 00_master_prompt.md           # Root prompt driving LLM sequential execution
├── 00_orchestration_report.md    # Feature detection summary & component inventory
├── 01_unit_test_prompt.md        # ONE prompt covering ALL testable classes
├── 02_integration_test_prompt.md # ONE prompt covering API/DB/Messaging
├── 03_e2e_test_prompt.md         # Full E2E tests
├── 04_documentation_prompt.md    # Architecture and API documentation
├── 05_c4_architecture_prompt.md  # C4 PlantUML generation
└── 06_run_arguments_prompt.md    # Environments, JVM, CLI args
```
