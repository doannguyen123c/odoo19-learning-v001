from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError
from datetime import datetime

class NotificationTag(models.Model):
    _name = 'notification.tag'
    _description = 'Notification Tag'
    
    name = fields.Char(string='Tag Name', required=True)
    color = fields.Integer(string='Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists!"),
    ]

class NotificationBoard(models.Model):
    _name = 'notification.board'
    _description = 'Notification Board'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Title', required=True, tracking=True)
    content = fields.Html(string='Content', sanitize=True, strip_style=False)
    
    cover_image = fields.Binary(string="Cover Image", attachment=True)
    
    tag_ids = fields.Many2many('notification.tag', string='Tags')
    
    create_date = fields.Datetime(string='Created On', readonly=True)
    write_date = fields.Datetime(string='Last Updated', readonly=True)
    
    user_id = fields.Many2one('res.users', string='Author', default=lambda self: self.env.uid, readonly=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('published', 'Published')
    ], string='Status', default='draft', tracking=True)
    
    def action_publish(self):
        self.write({'state': 'published'})
        return True