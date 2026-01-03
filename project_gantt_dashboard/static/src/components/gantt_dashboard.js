/** @odoo-module **/

import { Component, onMounted, useState, useRef, onWillUnmount } from "@odoo/owl";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { useService } from "@web/core/utils/hooks";
import { ganttService } from "../services/gantt_data_service";
const { DateTime } = luxon;
// Frappe Gantt is loaded globally via assets_backend, so we access it via window or directly if exposed.
// Since we manually included the file, it assigns to 'Gantt' variable.

export class GanttDashboard extends Component {
    static template = "project_gantt_dashboard.GanttDashboard";
    static props = { ...standardActionServiceProps };

    setup() {
        this.actionService = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            projectId: null,
            projects: [],
            loading: false,
            viewMode: 'Week', // Default view mode
        });
        
        this.ganttContainer = useRef("gantt-container");
        this.ganttInstance = null;
        this.isUpdating = false; // Flag to prevent rapid-fire updates

        onMounted(async () => {
            await this.loadProjects();
        });

        onWillUnmount(() => {
            // Cleanup if necessary
            this.ganttInstance = null;
        });
    }

    async loadProjects() {
        this.state.loading = true;
        const projects = await ganttService.fetchProjects();
        this.state.projects = projects;
        
        if (projects.length > 0) {
            this.state.projectId = projects[0].id;
            await this.refreshGantt();
        }
        this.state.loading = false;
    }

    async onProjectChange(ev) {
        this.state.projectId = ev.target.value;
        await this.refreshGantt();
    }

    async onViewModeChange(mode) {
        this.state.viewMode = mode;
        if (this.ganttInstance) {
            this.ganttInstance.change_view_mode(mode);
        }
    }

    async refreshGantt() {
        if (!this.state.projectId) return;

        this.state.loading = true;
        const tasks = await ganttService.fetchTasks(this.state.projectId);
        this.state.loading = false;

        this.renderGantt(tasks);
    }

    async openTaskForm(taskId) {
        try {
            await this.actionService.doAction({
                type: 'ir.actions.act_window',
                res_model: 'project.task',
                res_id: parseInt(taskId),
                views: [[false, 'form']],
                target: 'new', // Open in Dialog/Popup
            }, {
                onClose: async () => {
                    // Reload Gantt data when popup closes to reflect changes
                    await this.refreshGantt();
                }
            });
        } catch (error) {
            this.notification.add("Unable to open task. You might not have access.", {
                type: "danger",
            });
        }
    }

    renderGantt(tasks) {
        const container = this.ganttContainer.el;
        if (!container) return;

        // Safeguard: Ensure tasks is always an array
        if (!Array.isArray(tasks)) {
            console.error("renderGantt received non-array tasks:", tasks);
            tasks = [];
        }

        // Clear previous content to avoid ghosting
        container.innerHTML = "";

        if (tasks.length === 0) {
            container.innerHTML = `<div class="text-center text-muted mt-5"><h4>No tasks found for this project.</h4></div>`;
            return;
        }

        try {
            // Initialize Frappe Gantt
            this.ganttInstance = new Gantt(container, tasks, {
                header_height: 50,
                column_width: 30,
                step: 24,
                view_modes: ['Quarter Day', 'Half Day', 'Day', 'Week', 'Month'],
                bar_height: 25,
                bar_corner_radius: 3,
                arrow_curve: 5,
                padding: 18,
                view_mode: this.state.viewMode,
                date_format: 'YYYY-MM-DD',
                popup_trigger: 'click',
                language: 'en',
                
                // Event Handlers
                on_click: (task) => {
                    this.openTaskForm(task.id);
                },
                
                on_date_change: async (task, start, end) => {
                    if (this.isUpdating) return;
                    this.isUpdating = true;

                    // Normalize dates to YYYY-MM-DD for Odoo backend
                    const startDate = DateTime.fromJSDate(start).toISODate();
                    const endDate = DateTime.fromJSDate(end).toISODate();

                    const success = await ganttService.updateTaskDates(task.id, startDate, endDate);

                    if (success) {
                        this.notification.add("Task updated successfully", { type: "success" });
                        // Optimistic UI: Do not refresh, keep the bar where user dropped it
                    } else {
                        this.notification.add("Update failed! Check permissions or date constraints.", { 
                            type: "danger", 
                            sticky: true 
                        });
                        // Revert: Refresh to snap bar back to original position
                        await this.refreshGantt();
                    }
                    
                    this.isUpdating = false;
                },
                
                on_progress_change: (task, progress) => {
                    // Placeholder for progress update
                },
                on_view_change: (mode) => {
                    // View mode changed
                }
            });
        } catch (error) {
            console.error("Gantt Render Error:", error);
            container.innerHTML = `<div class="alert alert-danger">Error rendering chart: ${error.message}</div>`;
        }
    }
}
