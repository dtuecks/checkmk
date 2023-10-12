#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

"""Central module for common (non-edition specific) registrations"""


from functools import partial

from cmk.utils.licensing.registry import register_cre_licensing_handler
from cmk.utils.version import edition, Edition

import cmk.gui.help
from cmk.gui import (
    agent_registration,
    autocompleters,
    crash_reporting,
    cron,
    dashboard,
    default_permissions,
    graphing,
    gui_background_job,
    inventory,
    login,
    logwatch,
    main,
    message,
    mobile,
    node_visualization,
    notifications,
    prediction,
    robotmk,
    sidebar,
    user_message,
    valuespec,
    visuals,
    watolib,
    werks,
)
from cmk.gui.background_job import job_registry
from cmk.gui.background_job import registration as background_job_registration
from cmk.gui.backup.registration import backup_register
from cmk.gui.bi import registration as bi_registration
from cmk.gui.config import register_post_config_load_hook
from cmk.gui.custom_icons.registration import custom_icons_register
from cmk.gui.dashboard import dashlet_registry
from cmk.gui.data_source import data_source_registry
from cmk.gui.main_menu import mega_menu_registry
from cmk.gui.mkeventd import registration as mkeventd_registration
from cmk.gui.pages import page_registry
from cmk.gui.painter.v0.base import painter_registry
from cmk.gui.painter_options import painter_option_registry
from cmk.gui.permissions import permission_registry, permission_section_registry
from cmk.gui.query_filters import cre_sites_options
from cmk.gui.sidebar import snapin_registry
from cmk.gui.userdb import registration as userdb_registration
from cmk.gui.userdb import user_attribute_registry, user_connector_registry
from cmk.gui.valuespec import autocompleter_registry
from cmk.gui.views import registration as views_registration
from cmk.gui.views.command import command_registry
from cmk.gui.views.icon import icon_and_action_registry
from cmk.gui.views.inventory.row_post_processor import inventory_row_post_processor
from cmk.gui.views.join_service_rows import join_service_row_post_processor
from cmk.gui.views.layout import layout_registry
from cmk.gui.views.row_post_processing import register_row_post_processor
from cmk.gui.views.sorter import sorter_registry
from cmk.gui.visuals.filter import filter_registry
from cmk.gui.visuals.info import visual_info_registry
from cmk.gui.visuals.type import visual_type_registry
from cmk.gui.wato import notification_parameter_registry
from cmk.gui.wato import registration as wato_registration
from cmk.gui.watolib.analyze_configuration import ac_test_registry
from cmk.gui.watolib.automation_commands import automation_command_registry
from cmk.gui.watolib.config_domain_name import (
    config_domain_registry,
    config_variable_group_registry,
    config_variable_registry,
    sample_config_generator_registry,
)
from cmk.gui.watolib.groups import contact_group_usage_finder_registry
from cmk.gui.watolib.host_rename import rename_host_hook_registry
from cmk.gui.watolib.main_menu import main_module_registry, main_module_topic_registry
from cmk.gui.watolib.mode import mode_registry
from cmk.gui.watolib.rulespecs import rulespec_group_registry, rulespec_registry
from cmk.gui.watolib.search import match_item_generator_registry


def register_sites_options() -> None:
    visuals.MultipleSitesFilter.sites_options = cre_sites_options
    visuals.SiteFilter.heading_hook = visuals.cre_site_filter_heading_info

    autocompleter_registry.register_expression("sites")(
        partial(autocompleters.sites_autocompleter, sites_options=cre_sites_options)
    )


def register() -> None:
    default_permissions.register(permission_section_registry, permission_registry)
    register_cre_licensing_handler()
    visuals.register(page_registry, visual_info_registry, filter_registry)
    views_registration.register(
        permission_section_registry,
        permission_registry,
        page_registry,
        visual_type_registry,
        register_post_config_load_hook,
    )
    inventory.register(
        page_registry,
        visual_info_registry,
        filter_registry,
        rulespec_group_registry,
        rulespec_registry,
        icon_and_action_registry,
    )
    dashboard.register(
        permission_section_registry,
        page_registry,
        visual_type_registry,
        dashlet_registry,
    )
    crash_reporting.register(
        page_registry,
        data_source_registry,
        painter_registry,
        sorter_registry,
        command_registry,
        config_variable_group_registry,
        config_variable_registry,
    )
    watolib.register(
        rulespec_group_registry,
        automation_command_registry,
        job_registry,
        sample_config_generator_registry,
        contact_group_usage_finder_registry,
    )

    if edition() is not Edition.CSE:  # disabled in CSE
        backup_register(
            page_registry,
            mode_registry,
            main_module_registry,
        )
        mkeventd_registration.register(
            permission_section_registry,
            permission_registry,
            data_source_registry,
            painter_registry,
            command_registry,
            sorter_registry,
            icon_and_action_registry,
            config_domain_registry,
            sample_config_generator_registry,
            mode_registry,
            main_module_registry,
            config_variable_group_registry,
            config_variable_registry,
            rulespec_group_registry,
            rulespec_registry,
            autocompleter_registry,
            filter_registry,
            notification_parameter_registry,
            snapin_registry,
            contact_group_usage_finder_registry,
        )
        custom_icons_register(
            mode_registry,
            main_module_registry,
            permission_registry,
        )
    mobile.register(layout_registry)
    userdb_registration.register(
        page_registry,
        user_attribute_registry,
        user_connector_registry,
        job_registry,
        contact_group_usage_finder_registry,
    )
    wato_registration.register(
        page_registry,
        painter_registry,
        sorter_registry,
        icon_and_action_registry,
        automation_command_registry,
        job_registry,
        filter_registry,
        mode_registry,
        permission_section_registry,
        permission_registry,
        main_module_topic_registry,
        main_module_registry,
        rulespec_group_registry,
        config_domain_registry,
        config_variable_registry,
        config_variable_group_registry,
        snapin_registry,
        match_item_generator_registry,
        mega_menu_registry,
        ac_test_registry,
    )
    bi_registration.register(
        data_source_registry,
        painter_registry,
        painter_option_registry,
        permission_section_registry,
        permission_registry,
        page_registry,
        filter_registry,
        rename_host_hook_registry,
        main_module_topic_registry,
        main_module_registry,
        mode_registry,
        icon_and_action_registry,
        snapin_registry,
    )
    robotmk.register(page_registry)
    cron.register(page_registry)
    node_visualization.register(page_registry, filter_registry)
    notifications.register(page_registry, permission_section_registry)
    user_message.register(page_registry)
    valuespec.register(page_registry)
    autocompleters.register(page_registry)
    werks.register(page_registry)
    login.register(page_registry)
    sidebar.register(page_registry, permission_section_registry, snapin_registry)
    message.register(page_registry)
    cmk.gui.help.register(page_registry)
    main.register(page_registry)
    logwatch.register(page_registry)
    prediction.register(page_registry)
    register_sites_options()
    register_row_post_processor(inventory_row_post_processor)
    register_row_post_processor(join_service_row_post_processor)
    background_job_registration.register(page_registry, mode_registry, main_module_registry)
    gui_background_job.register(permission_section_registry, permission_registry)
    graphing.register(page_registry, config_variable_registry)
    agent_registration.register(permission_section_registry)


register()
