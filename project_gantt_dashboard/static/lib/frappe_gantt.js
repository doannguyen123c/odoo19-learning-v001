/**
 * Frappe Gantt v0.6.1
 * (c) 2023 Frappe Technologies Pvt. Ltd.
 * License: MIT
 */

var Gantt = (function () {
    'use strict';

    const YEAR = 'Year';
    const MONTH = 'Month';
    const WEEK = 'Week';
    const DAY = 'Day';
    const HALF_DAY = 'Half Day';
    const QUARTER_DAY = 'Quarter Day';
    const HOUR = 'Hour';

    const VIEW_MODE = {
        QUARTER_DAY,
        HALF_DAY,
        DAY,
        WEEK,
        MONTH,
        YEAR,
    };

    class Gantt {
        constructor(wrapper, tasks, options) {
            this.setup_wrapper(wrapper);
            this.setup_options(options);
            this.setup_tasks(tasks);
            // initialize with default view mode
            this.change_view_mode();
            this.bind_events();
        }

        setup_wrapper(element) {
            let container_class = 'gantt-container';

            if (typeof element === 'string') {
                element = document.querySelector(element);
            }

            // Create svg element
            if (element instanceof HTMLElement) {
                this.wrapper = element;
                this.wrapper.innerHTML = '';
            } else {
                throw new Error('Invalid argument passed to Gantt constructor');
            }

            // Create SVG
            this.svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            this.svg.classList.add('gantt');
            this.wrapper.appendChild(this.svg);

            this.container = document.createElement('div');
            this.container.classList.add(container_class);
            this.wrapper.appendChild(this.container);
            this.container.appendChild(this.svg);

            this.popup_wrapper = document.createElement('div');
            this.popup_wrapper.classList.add('popup-wrapper');
            this.container.appendChild(this.popup_wrapper);
        }

        setup_options(options) {
            const default_options = {
                header_height: 50,
                column_width: 30,
                step: 24,
                view_modes: [...Object.values(VIEW_MODE)],
                bar_height: 20,
                bar_corner_radius: 3,
                arrow_curve: 5,
                padding: 18,
                view_mode: 'Day',
                date_format: 'YYYY-MM-DD',
                popup_trigger: 'click',
                custom_popup_html: null,
                language: 'en',
            };
            this.options = Object.assign({}, default_options, options);
        }

        setup_tasks(tasks) {
            // prepare tasks
            this.tasks = tasks.map((task, i) => {
                // convert to Date objects
                task._start = date_utils.parse(task.start);
                task._end = date_utils.parse(task.end);

                // make task invalid if duration too large
                if (date_utils.diff(task._end, task._start, 'year') > 10) {
                    task.end = null;
                }

                // cache index
                task._index = i;

                // invalid dates
                if (!task.start && !task.end) {
                    const today = date_utils.today();
                    task._start = today;
                    task._end = date_utils.add(today, 2, 'day');
                }

                if (!task.start && task.end) {
                    task._start = date_utils.add(date_utils.parse(task.end), -2, 'day');
                }

                if (task.start && !task.end) {
                    task._end = date_utils.add(date_utils.parse(task.start), 2, 'day');
                }

                // if dates are not valid, set to today
                const date_diff = date_utils.diff(task._end, task._start, 'year');
                if (date_diff < 0) {
                    task._end = date_utils.add(task._start, 2, 'day');
                }

                return task;
            });

            this.setup_dependencies();
        }

        setup_dependencies() {
            this.dependency_map = {};
            for (let t of this.tasks) {
                if (t.dependencies) {
                    t.dependencies.split(',').forEach((d) => {
                        const dep = d.trim();
                        if (!this.dependency_map[dep]) {
                            this.dependency_map[dep] = [];
                        }
                        this.dependency_map[dep].push(t.id);
                    });
                }
            }
        }

        refresh(tasks) {
            this.setup_tasks(tasks);
            this.change_view_mode();
        }

        change_view_mode(mode = this.options.view_mode) {
            this.update_view_scale(mode);
            this.setup_dates();
            this.render();
            // fire viewmode_change event
            this.trigger_event('view_change', [mode]);
        }

        update_view_scale(view_mode) {
            this.options.view_mode = view_mode;

            if (view_mode === DAY) {
                this.options.step = 24;
                this.options.column_width = 38;
            } else if (view_mode === HALF_DAY) {
                this.options.step = 24 / 2;
                this.options.column_width = 38;
            } else if (view_mode === QUARTER_DAY) {
                this.options.step = 24 / 4;
                this.options.column_width = 38;
            } else if (view_mode === WEEK) {
                this.options.step = 24 * 7;
                this.options.column_width = 140;
            } else if (view_mode === MONTH) {
                this.options.step = 24 * 30;
                this.options.column_width = 120;
            } else if (view_mode === YEAR) {
                this.options.step = 24 * 365;
                this.options.column_width = 120;
            }
        }

        setup_dates() {
            this.setup_gantt_dates();
            this.setup_date_values();
        }

        setup_gantt_dates() {
            this.gantt_start = this.gantt_end = null;

            for (let task of this.tasks) {
                // set global start and end date
                if (!this.gantt_start || task._start < this.gantt_start) {
                    this.gantt_start = task._start;
                }
                if (!this.gantt_end || task._end > this.gantt_end) {
                    this.gantt_end = task._end;
                }
            }

            this.gantt_start = date_utils.start_of(this.gantt_start, 'year');
            this.gantt_end = date_utils.add(this.gantt_end, 1, 'year'); // Add buffer
            
            // Handle empty tasks case
            if(!this.gantt_start) this.gantt_start = new Date();
            if(!this.gantt_end) this.gantt_end = date_utils.add(new Date(), 1, 'month');
        }

        setup_date_values() {
            this.dates = [];
            let cur_date = null;

            while (cur_date === null || cur_date < this.gantt_end) {
                if (!cur_date) {
                    cur_date = date_utils.clone(this.gantt_start);
                } else {
                    if (this.view_is(YEAR)) {
                        cur_date = date_utils.add(cur_date, 1, 'year');
                    } else if (this.view_is(MONTH)) {
                        cur_date = date_utils.add(cur_date, 1, 'month');
                    } else {
                        cur_date = date_utils.add(
                            cur_date,
                            this.options.step,
                            'hour'
                        );
                    }
                }
                this.dates.push(cur_date);
            }
        }

        bind_events() {
            this.bind_grid_click();
            this.bind_bar_events();
        }

        render() {
            this.clear();
            this.setup_layers();
            this.make_grid();
            this.make_dates();
            this.make_bars();
            this.make_arrows();
            this.map_arrows_on_bars();
            this.set_width();
            this.set_scroll_position();
        }

        setup_layers() {
            this.layers = {};
            const layers = ['grid', 'date', 'arrow', 'progress', 'bar', 'details'];
            // make group layers
            for (let layer of layers) {
                this.layers[layer] = createSVG('g', {
                    class: layer,
                    append_to: this.svg,
                });
            }
        }

        make_grid() {
            this.make_grid_background();
            this.make_grid_rows();
            this.make_grid_header();
            this.make_grid_ticks();
            this.make_grid_highlights();
        }

        make_grid_background() {
            const grid_width = this.dates.length * this.options.column_width;
            const grid_height =
                this.options.header_height +
                this.options.padding +
                (this.options.bar_height + this.options.padding) *
                    this.tasks.length;

            createSVG('rect', {
                x: 0,
                y: 0,
                width: grid_width,
                height: grid_height,
                class: 'grid-background',
                append_to: this.layers.grid,
            });

            $.attr(this.svg, {
                height: grid_height + this.options.padding + 100,
                width: '100%',
            });
        }

        make_grid_rows() {
            const rows_layer = createSVG('g', { append_to: this.layers.grid });
            const lines_layer = createSVG('g', { append_to: this.layers.grid });

            const row_width = this.dates.length * this.options.column_width;
            const row_height = this.options.bar_height + this.options.padding;

            let row_y = this.options.header_height + this.options.padding / 2;

            for (let task of this.tasks) {
                createSVG('rect', {
                    x: 0,
                    y: row_y,
                    width: row_width,
                    height: row_height,
                    class: 'grid-row',
                    append_to: rows_layer,
                });

                createSVG('line', {
                    x1: 0,
                    y1: row_y + row_height,
                    x2: row_width,
                    y2: row_y + row_height,
                    class: 'row-line',
                    append_to: lines_layer,
                });

                row_y += this.options.bar_height + this.options.padding;
            }
        }

        make_grid_header() {
            const header_width = this.dates.length * this.options.column_width;
            const header_height = this.options.header_height + 10;
            createSVG('rect', {
                x: 0,
                y: 0,
                width: header_width,
                height: header_height,
                class: 'grid-header',
                append_to: this.layers.grid,
            });
        }

        make_grid_ticks() {
            let tick_x = 0;
            let tick_y = this.options.header_height + this.options.padding / 2;
            let tick_height =
                (this.options.bar_height + this.options.padding) *
                this.tasks.length;

            for (let date of this.dates) {
                let tick_class = 'tick';
                if (this.view_is(DAY) && date.getDate() === 1) {
                    tick_class += ' thick';
                }
                if (this.view_is(WEEK) && date.getDate() >= 1 && date.getDate() < 8) {
                    tick_class += ' thick';
                }
                if (this.view_is(MONTH) && date.getMonth() % 3 === 0) {
                    tick_class += ' thick';
                }

                createSVG('path', {
                    d: `M ${tick_x} ${tick_y} v ${tick_height}`,
                    class: tick_class,
                    append_to: this.layers.grid,
                });

                if (this.view_is(MONTH)) {
                    tick_x +=
                        (date_utils.get_days_in_month(date) *
                            this.options.column_width) /
                        30;
                } else {
                    tick_x += this.options.column_width;
                }
            }
        }

        make_grid_highlights() {
            // highlight today's date
            if (this.view_is(DAY)) {
                const x =
                    (date_utils.diff(
                        date_utils.today(),
                        this.gantt_start,
                        'hour'
                    ) /
                        this.options.step) *
                    this.options.column_width;
                const y = 0;
                const width = this.options.column_width;
                const height =
                    (this.options.bar_height + this.options.padding) *
                        this.tasks.length +
                    this.options.header_height +
                    this.options.padding / 2;

                createSVG('rect', {
                    x,
                    y,
                    width,
                    height,
                    class: 'today-highlight',
                    append_to: this.layers.grid,
                });
            }
        }

        make_dates() {
            for (let date of this.get_dates_to_draw()) {
                createSVG('text', {
                    x: date.lower_x,
                    y: date.lower_y,
                    innerHTML: date.lower_text,
                    class: 'lower-text',
                    append_to: this.layers.date,
                });

                if (date.upper_text) {
                    const $upper_text = createSVG('text', {
                        x: date.upper_x,
                        y: date.upper_y,
                        innerHTML: date.upper_text,
                        class: 'upper-text',
                        append_to: this.layers.date,
                    });

                    // remove out-of-bound dates
                    if (
                        $upper_text.getBBox().x > this.layers.grid.getBBox().width
                    ) {
                        $upper_text.remove();
                    }
                }
            }
        }

        get_dates_to_draw() {
            let last_date = null;
            const dates = this.dates.map((date, i) => {
                const d = this.get_date_info(date, last_date, i);
                last_date = date;
                return d;
            });
            return dates;
        }

        get_date_info(date, last_date, i) {
            if (!last_date) {
                last_date = date_utils.add(date, 1, 'year');
            }
            const date_text = {
                [QUARTER_DAY]: date_utils.format(date, 'HH', 'en'),
                [HALF_DAY]: date_utils.format(date, 'HH', 'en'),
                [DAY]: date.getDate() !== last_date.getDate() ? date_utils.format(date, 'D', 'en') : '',
                [WEEK]: date.getDate() !== last_date.getDate() ? date_utils.format(date, 'D MMM', 'en') : '',
                [MONTH]: date_utils.format(date, 'MMMM', 'en'),
                [YEAR]: date_utils.format(date, 'YYYY', 'en'),
            };

            const base_pos = {
                x: i * this.options.column_width,
                lower_y: this.options.header_height,
                upper_y: this.options.header_height - 25,
            };

            const x_pos = {
                [QUARTER_DAY]: this.options.column_width / 2,
                [HALF_DAY]: this.options.column_width / 2,
                [DAY]: this.options.column_width / 2,
                [WEEK]: 0,
                [MONTH]: this.options.column_width / 2,
                [YEAR]: this.options.column_width / 2,
            };

            return {
                upper_text: this.view_is(DAY) && (!last_date || date.getMonth() !== last_date.getMonth())
                    ? date_utils.format(date, 'MMMM', 'en')
                    : '',
                lower_text: date_text[this.options.view_mode],
                lower_x: base_pos.x + x_pos[this.options.view_mode],
                lower_y: base_pos.lower_y,
                upper_x: base_pos.x,
                upper_y: base_pos.upper_y,
            };
        }

        make_bars() {
            this.bars = this.tasks.map((task) => {
                const bar = new Bar(this, task);
                this.layers.bar.appendChild(bar.group);
                return bar;
            });
        }

        make_arrows() {
            this.arrows = [];
            for (let task of this.tasks) {
                let arrows = [];
                if (task.dependencies) {
                    arrows = task.dependencies
                        .split(',')
                        .map((task_id) => {
                            const dependency = this.get_task(task_id);
                            if (!dependency) return;
                            const arrow = new Arrow(
                                this,
                                this.bars[dependency._index], // from_task
                                this.bars[task._index] // to_task
                            );
                            this.layers.arrow.appendChild(arrow.element);
                            return arrow;
                        })
                        .filter(Boolean); // filter nulls
                }
                this.arrows = this.arrows.concat(arrows);
            }
        }

        map_arrows_on_bars() {
            for (let bar of this.bars) {
                bar.arrows = this.arrows.filter((arrow) => {
                    return (
                        arrow.from_task.task.id === bar.task.id ||
                        arrow.to_task.task.id === bar.task.id
                    );
                });
            }
        }

        set_width() {
            const cur_width = this.svg.getBoundingClientRect().width;
            const actual_width = this.svg
                .querySelector('.grid .grid-row')
                .getAttribute('width');
            if (cur_width < actual_width) {
                this.svg.setAttribute('width', actual_width);
            }
        }

        set_scroll_position() {
            const parent_element = this.svg.parentElement;
            if (!parent_element) return;

            const hours_before_first_task = date_utils.diff(
                this.get_oldest_starting_date(),
                this.gantt_start,
                'hour'
            );

            const scroll_pos =
                (hours_before_first_task / this.options.step) *
                    this.options.column_width -
                this.options.column_width;

            parent_element.scrollLeft = scroll_pos;
        }

        bind_grid_click() {
            $.on(
                this.svg,
                this.options.popup_trigger,
                '.grid-row, .grid-header',
                () => {
                    this.unselect_all();
                    this.hide_popup();
                }
            );
        }

        bind_bar_events() {
            let is_dragging = false;
            let x_on_start = 0;
            let y_on_start = 0;
            let is_resizing_left = false;
            let is_resizing_right = false;
            let parent_bar_id = null;
            let bars = []; // instanceof Bar
            this.bar_being_dragged = null;

            function action_in_progress() {
                return is_dragging || is_resizing_left || is_resizing_right;
            }

            $.on(this.svg, 'mousedown', '.bar-wrapper, .handle', (e, element) => {
                const bar_wrapper = $.closest('.bar-wrapper', element);

                if (element.classList.contains('left')) {
                    is_resizing_left = true;
                } else if (element.classList.contains('right')) {
                    is_resizing_right = true;
                } else if (element.classList.contains('bar-wrapper')) {
                    is_dragging = true;
                }

                bar_wrapper.classList.add('active');
                this.popup_wrapper.classList.add('hide'); // Hide popup during drag

                x_on_start = e.offsetX;
                y_on_start = e.offsetY;

                parent_bar_id = bar_wrapper.getAttribute('data-id');
                const ids = [
                    parent_bar_id,
                    ...this.get_all_dependent_tasks(parent_bar_id),
                ];
                bars = ids.map((id) => this.get_bar(id));

                this.bar_being_dragged = parent_bar_id;

                bars.forEach((bar) => {
                    const $bar = bar.group;
                    $bar.classList.add('active');
                    $bar.style.cursor = 'move';
                });
            });

            $.on(this.svg, 'mousemove', (e) => {
                if (!action_in_progress()) return;
                const dx = e.offsetX - x_on_start;
                // const dy = e.offsetY - y_on_start; // unused

                bars.forEach((bar) => {
                    const $bar = bar.group;
                    $bar.style.cursor = 'move';
                    if (is_resizing_left) {
                        bar.update_bar_position({ x: dx, width: -dx });
                    } else if (is_resizing_right) {
                        bar.update_bar_position({ width: dx });
                    } else if (is_dragging) {
                        bar.update_bar_position({ x: dx });
                    }
                });
            });

            document.addEventListener('mouseup', (e) => {
                if (is_dragging || is_resizing_left || is_resizing_right) {
                    bars.forEach((bar) => {
                        bar.group.classList.remove('active');
                        bar.group.style.cursor = 'pointer'; // Reset cursor
                    });
                    if (this.bar_being_dragged) {
                        this.bar_being_dragged = null;
                        bars.forEach((bar) => {
                            // save action
                             const { task } = bar;
                            this.trigger_event('date_change', [
                                task,
                                task._start,
                                task._end,
                            ]);
                        });
                    }
                }

                is_dragging = false;
                is_resizing_left = false;
                is_resizing_right = false;
            });
        }

        get_all_dependent_tasks(task_id) {
            let out = [];
            let to_process = [task_id];
            while (to_process.length) {
                const deps = to_process.reduce((acc, curr) => {
                    acc = acc.concat(this.dependency_map[curr]);
                    return acc;
                }, []);

                out = out.concat(deps);
                to_process = deps.filter((d) => !to_process.includes(d));
            }

            return out.filter(Boolean);
        }

        get_snap_position(dx) {
            let odx = dx,
                rem,
                position;

            if (this.view_is(WEEK)) {
                rem = dx % (this.options.column_width / 7);
                position =
                    odx -
                    rem +
                    (rem < this.options.column_width / 14
                        ? 0
                        : this.options.column_width / 7);
            } else if (this.view_is(MONTH)) {
                rem = dx % (this.options.column_width / 30);
                position =
                    odx -
                    rem +
                    (rem < this.options.column_width / 60
                        ? 0
                        : this.options.column_width / 30);
            } else {
                rem = dx % this.options.column_width;
                position =
                    odx -
                    rem +
                    (rem < this.options.column_width / 2
                        ? 0
                        : this.options.column_width);
            }
            return position;
        }

        unselect_all() {
            [...this.svg.querySelectorAll('.bar-wrapper')].forEach((el) => {
                el.classList.remove('active');
            });
             this.hide_popup();
        }

        view_is(modes) {
            if (typeof modes === 'string') {
                return this.options.view_mode === modes;
            }

            if (Array.isArray(modes)) {
                return modes.some((mode) => this.options.view_mode === mode);
            }

            return false;
        }

        get_task(id) {
            return this.tasks.find((task) => {
                return task.id == id;
            });
        }

        get_bar(id) {
            return this.bars.find((bar) => {
                return bar.task.id == id;
            });
        }

        show_popup(options) {
            if (!this.options.custom_popup_html) {
                // Default popup
                this.popup_wrapper.innerHTML = `
                    <div class="popup-content">
                        <div class="title">${options.title}</div>
                        <div class="subtitle">${options.subtitle}</div>
                    </div>
                `;
            } else {
                // Custom popup
            }
             this.popup_wrapper.classList.remove('hide');
             this.popup_wrapper.style.left = options.x + 'px';
             this.popup_wrapper.style.top = options.y + 'px';
        }

        hide_popup() {
            this.popup_wrapper.classList.add('hide');
        }

        trigger_event(event, args) {
            if (this.options['on_' + event]) {
                this.options['on_' + event].apply(null, args);
            }
        }

        get_oldest_starting_date() {
            return this.tasks
                .map((task) => task._start)
                .reduce((prev, current) => {
                    return prev <= current ? prev : current;
                });
        }

        clear() {
            this.svg.innerHTML = '';
        }
    }

    class Bar {
        constructor(gantt, task) {
            this.set_defaults(gantt, task);
            this.prepare();
            this.draw();
            this.bind();
        }

        set_defaults(gantt, task) {
            this.action_completed = false;
            this.gantt = gantt;
            this.task = task;
        }

        prepare() {
            this.prepare_values();
            this.prepare_helpers();
        }

        prepare_values() {
            this.invalid = this.task.invalid;
            this.height = this.gantt.options.bar_height;
            this.x = this.compute_x();
            this.y = this.compute_y();
            this.corner_radius = this.gantt.options.bar_corner_radius;
            this.duration =
                date_utils.diff(this.task._end, this.task._start, 'hour') /
                this.gantt.options.step;
            this.width = this.gantt.options.column_width * this.duration;
            this.progress_width =
                this.gantt.options.column_width *
                    this.duration *
                    (this.task.progress / 100) || 0;
            this.group = createSVG('g', {
                class: 'bar-wrapper ' + (this.task.custom_class || ''),
                'data-id': this.task.id,
            });
            this.bar_group = createSVG('g', {
                class: 'bar-group',
                append_to: this.group,
            });
            this.handle_group = createSVG('g', {
                class: 'handle-group',
                append_to: this.group,
            });
        }

        prepare_helpers() {
            createSVG('rect', {
                x: this.x,
                y: this.y,
                width: this.width,
                height: this.height,
                rx: this.corner_radius,
                ry: this.corner_radius,
                class: 'bar',
                append_to: this.bar_group,
            });

            createSVG('rect', {
                x: this.x,
                y: this.y,
                width: this.progress_width,
                height: this.height,
                rx: this.corner_radius,
                ry: this.corner_radius,
                class: 'bar-progress',
                append_to: this.bar_group,
            });

            createSVG('text', {
                x: this.x + this.width / 2,
                y: this.y + this.height / 2,
                innerHTML: this.task.name,
                class: 'bar-label',
                append_to: this.bar_group,
            });
        }

        draw() {
            this.draw_handles();
        }

        draw_handles() {
            const bar_corner_radius = this.gantt.options.bar_corner_radius;

            createSVG('rect', {
                x: this.x + 1,
                y: this.y + 1,
                width: this.width - 2,
                height: this.height - 2,
                rx: bar_corner_radius,
                ry: bar_corner_radius,
                class: 'handle progress',
                append_to: this.handle_group,
            });

            createSVG('rect', {
                x: this.x + 1,
                y: this.y + 1,
                width: 5,
                height: this.height - 2,
                rx: bar_corner_radius,
                ry: bar_corner_radius,
                class: 'handle left',
                append_to: this.handle_group,
            });

            createSVG('rect', {
                x: this.x + this.width - 6,
                y: this.y + 1,
                width: 5,
                height: this.height - 2,
                rx: bar_corner_radius,
                ry: bar_corner_radius,
                class: 'handle right',
                append_to: this.handle_group,
            });
        }

        bind() {
            this.group.addEventListener('click', (e) => {
                 this.gantt.trigger_event('click', [this.task]);
                 e.stopPropagation(); // prevent grid click
            });
        }

        update_bar_position({ x = null, width = null }) {
            const bar = this.bar_group.querySelector('.bar');
            if (x) {
                // get all x values of parent task
                const xs = this.task.dependencies.map((dep) => {
                    return this.gantt.get_bar(dep).x;
                });
                // constraint
                // todo
                this.update_attr(bar, 'x', x);
            }
            if (width && width >= this.gantt.options.column_width) {
                this.update_attr(bar, 'width', width);
            }
            this.update_label_position();
            this.update_handle_position();
            this.update_progressbar_position();
            this.update_arrow_position();
        }

        update_label_position_on_horizontal_scroll() {
             // implement logic to keep label visible
        }

        update_attr(element, attr, value) {
            value = +element.getAttribute(attr) + value;
            element.setAttribute(attr, value);
        }

        update_progressbar_position() {
            this.bar_group.querySelector('.bar-progress').setAttribute('x', this.bar_group.querySelector('.bar').getAttribute('x'));
            this.bar_group.querySelector('.bar-progress').setAttribute('width', this.bar_group.querySelector('.bar').getAttribute('width') * (this.task.progress / 100));
        }

        update_label_position() {
             const bar = this.bar_group.querySelector('.bar');
             const label = this.bar_group.querySelector('.bar-label');
             label.setAttribute('x', +bar.getAttribute('x') + +bar.getAttribute('width') / 2);
             label.setAttribute('y', +bar.getAttribute('y') + +bar.getAttribute('height') / 2);
        }

        update_handle_position() {
            const bar = this.bar_group.querySelector('.bar');
            this.handle_group.querySelector('.handle.left').setAttribute('x', +bar.getAttribute('x') + 1);
            this.handle_group.querySelector('.handle.right').setAttribute('x', +bar.getAttribute('x') + +bar.getAttribute('width') - 6);
        }

        update_arrow_position() {
            this.arrows = this.arrows || [];
            for (let arrow of this.arrows) {
                arrow.update();
            }
        }

        compute_x() {
            const { step, column_width } = this.gantt.options;
            const task_start = this.task._start;
            const gantt_start = this.gantt.gantt_start;

            const diff = date_utils.diff(task_start, gantt_start, 'hour');
            let x = (diff / step) * column_width;

            if (this.gantt.view_is(MONTH)) {
                const diff = date_utils.diff(task_start, gantt_start, 'day');
                x = (diff * column_width) / 30;
            }
            return x;
        }

        compute_y() {
            return (
                this.gantt.options.header_height +
                this.gantt.options.padding +
                this.task._index * (this.gantt.options.bar_height + this.gantt.options.padding)
            );
        }
    }

    class Arrow {
        constructor(gantt, from_task, to_task) {
            this.gantt = gantt;
            this.from_task = from_task;
            this.to_task = to_task;

            this.calculate_path();
            this.draw();
        }

        calculate_path() {
            let start_x =
                this.from_task.group.querySelector('.bar').getAttribute('x') +
                this.from_task.group.querySelector('.bar').getAttribute('width') / 2;

            const condition = () =>
                this.to_task.group.querySelector('.bar').getAttribute('x') +
                this.to_task.group.querySelector('.bar').getAttribute('width') / 2;

            let start_y =
                this.gantt.options.header_height +
                this.gantt.options.bar_height +
                (this.gantt.options.padding + this.gantt.options.bar_height) *
                    this.from_task.task._index +
                this.gantt.options.padding;

            const end_y =
                this.gantt.options.header_height +
                this.gantt.options.bar_height / 2 +
                (this.gantt.options.padding + this.gantt.options.bar_height) *
                    this.to_task.task._index +
                this.gantt.options.padding;

            const from_is_below_to =
                this.from_task.task._index > this.to_task.task._index;
            const curve = this.gantt.options.arrow_curve;
            const clockwise = from_is_below_to ? 1 : 0;
            const curve_y = from_is_below_to ? -curve : curve;
            const offset = from_is_below_to ? -curve : curve;

            this.path = `
                M ${start_x} ${start_y}
                V ${end_y + offset}
                a ${curve} ${curve} 0 0 ${clockwise} ${curve} ${curve_y}
                L ${condition()} ${end_y}
                m -5 -5
                l 5 5
                l -5 5`;

            if (
                this.to_task.group.querySelector('.bar').getAttribute('x') <
                this.from_task.group.querySelector('.bar').getAttribute('x') +
                    this.from_task.group.querySelector('.bar').getAttribute('width')
            ) {
                 // handle backward arrows
            }
        }

        draw() {
            this.element = createSVG('path', {
                d: this.path,
                'data-from': this.from_task.task.id,
                'data-to': this.to_task.task.id,
            });
        }

        update() {
            this.calculate_path();
            this.element.setAttribute('d', this.path);
        }
    }

    // UTILITIES
    const date_utils = {
        parse(date, date_separator = '-', time_separator = /[.:]/) {
            if (date instanceof Date) {
                return date;
            }
            const parts = date.split(' ');
            const date_parts = parts[0]
                .split(date_separator)
                .map((val) => parseInt(val, 10));
            const time_parts = parts[1]
                ? parts[1].split(time_separator).map((val) => parseInt(val, 10))
                : [0, 0];

            // new Date(year, monthIndex, day, hours, minutes)
            return new Date(
                date_parts[0],
                date_parts[1] - 1,
                date_parts[2],
                time_parts[0],
                time_parts[1]
            );
        },
        to_string(date, with_time = false) {
            if (!(date instanceof Date)) {
                throw new TypeError('Invalid argument type');
            }
            const vals = this.get_date_values(date);
            const date_string = `${vals.year}-${vals.month}-${vals.day}`;
            const time_string = `${vals.hr}:${vals.min}`;

            return `${date_string}${with_time ? ' ' + time_string : ''}`;
        },
        format(date, format_string = 'YYYY-MM-DD HH:mm', lang = 'en') {
             // Simple formatting for MVP
             if(format_string.includes('YYYY')) return date.getFullYear();
             if(format_string.includes('MMMM')) return date.toLocaleString(lang, { month: 'long' });
             if(format_string.includes('MMM')) return date.toLocaleString(lang, { month: 'short' });
             if(format_string.includes('MM')) return (date.getMonth()+1).toString().padStart(2, '0');
             if(format_string.includes('DD')) return date.getDate().toString().padStart(2, '0');
             if(format_string.includes('D')) return date.getDate();
             return date.toDateString();
        },
        diff(date_a, date_b, scale = 'day') {
            let milliseconds, seconds, hours, minutes, days, months, years;

            milliseconds = date_a - date_b;
            seconds = milliseconds / 1000;
            minutes = seconds / 60;
            hours = minutes / 60;
            days = hours / 24;
            months = days / 30;
            years = months / 12;

            if (!scale.endsWith('s')) {
                scale += 's';
            }

            return Math.floor(
                {
                    milliseconds,
                    seconds,
                    minutes,
                    hours,
                    days,
                    months,
                    years,
                }[scale]
            );
        },
        today() {
            const vals = this.get_date_values(new Date());
            return new Date(vals.year, vals.month, vals.day);
        },
        now() {
            return new Date();
        },
        add(date, qty, scale) {
            qty = parseInt(qty, 10);
            const vals = [
                date.getFullYear() + (scale === 'year' ? qty : 0),
                date.getMonth() + (scale === 'month' ? qty : 0),
                date.getDate() + (scale === 'day' ? qty : 0),
                date.getHours() + (scale === 'hour' ? qty : 0),
                date.getMinutes() + (scale === 'minute' ? qty : 0),
                date.getSeconds() + (scale === 'second' ? qty : 0),
            ];
            return new Date(...vals);
        },
        start_of(date, scale) {
            const scores = {
                year: 6,
                month: 5,
                day: 4,
                hour: 3,
                minute: 2,
                second: 1,
                millisecond: 0,
            };

            function should_reset(_scale) {
                const max_score = scores[scale];
                return scores[_scale] <= max_score;
            }

            const vals = [
                date.getFullYear(),
                should_reset('year') ? 0 : date.getMonth(),
                should_reset('month') ? 1 : date.getDate(),
                should_reset('day') ? 0 : date.getHours(),
                should_reset('hour') ? 0 : date.getMinutes(),
                should_reset('minute') ? 0 : date.getSeconds(),
                should_reset('second') ? 0 : date.getMilliseconds(),
            ];

            return new Date(...vals);
        },
        clone(date) {
            return new Date(date.valueOf());
        },
        get_date_values(date) {
            return {
                year: date.getFullYear(),
                month: date.getMonth(),
                day: date.getDate(),
                hr: date.getHours(),
                min: date.getMinutes(),
            };
        },
        get_days_in_month(date) {
             const no_of_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
             const month = date.getMonth();
             if(month !== 1) return no_of_days[month];
             // Leap year check
             const year = date.getFullYear();
             if ((year % 4 == 0 && year % 100 != 0) || year % 400 == 0) return 29;
             return 28;
        }
    };

    // DOM Utilities
    const $ = {
        on(element, event, selector, callback) {
            if (!callback) {
                callback = selector;
                $.bind(element, event, callback);
            } else {
                $.delegate(element, event, selector, callback);
            }
        },
        bind(element, event, callback) {
            event.split(' ').forEach((event) => {
                element.addEventListener(event, callback);
            });
        },
        delegate(element, event, selector, callback) {
            element.addEventListener(event, function (e) {
                const target = $.closest(selector, e.target);
                if (target) {
                    // e.target = target; // REMOVED: Illegal in strict mode
                    callback.call(this, e, target);
                }
            });
        },
        closest(selector, element) {
            if (!element) return null;

            if (element.matches && element.matches(selector)) {
                return element;
            }
            // Fallback for older browsers or text nodes
            if (!element.matches && element.nodeType === 3) { // Text Node
                 return $.closest(selector, element.parentNode);
            }

            return $.closest(selector, element.parentNode);
        },
        attr(element, attr, value) {
            if (!value && typeof attr === 'object') {
                for (let key in attr) {
                    element.setAttribute(key, attr[key]);
                }
            } else {
                element.setAttribute(attr, value);
            }
        },
    };

    function createSVG(tag, attrs) {
        const elem = document.createElementNS('http://www.w3.org/2000/svg', tag);
        for (let attr in attrs) {
            if (attr === 'append_to') {
                const parent = attrs.append_to;
                parent.appendChild(elem);
            } else if (attr === 'innerHTML') {
                elem.innerHTML = attrs.innerHTML;
            } else {
                elem.setAttribute(attr, attrs[attr]);
            }
        }
        return elem;
    }

    return Gantt;
})();