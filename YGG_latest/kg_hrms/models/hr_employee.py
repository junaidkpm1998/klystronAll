from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    division = fields.Many2one('division.master', string="Division")
    sl_no = fields.Integer(string="Sl no:")
