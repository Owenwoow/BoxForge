"""Entry point: read config.yaml -> build box -> export STL."""
from __future__ import annotations

import argparse
import sys

from box_builder.body import build_body
from box_builder.export import export_stl
from box_builder.hollow import apply_hollow
from box_builder.partitions import build_partitions
from box_builder.validate import ConfigError, load_config


def build_from_config(cfg: dict):
    """cfg must already be a validated config (see validate.validate_config)."""
    solid = build_body(cfg["box"])

    partitions_solid, wall_specs = build_partitions(cfg["partitions"], cfg["box"])
    if partitions_solid is not None:
        solid = solid.union(partitions_solid)

    solid = apply_hollow(solid, cfg["box"], wall_specs, cfg["hollow"])
    return solid


def build(config_path: str):
    cfg = load_config(config_path)
    solid = build_from_config(cfg)
    return solid, cfg


def main():
    parser = argparse.ArgumentParser(description="Parametric storage box generator")
    parser.add_argument("config", nargs="?", default="config.yaml", help="Path to YAML config")
    args = parser.parse_args()

    try:
        solid, cfg = build(args.config)
    except ConfigError as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)

    filename = export_stl(solid, cfg["export"])
    print(f"Exported {filename}")


if __name__ == "__main__":
    main()
