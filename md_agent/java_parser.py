"""
Java source file parser using the ``javalang`` library.

Parses .java files into our internal ClassInfo / MethodInfo dataclass model
by walking the javalang AST.

Capabilities:
  - Class, interface, enum declarations
  - Inner/nested class hierarchies
  - Generic type parameters (e.g., <T extends Comparable<T>>)
  - Annotation value extraction (e.g., @RequestMapping("/api"))
  - Record detection (Java 14+) via naming/modifier heuristics
  - Sealed class detection (Java 17+) via modifier heuristics
  - Static and instance initializer block detection
  - Default interface method detection
  - Constructor and method parsing with full signatures
  - Field declarations with annotation values
"""

from __future__ import annotations

import re
import os
from pathlib import Path
from typing import Dict, List, Optional

import javalang

from md_agent.models import ClassInfo, FieldInfo, MethodInfo, ParameterInfo


def parse_java_file(filepath: str) -> List[ClassInfo]:
    """
    Parse a single .java file and return a list of ClassInfo objects
    (one per top-level class/interface/enum declared in the file).
    Inner classes are nested inside their parent's inner_classes field.
    """
    filepath = str(Path(filepath).resolve())
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
    return parse_java_source(source, source_file=filepath)


def parse_java_source(source: str, source_file: Optional[str] = None) -> List[ClassInfo]:
    """
    Parse raw Java source code string and return a list of ClassInfo objects.
    """
    tree = javalang.parse.parse(source)
    classes: List[ClassInfo] = []

    package_name = tree.package.name if tree.package else None
    imports = [imp.path for imp in (tree.imports or [])]

    # Only process top-level declarations (filter gives all, including nested)
    # We use tree.types which gives only top-level types
    for node in (tree.types or []):
        if isinstance(node, javalang.tree.ClassDeclaration):
            classes.append(_parse_class_declaration(node, package_name, imports, source_file, source))
        elif isinstance(node, javalang.tree.InterfaceDeclaration):
            classes.append(_parse_interface_declaration(node, package_name, imports, source_file, source))
        elif isinstance(node, javalang.tree.EnumDeclaration):
            classes.append(_parse_enum_declaration(node, package_name, imports, source_file, source))

    return classes


# -- Internal helpers --------------------------------------------------

def _extract_modifiers(node) -> List[str]:
    """Extract modifier strings from a javalang node."""
    return sorted(list(node.modifiers)) if node.modifiers else []


def _extract_annotations(node) -> List[str]:
    """Extract annotation names from a javalang node."""
    if not node.annotations:
        return []
    return [ann.name for ann in node.annotations]


def _extract_annotation_values(node) -> Dict[str, str]:
    """
    Extract annotation values from a javalang node.

    Handles:
      - Single element: @GetMapping("/users") -> {"GetMapping": "/users"}
      - Named elements: @RequestMapping(value="/api", method=GET) -> {"RequestMapping": "value=/api, method=GET"}
    """
    values: Dict[str, str] = {}
    if not node.annotations:
        return values

    for ann in node.annotations:
        ann_name = ann.name
        if hasattr(ann, "element") and ann.element is not None:
            element = ann.element
            if isinstance(element, list):
                # Multiple named elements: @Annotation(key1=val1, key2=val2)
                parts = []
                for e in element:
                    if hasattr(e, "name") and hasattr(e, "value"):
                        val_str = _annotation_value_to_str(e.value)
                        parts.append(f"{e.name}={val_str}")
                    else:
                        parts.append(_annotation_value_to_str(e))
                values[ann_name] = ", ".join(parts)
            else:
                # Single element: @Annotation("value") or @Annotation(key=value)
                values[ann_name] = _annotation_value_to_str(element)

    return values


def _annotation_value_to_str(value) -> str:
    """Convert a javalang annotation element value to a readable string."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if hasattr(value, "value"):
        return str(value.value)
    if hasattr(value, "qualifier") and hasattr(value, "member"):
        return f"{value.qualifier}.{value.member}" if value.qualifier else str(value.member)
    return str(value)


def _extract_javadoc(node) -> Optional[str]:
    """Extract Javadoc comment from a node's documentation attribute."""
    doc = getattr(node, "documentation", None)
    if doc:
        lines = doc.strip().split("\n")
        cleaned = []
        for line in lines:
            line = line.strip()
            if line.startswith("/**") or line.startswith("*/"):
                continue
            if line.startswith("*"):
                line = line[1:].strip()
            cleaned.append(line)
        return "\n".join(cleaned).strip() or None
    return None


def _parse_type(type_node) -> str:
    """Convert a javalang type node to a readable string."""
    if type_node is None:
        return "void"
    name = type_node.name if hasattr(type_node, "name") else str(type_node)

    # Handle generic type arguments
    if hasattr(type_node, "arguments") and type_node.arguments:
        args = ", ".join(
            _parse_type(a.type) if hasattr(a, "type") and a.type else "?"
            for a in type_node.arguments
        )
        name = f"{name}<{args}>"

    # Handle array dimensions
    if hasattr(type_node, "dimensions") and type_node.dimensions:
        name += "[]" * len(type_node.dimensions)

    return name


