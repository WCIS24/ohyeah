"""Config schema and validation."""

from .schema import (
    DEFAULT_CONFIG,
    get_path,
    load_and_resolve,
    resolve_and_validate,
    resolve_config,
    set_path,
    validate_config,
    validate_paths,
    write_resolved_config,
)
