from odoo import models, fields


class HrJob(models.Model):
    _inherit = 'hr.job'

    division = fields.Many2one('division.master', string="Division")
