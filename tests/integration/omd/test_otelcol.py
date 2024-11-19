#!/usr/bin/env python3
# Copyright (C) 2024 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from pathlib import Path

import pytest

from tests.testlib.site import Site
from tests.testlib.version import version_from_env

# Apply the skipif marker to all tests in this file for non Managed or Cloud edition
pytestmark = [
    pytest.mark.skipif(
        True
        not in [version_from_env().is_cloud_edition(), version_from_env().is_managed_edition()],
        reason="otel-collector only shipped with Cloud or Managed",
    )
]


def test_otelcol_exists(site: Site) -> None:
    assert Path(site.root, "bin", "otelcol").exists()


def test_otelcol_help(site: Site) -> None:
    # Commands executed here should return with exit code 0
    site.check_output(["otelcol", "--help"])