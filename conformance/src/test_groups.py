"""
Reads a template file that describes groups of tests in the
conformance test suite.
"""

from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Mapping, Sequence

import tomli


@dataclass
class TestGroup:
    name: str
    href: str


def get_test_groups(root_dir: Path) -> Mapping[str, TestGroup]:
    # Read the TOML file that defines the test groups. Each test
    # group has a name that associated test cases must start with.
    test_group_file = root_dir / "src" / "test_groups.toml"
    with open(test_group_file, "rb") as f:
        test_groups = tomli.load(f)

    return {
        k: TestGroup(v.get("name", "unknown"), v.get("href", ""))
        for k, v in test_groups.items()
    }


def get_test_cases(
    test_groups: Mapping[str, TestGroup], tests_dir: Path
) -> Sequence[Path]:
    test_group_names = test_groups.keys()

    # Filter test cases based on test group names. Files that do
    # not begin with a known test group name are assumed to be
    # files that support one or more tests.
    test_cases = [
        p
        for p in chain(tests_dir.glob("*.py"), tests_dir.glob("*.pyi"))
        if p.name.split("_")[0] in test_group_names
    ]

    return test_cases
