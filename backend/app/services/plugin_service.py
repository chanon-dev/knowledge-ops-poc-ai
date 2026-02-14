"""Plugin architecture for extensible functionality."""

import importlib
import logging
from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


class PluginInterface(ABC):
    """Base interface for all plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    async def execute(self, input_data: dict) -> dict:
        pass

    def validate_input(self, input_data: dict) -> bool:
        return True


class LogParserPlugin(PluginInterface):
    """Parse common log formats: Apache, Nginx, syslog."""

    name = "log-parser"
    version = "1.0.0"
    description = "Parse and analyze common log formats (Apache, Nginx, syslog)"

    async def execute(self, input_data: dict) -> dict:
        log_text = input_data.get("log_text", "")
        log_format = input_data.get("format", "auto")

        if log_format == "auto":
            log_format = self._detect_format(log_text)

        lines = log_text.strip().split("\n")
        parsed = []
        errors = []
        warnings = []

        for line in lines:
            entry = {"raw": line, "format": log_format}
            lower = line.lower()
            if "error" in lower or "fatal" in lower or "crit" in lower:
                errors.append(line)
                entry["level"] = "error"
            elif "warn" in lower:
                warnings.append(line)
                entry["level"] = "warning"
            else:
                entry["level"] = "info"
            parsed.append(entry)

        return {
            "format_detected": log_format,
            "total_lines": len(lines),
            "errors": len(errors),
            "warnings": len(warnings),
            "error_lines": errors[:20],
            "warning_lines": warnings[:20],
            "summary": f"Parsed {len(lines)} lines: {len(errors)} errors, {len(warnings)} warnings",
        }

    def _detect_format(self, text: str) -> str:
        if "HTTP/" in text and ('" 2' in text or '" 3' in text or '" 4' in text or '" 5' in text):
            return "apache" if "Apache" in text else "nginx"
        if text.startswith("<") and ">" in text[:20]:
            return "syslog"
        return "generic"


class ConfigValidatorPlugin(PluginInterface):
    """Validate YAML/JSON configs against expected patterns."""

    name = "config-validator"
    version = "1.0.0"
    description = "Validate YAML/JSON configuration files"

    async def execute(self, input_data: dict) -> dict:
        config_text = input_data.get("config_text", "")
        config_format = input_data.get("format", "auto")

        issues = []
        parsed = None

        # Try JSON
        if config_format in ("auto", "json"):
            try:
                import json
                parsed = json.loads(config_text)
                config_format = "json"
            except json.JSONDecodeError as e:
                if config_format == "json":
                    issues.append({"severity": "error", "message": f"Invalid JSON: {e}"})

        # Try YAML
        if parsed is None and config_format in ("auto", "yaml"):
            try:
                import yaml
                parsed = yaml.safe_load(config_text)
                config_format = "yaml"
            except yaml.YAMLError as e:
                if config_format == "yaml":
                    issues.append({"severity": "error", "message": f"Invalid YAML: {e}"})

        if parsed is None:
            return {"valid": False, "format": config_format, "issues": issues or [{"severity": "error", "message": "Could not parse config"}]}

        # Check common issues
        if isinstance(parsed, dict):
            self._check_dict(parsed, "", issues)

        return {
            "valid": len([i for i in issues if i["severity"] == "error"]) == 0,
            "format": config_format,
            "issues": issues,
            "keys_found": list(parsed.keys()) if isinstance(parsed, dict) else [],
        }

    def _check_dict(self, d: dict, path: str, issues: list):
        for key, value in d.items():
            full_path = f"{path}.{key}" if path else key
            if value is None:
                issues.append({"severity": "warning", "message": f"Null value at '{full_path}'"})
            if isinstance(key, str) and key.lower() in ("password", "secret", "api_key", "token"):
                if isinstance(value, str) and not value.startswith("${"):
                    issues.append({"severity": "error", "message": f"Hardcoded secret at '{full_path}'"})
            if isinstance(value, dict):
                self._check_dict(value, full_path, issues)


class IncidentReportPlugin(PluginInterface):
    """Auto-generate incident summary reports."""

    name = "incident-report"
    version = "1.0.0"
    description = "Generate structured incident reports from query/resolution data"

    async def execute(self, input_data: dict) -> dict:
        from datetime import datetime

        title = input_data.get("title", "Untitled Incident")
        description = input_data.get("description", "")
        resolution = input_data.get("resolution", "")
        severity = input_data.get("severity", "medium")
        affected_systems = input_data.get("affected_systems", [])

        report = f"""# Incident Report

## Summary
- **Title**: {title}
- **Severity**: {severity.upper()}
- **Date**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
- **Affected Systems**: {', '.join(affected_systems) if affected_systems else 'N/A'}

## Description
{description}

## Root Cause Analysis
{resolution if resolution else 'Pending investigation'}

## Impact
- Systems affected: {len(affected_systems)}
- Severity level: {severity}

## Resolution Steps
{resolution if resolution else 'Resolution pending'}

## Prevention
- [ ] Review monitoring alerts
- [ ] Update runbooks
- [ ] Schedule post-mortem
"""
        return {
            "report": report,
            "severity": severity,
            "title": title,
            "format": "markdown",
        }


# Plugin registry
BUILT_IN_PLUGINS: dict[str, type[PluginInterface]] = {
    "log-parser": LogParserPlugin,
    "config-validator": ConfigValidatorPlugin,
    "incident-report": IncidentReportPlugin,
}


class PluginManager:
    """Manage plugin discovery, registration, and execution."""

    def __init__(self):
        self._plugins: dict[str, PluginInterface] = {}
        # Register built-in plugins
        for name, cls in BUILT_IN_PLUGINS.items():
            self._plugins[name] = cls()

    def list_plugins(self) -> list[dict]:
        return [
            {"name": p.name, "version": p.version, "description": p.description}
            for p in self._plugins.values()
        ]

    def get_plugin(self, name: str) -> PluginInterface | None:
        return self._plugins.get(name)

    async def execute_plugin(self, name: str, input_data: dict) -> dict:
        plugin = self.get_plugin(name)
        if not plugin:
            return {"error": f"Plugin '{name}' not found"}
        if not plugin.validate_input(input_data):
            return {"error": "Invalid input data"}
        return await plugin.execute(input_data)

    def register_plugin(self, plugin: PluginInterface):
        self._plugins[plugin.name] = plugin
        logger.info(f"Plugin registered: {plugin.name} v{plugin.version}")
