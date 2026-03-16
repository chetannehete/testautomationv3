# Improve MD Agent Prompt System, Java Parser, and Documentation

Clean up legacy code, make prompts generic and reusable per type, add comprehensive hard/soft rules, enhance Java parser, and update documentation.

## Proposed Changes

### Legacy Code Removal

#### [DELETE] [analyzer.py](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/analyzer.py)
Remove entirely — this is the old rule-based test case / doc generator. Superseded by the orchestrator + prompt_templates system.

#### [DELETE] [md_renderer.py](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/md_renderer.py)
Remove entirely — Jinja2 renderer only used by the legacy [analyzer.py](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/analyzer.py) flow.

#### [MODIFY] [models.py](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/models.py)
- Remove `TestCase`, `TestSuite`, `DocSection`, `Documentation` dataclasses (lines 224–259, marked LEGACY)
- These are only used by the deleted [analyzer.py](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/analyzer.py)

#### [MODIFY] [cli.py](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/cli.py)
- Remove legacy commands: [generate](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/orchestrator.py#151-178), `testcases`, `docs`, and the shared [_run()](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/orchestrator.py#311-315) helper (lines 264–338)
- Remove imports of `generate_test_suite`, [generate_documentation](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/orchestrator.py#301-305), `render_test_cases`, `render_documentation`
- Keep [orchestrate](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/cli.py#37-126) and [execute](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/cli.py#132-258) commands

#### [MODIFY] [__init__.py](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/__init__.py)
- Update exports to reflect removed modules

---

### Generic Reusable Prompts (Per-Type, Not Per-Class)

#### [MODIFY] [prompt_templates.py](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/prompt_templates.py)

**Unit Test Prompt** — change [build_unit_test_prompt(component, analysis)](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/prompt_templates.py#37-235) to [build_unit_test_prompt(components: List[SpringComponent], analysis)](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/prompt_templates.py#37-235):
- Accepts ALL testable components at once
- Builds a single generic prompt with a **class inventory table** listing each class, its methods, dependencies
- The rules are class-independent; the LLM receives ONE prompt to generate tests for ALL classes
- The template includes a loop: "For each class listed below, generate a corresponding `{ClassName}Test.java`"

**Integration Test Prompt** — similarly aggregate:
- Change to [build_integration_test_prompt(components, analysis, test_type)](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/prompt_templates.py#241-492) accepting a list
- Build one prompt per test_type (api/db/messaging) covering ALL relevant components

**All other prompts** (E2E, Documentation, C4, Run Args) — already project-level, no change needed.

#### [MODIFY] [orchestrator.py](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/orchestrator.py)
- Change `_generate_unit_test_prompts` to collect all testable components into a single list, call [build_unit_test_prompt(all_testable, analysis)](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/prompt_templates.py#37-235) once → append one prompt
- Change `_generate_integration_test_prompts` similarly — one call per test_type with all relevant components

---

### Add More Hard & Soft Rules

#### [MODIFY] [prompt_templates.py](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/prompt_templates.py)

**Unit Test — New Hard Rules:**
| ID | Rule |
|----|------|
| UT-H11 | Never use `@SuppressWarnings` to hide test warnings |
| UT-H12 | Do not use `Thread.sleep()` in unit tests; use `Awaitility` if async testing needed |
| UT-H13 | Assert with specific matchers (assertEquals, assertTrue) — avoid generic `assertNotNull` alone |
| UT-H14 | Each test must have exactly one logical assertion (or closely related group, e.g., assertAll) |
| UT-H15 | Do not initialize mocks manually — rely on `@ExtendWith(MockitoExtension.class)` only |
| UT-H16 | Do not use `Mockito.any()` as a stub when the exact argument is knowable |

**Unit Test — New Soft Rules:**
| ID | Rule |
|----|------|
| UT-S8 | Use `@Timeout(5)` on long-running tests to prevent CI hangs |
| UT-S9 | Use `AssertJ` fluent assertions when available in the classpath |
| UT-S10 | Use `@RepeatedTest` for non-deterministic scenarios |
| UT-S11 | Include a test for thread-safety if the class uses shared mutable state |
| UT-S12 | Prefer `verify(mock, times(1))` over `verify(mock)` for explicit intent |

**Integration Test — New Hard Rules:**
| ID | Rule |
|----|------|
| IT-H9 | Always specify `@Timeout` on integration tests to prevent CI hangs |
| IT-H10 | Use `@MockBean` only for external services, never for the class under test |
| IT-H11 | Validate response content-type (application/json) in API tests |
| IT-H12 | Test error responses return proper ProblemDetail/error JSON structure |

**Integration Test — New Soft Rules:**
| ID | Rule |
|----|------|
| IT-S6 | Use `@Testcontainers` annotation with `@Container` fields for cleaner lifecycle |
| IT-S7 | Use `@AutoConfigureJsonTesters` for response body type-safe assertions |
| IT-S8 | Include concurrent request test for thread-safety of controllers |
| IT-S9 | Use `WireMock` for stubbing external HTTP dependencies |

**E2E — New Hard Rules:**
| ID | Rule |
|----|------|
| E2E-H7 | Include database state verification (not just HTTP responses) |
| E2E-H8 | Test idempotency — calling the same request twice should be safe |
| E2E-H9 | Use unique test data per test run to avoid flaky shared-state failures |

**E2E — New Soft Rules:**
| ID | Rule |
|----|------|
| E2E-S4 | Include response time assertions for performance-critical endpoints |
| E2E-S5 | Test pagination and large result sets |
| E2E-S6 | Include cleanup/teardown that runs regardless of test outcome (use `@AfterAll`) |

**Documentation — New Hard Rules:**
| ID | Rule |
|----|------|
| DOC-H8 | Include a dependency diagram (Mermaid) showing inter-service dependencies |
| DOC-H9 | Document all Spring profiles and their effect on behavior |
| DOC-H10 | Include a troubleshooting section with common errors and fixes |

**Documentation — New Soft Rules:**
| ID | Rule |
|----|------|
| DOC-S6 | Include curl examples for every REST endpoint |
| DOC-S7 | Add a "Known Limitations" section |
| DOC-S8 | Include a changelog template |

**C4 — New Hard/Soft Rules:**
| ID | Rule | Type |
|----|------|------|
| C4-H8 | Include deployment diagram if Kubernetes/Docker annotations are detected | Hard |
| C4-H9 | Show async communication (messaging) with dashed arrows | Hard |
| C4-S5 | Include a dynamic diagram for key user workflows | Soft |
| C4-S6 | Add boundary boxes for microservice groupings | Soft |

**Run Arguments — New Hard/Soft Rules:**
| ID | Rule | Type |
|----|------|------|
| RUN-H7 | Include Kubernetes deployment YAML snippet if applicable | Hard |
| RUN-H8 | Include Graceful Shutdown configuration (`server.shutdown=graceful`) | Hard |
| RUN-S5 | Add Prometheus metrics endpoint configuration | Soft |
| RUN-S6 | Include log-level tuning flags per profile | Soft |

**Global/Master — New Hard/Soft Rules:**
| ID | Rule | Type |
|----|------|------|
| GL-H7 | Use `org.springframework.boot:spring-boot-starter-test` as the only test dependency | Hard |
| GL-H8 | All generated code must follow Google Java Style Guide formatting | Hard |
| GL-H9 | Include package declaration matching the source class | Hard |
| GL-S4 | Add TODO comments for areas needing customization | Soft |
| GL-S5 | Include a README banner in the first generated file listing all output artifacts | Soft |

---

### Java Parser Enhancements

#### [MODIFY] [java_parser.py](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/java_parser.py)

1. **Inner/Nested Classes** — recurse into `ClassDeclaration.body` to find nested `ClassDeclaration` nodes; add `inner_classes: List[ClassInfo]` field to [ClassInfo](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/models.py#62-86)
2. **Generic Type Parameters** — extract `<T extends Comparable<T>>` from class declarations; add `type_parameters: List[str]` field
3. **Record Declarations** — handle `javalang.tree.RecordDeclaration` (Java 14+) if the javalang version supports it, otherwise pattern-match on source
4. **Sealed Class Detection** — detect [sealed](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/java_parser.py#278-309), `non-sealed`, `permits` keywords in modifiers
5. **Annotation Value Extraction** — parse `annotation.element` to get values like `@RequestMapping("/api/v1")`; add `annotation_values: Dict[str, str]` to relevant models
6. **Default Interface Methods** — detect `default` modifier on interface method declarations
7. **Static/Instance Initializers** — count initializer blocks; add `has_static_init: bool`, `has_instance_init: bool` to [ClassInfo](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/models.py#62-86)

#### [MODIFY] [models.py](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/models.py)
- Add new fields: [inner_classes](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/java_parser.py#311-327), [type_parameters](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/java_parser.py#165-182), `is_record`, `is_sealed`, `has_static_init`, `has_instance_init` to [ClassInfo](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/models.py#62-86)
- Add `annotation_values: Dict[str, str]` to  [MethodInfo](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/models.py#46-60) and [FieldInfo](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/models.py#35-44)

#### [MODIFY] [spring_detector.py](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/spring_detector.py)
- Use new annotation values for better `@RequestMapping` path extraction
- Detect `@Value("${...}")` annotation values for config property discovery

---

### Documentation Updates

#### [MODIFY] [README.md](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/README.md)
- Remove legacy command references
- Add detailed sections on: generic prompt architecture, rule system (hard vs soft), Java parser capabilities  
- Add a full rules reference table
- Add a "What's New" section

---

### Standard Output Layout Extraction

#### [MODIFY] [llm_runner.py](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/llm_runner.py)
- Update [_infer_filename](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/md_agent/llm_runner.py#116-141) to return relative directory paths instead of flat filenames.
- For [java](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/samples/Calculator.java) files: Use Regex to extract the `package` declaration. Return `src/test/java/{package}/{filename}`.
- For `markdown`, [md](file:///c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test%20automation/README.md), `plantuml`, `puml` files: Return `docs/{filename}`.
- For `bash`, `sh`, `yaml`, `yml` files: Return `scripts/{filename}` or `deploy/{filename}`.
- Ensure the extraction logic cleanly supports creating nested subdirectories when writing generated files to the target output directory.

---

## Verification Plan

### Automated Tests

1. **Parse test** — run the orchestrator on the existing samples directory:
```bash
cd "c:\Users\cheta\OneDrive\Desktop\aNTIGRAVITY\test automation"
python -m md_agent orchestrate samples/ -o test_output_v2 -n TestProject
```
Verify: exits 0, generates all expected prompt files, each prompt contains the new rules.

2. **Java parser validation** — Run Python to import and parse the sample Calculator.java:
```bash
python -c "from md_agent.java_parser import parse_java_file; classes = parse_java_file('samples/Calculator.java'); print(f'Parsed {len(classes)} classes'); [print(f'  {c.name}: {len(c.methods)} methods, inner={len(c.inner_classes)}') for c in classes]"
```

3. **Import sanity check** — verify no broken imports after cleanup:
```bash
python -c "import md_agent; from md_agent.cli import cli; from md_agent.orchestrator import PromptOrchestrator; from md_agent.prompt_templates import build_unit_test_prompt; print('All imports OK')"
```

### Manual Verification 
- Inspect the generated prompt files in `test_output_v2/` to confirm:
  - Each prompt type has a single file (not per-class)
  - All new hard/soft rules are present
  - The class inventory table is correct
  - No references to deleted legacy modules