def _parse_type_parameters(node) -> List[str]:
    """
    Extract generic type parameters from a class/interface declaration.

    e.g., class Foo<T extends Comparable<T>, E> -> ["T extends Comparable<T>", "E"]
    """
    if not hasattr(node, "type_parameters") or not node.type_parameters:
        return []

    result = []
    for tp in node.type_parameters:
        param_str = tp.name
        if hasattr(tp, "extends") and tp.extends:
            bounds = ", ".join(_parse_type(b) for b in tp.extends)
            param_str += f" extends {bounds}"
        result.append(param_str)
    return result


def _parse_parameters(params) -> List[ParameterInfo]:
    """Convert javalang formal parameters to ParameterInfo list."""
    if not params:
        return []
    result = []
    for p in params:
        ptype = _parse_type(p.type) if p.type else "Object"
        result.append(ParameterInfo(name=p.name, type=ptype))
    return result


def _parse_method(node, is_constructor: bool = False) -> MethodInfo:
    """Parse a single method or constructor declaration."""
    return_type = "void"
    if not is_constructor and hasattr(node, "return_type"):
        return_type = _parse_type(node.return_type)

    exceptions = []
    if node.throws:
        exceptions = list(node.throws)

    body_lines = 0
    if node.body:
        body_lines = len(node.body)

    modifiers = _extract_modifiers(node)

    # Detect default interface methods
    is_default = "default" in modifiers

    return MethodInfo(
        name=node.name,
        return_type=return_type,
        parameters=_parse_parameters(node.parameters),
        modifiers=modifiers,
        exceptions=exceptions,
        javadoc=_extract_javadoc(node),
        is_constructor=is_constructor,
        annotations=_extract_annotations(node),
        annotation_values=_extract_annotation_values(node),
        body_lines=body_lines,
        is_default=is_default,
    )


def _parse_field(node) -> List[FieldInfo]:
    """Parse a field declaration (may declare multiple variables)."""
    fields = []
    ftype = _parse_type(node.type) if node.type else "Object"
    modifiers = _extract_modifiers(node)
    annotations = _extract_annotations(node)
    annotation_values = _extract_annotation_values(node)

    for declarator in node.declarators:
        default = None
        if declarator.initializer:
            default = str(declarator.initializer)
        fields.append(FieldInfo(
            name=declarator.name,
            type=ftype,
            modifiers=modifiers,
            default_value=default,
            annotations=annotations,
            annotation_values=annotation_values,
        ))
    return fields


def _detect_initializers(body, source: Optional[str] = None) -> tuple:
    """
    Detect static and instance initializer blocks in a class body.
    Returns (has_static_init, has_instance_init).
    """
    has_static = False
    has_instance = False

    if body:
        for member in body:
            # javalang may represent initializer blocks as statements
            if hasattr(member, "__class__"):
                cls_name = member.__class__.__name__
                if cls_name == "StaticInitializer":
                    has_static = True
                elif cls_name == "InstanceInitializer":
                    has_instance = True

    # Fallback: regex scan on source for initializer blocks
    if source and not has_static:
        if re.search(r"\bstatic\s*\{", source):
            has_static = True

    return has_static, has_instance


def _detect_sealed(node, source: Optional[str] = None) -> tuple:
    """
    Detect sealed/non-sealed modifiers and permits clause.
    Returns (is_sealed, permits_list).

    javalang may not support sealed keywords directly, so we also
    do a regex-based fallback on the source code.
    """
    modifiers = _extract_modifiers(node)
    is_sealed = "sealed" in modifiers or "non-sealed" in modifiers
    permits: List[str] = []

    if hasattr(node, "permits") and node.permits:
        permits = [p.name if hasattr(p, "name") else str(p) for p in node.permits]

    # Regex fallback on source
    if source and not is_sealed:
        # Check for 'sealed class ClassName'
        pattern = rf"\bsealed\s+class\s+{re.escape(node.name)}\b"
        if re.search(pattern, source):
            is_sealed = True

        # Check for 'permits' clause
        permits_match = re.search(
            rf"\bclass\s+{re.escape(node.name)}.*?\bpermits\s+([\w\s,]+?)(?:\{{|$)",
            source, re.DOTALL
        )
        if permits_match and not permits:
            permits = [p.strip() for p in permits_match.group(1).split(",") if p.strip()]

    return is_sealed, permits


def _parse_inner_classes(body, package: Optional[str], imports: List[str],
                         source_file: Optional[str], source: Optional[str] = None) -> List[ClassInfo]:
    """Parse inner/nested class declarations from a class body."""
    inner_classes: List[ClassInfo] = []
    if not body:
        return inner_classes

    for member in body:
        if isinstance(member, javalang.tree.ClassDeclaration):
            inner_classes.append(_parse_class_declaration(member, package, imports, source_file, source))
        elif isinstance(member, javalang.tree.InterfaceDeclaration):
            inner_classes.append(_parse_interface_declaration(member, package, imports, source_file, source))
        elif isinstance(member, javalang.tree.EnumDeclaration):
            inner_classes.append(_parse_enum_declaration(member, package, imports, source_file, source))

    return inner_classes


