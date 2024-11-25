#!/usr/bin/env python3
# Copyright (C) 2024 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import re
import sys
from collections.abc import Sequence
from itertools import chain
from pathlib import Path

HEADER = [
    re.compile(r"Copyright \(C\) 20\d{2} Checkmk GmbH - License: GNU General Public License v2$"),
    re.compile(
        r"This file is part of Checkmk \(https://checkmk.com\)\. It is subject to the terms and$"
    ),
    re.compile(
        r"conditions defined in the file COPYING, which is part of this source code package\.$"
    ),
]

HEADER_CEE = [
    re.compile(r"Copyright \(C\) 20\d{2} Checkmk GmbH - License: Checkmk Enterprise License$"),
    re.compile(
        r"This file is part of Checkmk \(https://checkmk.com\)\. It is subject to the terms and$"
    ),
    re.compile(
        r"conditions defined in the file COPYING, which is part of this source code package\.$"
    ),
]

FILES_IGNORED = set(
    [
        Path(".editorconfig"),
        Path("eslint.config.js"),
        Path(".f12"),
        Path(".gitignore"),
        Path(".prettierignore"),
        Path(".prettierrc.json"),
        Path(".npmrc"),
        Path("README.md"),
        Path("index.html"),
        Path("src/components/_demo/index.html"),
        Path("env.d.ts"),
        Path("src/components/_demo/public/mockServiceWorker.js"),  # auto generated
    ]
)

ROOT_FOLDERS_IGNORED = set(
    [
        "node_modules",
        "dist",
        "dist-dev",
    ]
)

SUFFIX_IGNORED = set([".swp", ".pyc", ".svg"])

GLOB_IGNORED = [
    "*.log",  # added by ci
    "*.cid",  # added by ci
    "*.json",  # can not add comments to json, so no header possible
]

PATH_TO_SUFFIX = {
    Path("run"): ".sh",
}


class Checker:
    def __init__(
        self,
        *,
        omit_start_lines: int = 0,
        remove_prefix: str = "",
        previous_lines: None | list[str] = None,
        next_lines: None | list[str] = None,
    ) -> None:
        self.omit_start_lines = omit_start_lines
        self.remove_prefix = remove_prefix
        self.previous_lines = previous_lines or []
        self.next_lines = next_lines or []

    def _read(self, path: Path) -> list[str]:
        try:
            with path.open() as fo:
                for _ in range(self.omit_start_lines):
                    next(fo)
                return [
                    next(fo).removesuffix("\n").removeprefix(self.remove_prefix)
                    for _ in range(3 + len(self.previous_lines) + len(self.next_lines))
                ]
        except StopIteration:
            return []

    def check(self, path: Path, header: Sequence[re.Pattern]) -> bool:
        result = []
        lines = self._read(path)
        if not lines:
            return False
        for line in self.previous_lines:
            result.append(lines.pop(0) == line)
        for line in self.next_lines:
            result.append(lines.pop(len(header)) == line)
        return all(chain(result, (regex.match(line) for regex, line in zip(header, lines))))


CHECKER = {
    ".py": Checker(previous_lines=["#!/usr/bin/env python3"], remove_prefix="# "),
    ".ts": Checker(previous_lines=["/**"], remove_prefix=" * ", next_lines=[" */"]),
    ".js": Checker(previous_lines=["/**"], remove_prefix=" * ", next_lines=[" */"]),
    ".sh": Checker(omit_start_lines=1, remove_prefix="# "),
    ".vue": Checker(previous_lines=["<!--"], next_lines=["-->"]),
    ".css": Checker(previous_lines=["/**"], remove_prefix=" * ", next_lines=[" */"]),
}


def check(suffix: str, path: Path) -> bool:
    try:
        return CHECKER[suffix].check(
            path,
            HEADER_CEE if path.is_relative_to(Path("src/graph-designer")) else HEADER,
        )
    except Exception as e:
        raise RuntimeError(f"Could not find Checker for {path}") from e


def main() -> int:
    sys.stdout.write("Checking license headers...\n")
    problems = []
    for root, _dirs, files in Path(".").walk():
        if root.parts and root.parts[0] in ROOT_FOLDERS_IGNORED:
            continue
        for file in files:
            path = root / file

            if path.suffix in SUFFIX_IGNORED:
                continue

            if any(path.match(glob) for glob in GLOB_IGNORED):
                continue

            if path in FILES_IGNORED:
                continue

            if not (suffix := path.suffix):
                suffix = PATH_TO_SUFFIX[path]

            if not check(suffix, path):
                problems.append(path)

    if problems:
        sys.stdout.write("Please check the license header for the following files:\n")
        sys.stdout.write("\n".join(str(p) for p in problems) + "\n")
        return 1
    sys.stdout.write("Done!\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
