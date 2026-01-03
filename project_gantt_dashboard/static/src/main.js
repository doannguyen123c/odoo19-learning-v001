/** @odoo-module **/

import { registry } from "@web/core/registry";
import { GanttDashboard } from "./components/gantt_dashboard";

// Register the Client Action
// Tag name MUST match the 'tag' field in views/gantt_menus.xml
registry.category("actions").add("project_gantt_dashboard_tag", GanttDashboard);
