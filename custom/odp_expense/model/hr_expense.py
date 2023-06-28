from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.expense'

    bill_reference = fields.Char(string="Bill Reference")
    expense_account = fields.Many2one('res.partner.bank', required=True)

