#!/usr/bin/env python3
# Copyright (C) 2024 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from collections.abc import Mapping
from dataclasses import dataclass

from cmk.agent_based.v2 import (
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Result,
    Service,
    SimpleSNMPSection,
    SNMPTree,
    StringTable,
)
from cmk.plugins.lib.cisco_ucs import DETECT, Operability


@dataclass(frozen=True, kw_only=True)
class PSUModule:
    id: str
    operability: Operability
    serial: str
    model: str


def parse_cisco_ucs_psu(string_table: StringTable) -> dict[str, PSUModule]:
    return {
        " ".join(name.split("/")[2:]): PSUModule(
            id=name, operability=Operability(operability), serial=serial, model=model
        )
        for name, operability, serial, model in string_table
    }


snmp_section_cisco_ucs_psu = SimpleSNMPSection(
    name="cisco_ucs_psu",
    parse_function=parse_cisco_ucs_psu,
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.9.9.719.1.15.56.1",
        oids=[
            "2",  # 1.3.6.1.4.1.9.9.719.1.15.56.1.2	cucsEquipmentPsuDn
            "8",  # 1.3.6.1.4.1.9.9.719.1.15.56.1.8	cucsEquipmentPsuOperability
            "13",  # 1.3.6.1.4.1.9.9.719.1.15.56.1.13	cucsEquipmentPsuSerial
            "6",  # 1.3.6.1.4.1.9.9.719.1.15.56.1.6	cucsEquipmentPsuModel
        ],
    ),
    detect=DETECT,
)


def discover_cisco_ucs_psu(
    section: Mapping[str, PSUModule] | None,
) -> DiscoveryResult:
    if not section:
        return
    yield from (Service(item=name) for name in section)


def check_cisco_ucs_psu(
    item: str,
    section: Mapping[str, PSUModule] | None,
) -> CheckResult:
    if not (psu_module := (section or {}).get(item)):
        return

    yield Result(
        state=psu_module.operability.monitoring_state(),
        summary=f"Status: {psu_module.operability.name}, Model: {psu_module.model}, SN: {psu_module.serial}",
    )


check_plugin_cisco_ucs_psu = CheckPlugin(
    name="cisco_ucs_psu",
    service_name="psu %s",
    discovery_function=discover_cisco_ucs_psu,
    check_function=check_cisco_ucs_psu,
)
