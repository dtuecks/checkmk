#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.


from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from cmk.utils.rulesets import RuleSetName
from cmk.utils.rulesets.ruleset_matcher import RuleSpec
from cmk.utils.sectionname import SectionName

from cmk.checkengine.checking import CheckPluginName
from cmk.checkengine.inventory import InventoryPluginName
from cmk.checkengine.sectionparser import ParsedSectionName

from cmk.base.api.agent_based.plugin_classes import (
    AgentSectionPlugin,
    CheckPlugin,
    InventoryPlugin,
    SectionPlugin,
    SNMPSectionPlugin,
)
from cmk.base.api.agent_based.register.check_plugins import management_plugin_factory
from cmk.base.api.agent_based.register.utils import validate_check_ruleset_item_consistency

registered_agent_sections: dict[SectionName, AgentSectionPlugin] = {}
registered_snmp_sections: dict[SectionName, SNMPSectionPlugin] = {}
registered_check_plugins: dict[CheckPluginName, CheckPlugin] = {}
registered_inventory_plugins: dict[InventoryPluginName, InventoryPlugin] = {}

# N O T E: This currently contains discovery *and* host_label rulesets.
# The rules are deliberately put the same dictionary, as we allow for
# the host_label_function and the discovery_function to share a ruleset.
# We provide separate API functions however, should the need arise to
# separate them.
stored_rulesets: dict[RuleSetName, Sequence[RuleSpec]] = {}

# Lookup table for optimizing validate_check_ruleset_item_consistency()
_check_plugins_by_ruleset_name: dict[RuleSetName | None, list[CheckPlugin]] = defaultdict(list)

_sections_by_parsed_name: dict[ParsedSectionName, dict[SectionName, SectionPlugin]] = defaultdict(
    dict
)


@dataclass(frozen=True)
class AgentBasedPlugins:
    agent_sections: Mapping[SectionName, AgentSectionPlugin]
    snmp_sections: Mapping[SectionName, SNMPSectionPlugin]
    check_plugins: Mapping[CheckPluginName, CheckPlugin]
    inventory_plugins: Mapping[InventoryPluginName, InventoryPlugin]


def get_previously_loaded_plugins() -> AgentBasedPlugins:
    """Return the previously loaded agent-based plugins

    In the long run we want to get rid of this function and instead
    return the plugins directly after loading them (without registry).
    """
    return AgentBasedPlugins(
        agent_sections=registered_agent_sections,
        snmp_sections=registered_snmp_sections,
        check_plugins=registered_check_plugins,
        inventory_plugins=registered_inventory_plugins,
    )


def add_check_plugin(check_plugin: CheckPlugin) -> None:
    validate_check_ruleset_item_consistency(check_plugin, _check_plugins_by_ruleset_name)
    registered_check_plugins[check_plugin.name] = check_plugin
    _check_plugins_by_ruleset_name[check_plugin.check_ruleset_name].append(check_plugin)


def add_discovery_ruleset(ruleset_name: RuleSetName) -> None:
    stored_rulesets.setdefault(ruleset_name, [])


def add_host_label_ruleset(ruleset_name: RuleSetName) -> None:
    stored_rulesets.setdefault(ruleset_name, [])


def add_inventory_plugin(inventory_plugin: InventoryPlugin) -> None:
    registered_inventory_plugins[inventory_plugin.name] = inventory_plugin


def add_section_plugin(section_plugin: SectionPlugin) -> None:
    _sections_by_parsed_name[section_plugin.parsed_section_name][section_plugin.name] = (
        section_plugin
    )
    if isinstance(section_plugin, AgentSectionPlugin):
        registered_agent_sections[section_plugin.name] = section_plugin
    else:
        registered_snmp_sections[section_plugin.name] = section_plugin


def get_check_plugin(plugin_name: CheckPluginName) -> CheckPlugin | None:
    """Returns the registered check plug-in

    Management plugins may be created on the fly.
    """
    plugin = registered_check_plugins.get(plugin_name)
    if plugin is not None or not plugin_name.is_management_name():
        return plugin

    return (
        None
        if (non_mgmt_plugin := registered_check_plugins.get(plugin_name.create_basic_name()))
        is None
        # create management board plug-in on the fly:
        else management_plugin_factory(non_mgmt_plugin)
    )


def get_discovery_ruleset(ruleset_name: RuleSetName) -> Sequence[RuleSpec]:
    """Returns all rulesets of a given name"""
    return stored_rulesets.get(ruleset_name, [])


def get_host_label_ruleset(ruleset_name: RuleSetName) -> Sequence[RuleSpec]:
    """Returns all rulesets of a given name"""
    return stored_rulesets.get(ruleset_name, [])


def get_inventory_plugin(plugin_name: InventoryPluginName) -> InventoryPlugin | None:
    """Returns the registered inventory plug-in"""
    return registered_inventory_plugins.get(plugin_name)


def get_relevant_raw_sections(
    *,
    check_plugin_names: Iterable[CheckPluginName],
    inventory_plugin_names: Iterable[InventoryPluginName],
) -> dict[SectionName, SectionPlugin]:
    """return the raw sections potentially relevant for the given check or inventory plugins"""
    parsed_section_names: set[ParsedSectionName] = set()

    for check_plugin_name in check_plugin_names:
        if check_plugin := get_check_plugin(check_plugin_name):
            parsed_section_names.update(check_plugin.sections)

    for inventory_plugin_name in inventory_plugin_names:
        if inventory_plugin := get_inventory_plugin(inventory_plugin_name):
            parsed_section_names.update(inventory_plugin.sections)

    return {
        section_name: section
        for parsed_name in parsed_section_names
        for section_name, section in _sections_by_parsed_name[parsed_name].items()
    }


def get_section_plugin(section_name: SectionName) -> SectionPlugin | None:
    return registered_agent_sections.get(section_name) or registered_snmp_sections.get(section_name)


def get_section_producers(parsed_section_name: ParsedSectionName) -> set[SectionName]:
    return set(_sections_by_parsed_name[parsed_section_name])


def is_registered_check_plugin(check_plugin_name: CheckPluginName) -> bool:
    return check_plugin_name in registered_check_plugins


def is_registered_inventory_plugin(inventory_plugin_name: InventoryPluginName) -> bool:
    return inventory_plugin_name in registered_inventory_plugins


def is_registered_section_plugin(section_name: SectionName) -> bool:
    return section_name in registered_snmp_sections or section_name in registered_agent_sections


def is_stored_ruleset(ruleset_name: RuleSetName) -> bool:
    return ruleset_name in stored_rulesets


def needs_redetection(section_name: SectionName) -> bool:
    section = get_section_plugin(section_name)
    ps_name = (
        ParsedSectionName(str(section_name)) if section is None else section.parsed_section_name
    )
    return len(get_section_producers(ps_name)) > 1


def iter_all_discovery_rulesets() -> Iterable[RuleSetName]:
    return stored_rulesets.keys()


def iter_all_host_label_rulesets() -> Iterable[RuleSetName]:
    return stored_rulesets.keys()


def set_discovery_ruleset(
    ruleset_name: RuleSetName,
    rules: Sequence[RuleSpec],
) -> None:
    """Set a ruleset to a given value"""
    stored_rulesets[ruleset_name] = rules


def set_host_label_ruleset(ruleset_name: RuleSetName, rules: Sequence[RuleSpec]) -> None:
    """Set a ruleset to a given value"""
    stored_rulesets[ruleset_name] = rules
