"""
Data models representing parsed Java code, Spring Boot patterns,
detected features, and all generated artifact structures.

Supports the full Prompt Orchestration System for Spring Boot microservices.

Java Parser Model Capabilities:
  - Classes, interfaces, enums, records (Java 14+)
  - Sealed classes (Java 17+)
  - Inner/nested class hierarchies
  - Generic type parameters on class declarations
  - Annotation values (e.g., @RequestMapping("/api"))
  - Static and instance initializer blocks
  - Default interface methods
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════
#  PARSED JAVA CODE MODEL
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class ParameterInfo:
    """A single method parameter."""
    name: str
    type: str


@dataclass
class FieldInfo:
    """A class-level field / member variable."""
    name: str
    type: str
    modifiers: List[str] = field(default_factory=list)
    default_value: Optional[str] = None
    annotations: List[str] = field(default_factory=list)
    annotation_values: Dict[str, str] = field(default_factory=dict)  # e.g., {"Value": "${app.name}"}


@dataclass
class MethodInfo:
    """A single method or constructor."""
    name: str
    return_type: str
    parameters: List[ParameterInfo] = field(default_factory=list)
    modifiers: List[str] = field(default_factory=list)
    exceptions: List[str] = field(default_factory=list)
    javadoc: Optional[str] = None
    is_constructor: bool = False
    annotations: List[str] = field(default_factory=list)
    annotation_values: Dict[str, str] = field(default_factory=dict)  # e.g., {"GetMapping": "/users"}
    body_lines: int = 0
    is_default: bool = False  # True for default interface methods


@dataclass
class ClassInfo:
    """Represents a single Java class / interface / enum / record."""
    name: str
    package: Optional[str] = None
    imports: List[str] = field(default_factory=list)
    modifiers: List[str] = field(default_factory=list)
    extends: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    fields: List[FieldInfo] = field(default_factory=list)
    methods: List[MethodInfo] = field(default_factory=list)
    constructors: List[MethodInfo] = field(default_factory=list)
    javadoc: Optional[str] = None
    annotations: List[str] = field(default_factory=list)
    source_file: Optional[str] = None
    # Enhanced Java parsing fields
    inner_classes: List['ClassInfo'] = field(default_factory=list)
    type_parameters: List[str] = field(default_factory=list)  # e.g., ["T", "E extends Comparable"]
    is_record: bool = False        # Java 14+ record declaration
    is_sealed: bool = False        # Java 17+ sealed class
    permits: List[str] = field(default_factory=list)  # sealed class permits list
    has_static_init: bool = False  # has static {} initializer block
    has_instance_init: bool = False  # has instance {} initializer block
    annotation_values: Dict[str, str] = field(default_factory=dict)  # class-level annotation values


# ═══════════════════════════════════════════════════════════════════════
#  SPRING BOOT PATTERN DETECTION
# ═══════════════════════════════════════════════════════════════════════

class ComponentType(str, Enum):
    """Spring Boot component categories."""
    REST_CONTROLLER = "rest_controller"
    CONTROLLER = "controller"
    SERVICE = "service"
    REPOSITORY = "repository"
    ENTITY = "entity"
    CONFIGURATION = "configuration"
    COMPONENT = "component"
    MESSAGING_LISTENER = "messaging_listener"
    MESSAGING_PRODUCER = "messaging_producer"
    SCHEDULED_TASK = "scheduled_task"
    SECURITY_CONFIG = "security_config"
    EXCEPTION_HANDLER = "exception_handler"
    DTO = "dto"
    MAPPER = "mapper"
    FILTER = "filter"
    INTERCEPTOR = "interceptor"
    APPLICATION = "application"
    TEST = "test"
    UNKNOWN = "unknown"


@dataclass
class EndpointInfo:
    """A single REST API endpoint."""
    http_method: str              # GET, POST, PUT, DELETE, PATCH
    path: str                     # URL path pattern
    method_name: str              # Java method name
    request_body_type: Optional[str] = None
    response_type: Optional[str] = None
    path_variables: List[str] = field(default_factory=list)
    query_params: List[str] = field(default_factory=list)
    produces: Optional[str] = None
    consumes: Optional[str] = None


@dataclass
class DependencyInfo:
    """An injected dependency (constructor or @Autowired)."""
    field_name: str
    type: str
    injection_method: str = "constructor"  # constructor | field | setter


@dataclass
class SpringComponent:
    """A classified Spring Boot component with extracted metadata."""
    class_info: ClassInfo
    component_type: ComponentType
    endpoints: List[EndpointInfo] = field(default_factory=list)
    dependencies: List[DependencyInfo] = field(default_factory=list)
    base_path: Optional[str] = None       # @RequestMapping base path
    profiles: List[str] = field(default_factory=list)
    config_properties: List[str] = field(default_factory=list)
    bean_methods: List[str] = field(default_factory=list)


@dataclass
class ProjectFeatures:
    """Detected project-level features from codebase analysis."""
    has_rest_controllers: bool = False
    has_database: bool = False
    has_jpa: bool = False
    has_messaging: bool = False
    has_kafka: bool = False
    has_rabbitmq: bool = False
    has_security: bool = False
    has_scheduling: bool = False
    has_caching: bool = False
    has_actuator: bool = False
    has_swagger: bool = False
    has_exception_handling: bool = False
    has_validation: bool = False
    has_feign_client: bool = False
    has_circuit_breaker: bool = False
    has_config_server: bool = False
    service_count: int = 0
    controller_count: int = 0
    repository_count: int = 0
    entity_count: int = 0
    total_classes: int = 0
    total_endpoints: int = 0
    packages: List[str] = field(default_factory=list)
    spring_profiles: List[str] = field(default_factory=list)
    database_types: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════
#  CODEBASE ANALYSIS RESULT
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class CodebaseAnalysis:
    """Complete codebase analysis result — input to the orchestrator."""
    project_name: str
    components: List[SpringComponent] = field(default_factory=list)
    features: ProjectFeatures = field(default_factory=ProjectFeatures)
    class_dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    all_classes: List[ClassInfo] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════
#  PROMPT SYSTEM MODELS
# ═══════════════════════════════════════════════════════════════════════

class PromptType(str, Enum):
    """Types of prompts the system generates."""
    MASTER = "master"
    UNIT_TEST = "unit_test"
    INTEGRATION_TEST = "integration_test"
    E2E_TEST = "e2e_test"
    DOCUMENTATION = "documentation"
    C4_ARCHITECTURE = "c4_architecture"
    RUN_ARGUMENTS = "run_arguments"


@dataclass
class PromptRule:
    """A rule (hard or soft) attached to a prompt."""
    id: str
    description: str
    is_hard: bool  # True = hard rule (mandatory), False = soft rule (recommended)


@dataclass
class GeneratedPrompt:
    """A fully constructed prompt ready for LLM execution."""
    prompt_type: PromptType
    purpose: str
    hard_rules: List[PromptRule] = field(default_factory=list)
    soft_rules: List[PromptRule] = field(default_factory=list)
    context: str = ""              # code context injected into prompt
    template_body: str = ""        # the rendered prompt text
    target_classes: List[str] = field(default_factory=list)
    conditional_trigger: str = ""  # why this prompt was triggered
    execution_steps: List[str] = field(default_factory=list)


@dataclass
class OrchestrationPlan:
    """The master orchestration plan — controls which prompts to generate."""
    project_name: str
    features: ProjectFeatures
    prompts_to_generate: List[PromptType] = field(default_factory=list)
    conditions_met: Dict[str, bool] = field(default_factory=dict)
    execution_order: List[PromptType] = field(default_factory=list)



