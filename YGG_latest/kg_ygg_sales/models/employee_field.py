from odoo import api, fields, models

class EmployeeModel(models.Model):
    _inherit = 'hr.employee'


    resident_id = fields.Char('Resident ID')
