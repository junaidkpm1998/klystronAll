from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    expense_approver = fields.Many2one('res.users', string='Expense Approver')