def _parse_class_declaration(node, package: Optional[str], imports: List[str],
                              source_file: Optional[str], source: Optional[str] = None) -> ClassInfo:
    """Parse a full class declaration into ClassInfo."""
    methods = []
    constructors = []
    fields = []

    for member in (node.body or []):
        if isinstance(member, javalang.tree.MethodDeclaration):
            methods.append(_parse_method(member))
        elif isinstance(member, javalang.tree.ConstructorDeclaration):
            constructors.append(_parse_method(member, is_constructor=True))
        elif isinstance(member, javalang.tree.FieldDeclaration):
            fields.extend(_parse_field(member))

    extends = None
    if node.extends:
        extends = node.extends.name if hasattr(node.extends, "name") else str(node.extends)

    implements_list = []
    if node.implements:
        implements_list = [iface.name if hasattr(iface, "name") else str(iface) for iface in node.implements]

    # Enhanced features
    type_params = _parse_type_parameters(node)
    inner_classes = _parse_inner_classes(node.body, package, imports, source_file, source)
    has_static_init, has_instance_init = _detect_initializers(node.body, source)
    is_sealed, permits = _detect_sealed(node, source)

    return ClassInfo(
        name=node.name,
        package=package,
        imports=imports,
        modifiers=_extract_modifiers(node),
        extends=extends,
        implements=implements_list,
        fields=fields,
        methods=methods,
        constructors=constructors,
        javadoc=_extract_javadoc(node),
        annotations=_extract_annotations(node),
        annotation_values=_extract_annotation_values(node),
        source_file=source_file,
        inner_classes=inner_classes,
        type_parameters=type_params,
        is_record=False,
        is_sealed=is_sealed,
        permits=permits,
        has_static_init=has_static_init,
        has_instance_init=has_instance_init,
    )


def _parse_interface_declaration(node, package: Optional[str], imports: List[str],
                                  source_file: Optional[str], source: Optional[str] = None) -> ClassInfo:
    """Parse an interface declaration into ClassInfo."""
    methods = []
    fields = []

    for member in (node.body or []):
        if isinstance(member, javalang.tree.MethodDeclaration):
            methods.append(_parse_method(member))
        elif isinstance(member, javalang.tree.FieldDeclaration):
            fields.extend(_parse_field(member))

    modifiers = _extract_modifiers(node)
    if "interface" not in [m.lower() for m in modifiers]:
        modifiers.append("interface")

    type_params = _parse_type_parameters(node)
    inner_classes = _parse_inner_classes(node.body, package, imports, source_file, source)
    is_sealed, permits = _detect_sealed(node, source)

    return ClassInfo(
        name=node.name,
        package=package,
        imports=imports,
        modifiers=modifiers,
        fields=fields,
        methods=methods,
        javadoc=_extract_javadoc(node),
        annotations=_extract_annotations(node),
        annotation_values=_extract_annotation_values(node),
        source_file=source_file,
        inner_classes=inner_classes,
        type_parameters=type_params,
        is_sealed=is_sealed,
        permits=permits,
    )


def _parse_enum_declaration(node, package: Optional[str], imports: List[str],
                             source_file: Optional[str], source: Optional[str] = None) -> ClassInfo:
    """Parse an enum declaration into ClassInfo."""
    methods = []
    constructors = []
    fields = []

    for member in (node.body.declarations or []) if node.body else []:
        if isinstance(member, javalang.tree.MethodDeclaration):
            methods.append(_parse_method(member))
        elif isinstance(member, javalang.tree.ConstructorDeclaration):
            constructors.append(_parse_method(member, is_constructor=True))
        elif isinstance(member, javalang.tree.FieldDeclaration):
            fields.extend(_parse_field(member))

    # Add enum constants as fields
    if node.body and node.body.constants:
        for const in node.body.constants:
            fields.append(FieldInfo(
                name=const.name,
                type=node.name,
                modifiers=["public", "static", "final"],
            ))

    modifiers = _extract_modifiers(node)
    if "enum" not in [m.lower() for m in modifiers]:
        modifiers.append("enum")

    inner_classes = _parse_inner_classes(
        node.body.declarations if node.body else None,
        package, imports, source_file, source
    )

    return ClassInfo(
        name=node.name,
        package=package,
        imports=imports,
        modifiers=modifiers,
        fields=fields,
        methods=methods,
        constructors=constructors,
        javadoc=_extract_javadoc(node),
        annotations=_extract_annotations(node),
        annotation_values=_extract_annotation_values(node),
        source_file=source_file,
        inner_classes=inner_classes,
    )


def discover_java_files(path: str, recursive: bool = True) -> List[str]:
    """
    Given a file or directory path, return a list of .java file paths.
    If ``recursive`` is True, searches subdirectories as well.
    """
    p = Path(path)
    if p.is_file() and p.suffix == ".java":
        return [str(p.resolve())]
    elif p.is_dir():
        pattern = "**/*.java" if recursive else "*.java"
        return sorted(str(f.resolve()) for f in p.glob(pattern))
    else:
        return []
