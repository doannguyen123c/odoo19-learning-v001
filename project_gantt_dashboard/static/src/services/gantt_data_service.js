/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
const { DateTime } = luxon;

export class GanttDataService {
    /**
     * Fetch all active projects for the dropdown selector.
     * @returns {Promise<Array>} List of projects [{id, name}]
     */
    async fetchProjects() {
        const domain = []; // Can be extended to filter by user access
        const fields = ['id', 'name'];
        
        try {
            const projects = await rpc("/web/dataset/call_kw/project.project/search_read", {
                model: 'project.project',
                method: 'search_read',
                args: [domain, fields],
                kwargs: {},
            });
            return projects;
        } catch (error) {
            console.error("GanttDataService: Error fetching projects", error);
            return [];
        }
    }

    /**
     * Fetch tasks for a specific project and prepare them for Gantt visualization.
     * @param {number} projectId 
     * @returns {Promise<Array>} List of processed task objects
     */
    async fetchTasks(projectId) {
        const domain = [['project_id', '=', parseInt(projectId)]];
        const fields = ['id', 'name', 'x_date_start', 'date_deadline', 'stage_id', 'user_ids'];
        
        try {
            const tasks = await rpc("/web/dataset/call_kw/project.task/search_read", {
                model: 'project.task',
                method: 'search_read',
                args: [domain, fields],
                kwargs: {},
            });
            
            // Validate response type
            if (!Array.isArray(tasks)) {
                console.warn("GanttDataService: RPC returned non-array", tasks);
                return [];
            }
            
            return this._processTasks(tasks);
        } catch (error) {
            console.error("GanttDataService: Error fetching tasks", error);
            return [];
        }
    }

    /**
     * Update task start and end dates in the backend.
     * @param {number|string} taskId 
     * @param {string} start ISO Date string (YYYY-MM-DD)
     * @param {string} end ISO Date string (YYYY-MM-DD)
     * @returns {Promise<boolean>} True if successful, False otherwise.
     */
    async updateTaskDates(taskId, start, end) {
        try {
            await rpc("/web/dataset/call_kw/project.task/write", {
                model: 'project.task',
                method: 'write',
                args: [[parseInt(taskId)], {
                    'x_date_start': start,
                    'date_deadline': end,
                }],
                kwargs: {},
            });
            return true;
        } catch (error) {
            // Error handling: Logic constraints or Access Rights will be caught here
            console.error("GanttDataService: Error updating task", error);
            return false;
        }
    }

    /**
     * INTERNAL: Process raw Odoo data into Gantt-friendly format.
     * Handles missing dates logic (Soft Visualization).
     */
    _processTasks(tasks) {
        const today = DateTime.now();

        return tasks.map(task => {
            let startObj = task.x_date_start ? DateTime.fromISO(task.x_date_start) : null;
            let endObj = task.date_deadline ? DateTime.fromISO(task.date_deadline) : null;
            let isVirtual = false;

            // Handle invalid/null inputs explicitly
            if (startObj && !startObj.isValid) startObj = null;
            if (endObj && !endObj.isValid) endObj = null;

            // LOGIC: Handle missing dates
            if (!startObj && !endObj) {
                // Case 3: Missing both -> Assume Today + 1 day
                startObj = today;
                endObj = today.plus({ days: 1 });
                isVirtual = true;
            } else if (!startObj && endObj) {
                // Case 1: Missing Start -> Assume End - 1 day
                startObj = endObj.minus({ days: 1 });
                isVirtual = true;
            } else if (startObj && !endObj) {
                // Case 2: Missing End -> Assume Start + 1 day
                endObj = startObj.plus({ days: 1 });
                isVirtual = true;
            }

            // Final safeguard: Ensure we have valid strings
            // If something went wrong, default to today
            const startStr = startObj ? startObj.toISODate() : today.toISODate();
            const endStr = endObj ? endObj.toISODate() : today.plus({ days: 1 }).toISODate();

            return {
                id: task.id,
                name: task.name,
                start: startStr,
                end: endStr,
                progress: 0,
                dependencies: "", 
                custom_class: isVirtual ? 'gantt-task-virtual' : '',
                stage_id: task.stage_id,
                user_names: task.user_ids && task.user_ids.length ? task.user_ids.map(u => u.name).join(", ") : "",
                is_virtual: isVirtual
            };
        });
    }
}

// Singleton instance for easy import
export const ganttService = new GanttDataService();
