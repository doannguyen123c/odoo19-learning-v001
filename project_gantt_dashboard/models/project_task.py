# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ProjectTask(models.Model):
    _inherit = 'project.task'

    x_date_start = fields.Date(
        string="Start Date",
        tracking=True,
        index=True,
        help="Custom Start Date used for Gantt Dashboard visualization."
    )

    @api.constrains('x_date_start', 'date_deadline')
    def _check_dates(self):
        """
        Ensure that the Start Date is not later than the Deadline.
        Logic applies only if both dates are set.
        """
        for task in self:
            if task.x_date_start and task.date_deadline:
                if task.x_date_start > task.date_deadline:
                    raise ValidationError(_(
                        "Error: Start Date (%(start)s) cannot be later than Deadline (%(end)s).",
                        start=task.x_date_start,
                        end=task.date_deadline
                    ))
