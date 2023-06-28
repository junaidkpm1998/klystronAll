from odoo import fields, models, api


class KGInheritHRContract(models.Model):
    _inherit = "hr.contract"

    basic_salary = fields.Monetary(string="Basic Salary")
