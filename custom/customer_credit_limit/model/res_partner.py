from odoo import models, fields, api


class CustomerCreditLimit(models.Model):
    _inherit = 'res.partner'

    flag = fields.Boolean(string="Active Credit limit")
    warning_amount = fields.Integer(string="Warning amount")
    blocking_stage = fields.Integer(string="Blocking Stage")

    # @api.onchange('flag')
    # def aaaaaaaa(self):
    #     print("kkkkkkkkkkkvc")
    #     print(self.total_due,"total")





