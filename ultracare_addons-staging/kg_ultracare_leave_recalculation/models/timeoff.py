# -*- coding: utf-8 -*-

from odoo import models, fields

class InhTimeoff(models.Model):
    _inherit = 'hr.leave.allocation'
    _description = 'Inherit Leave Allocation'

    public_holiday_id = fields.Many2one('resource.calendar.leaves','Public Holiday')