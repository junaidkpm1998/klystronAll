from odoo import models, fields


class DivisionMaster(models.Model):
    _name = 'division.master'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    head_title = fields.Char(string="Head Title")
    role = fields.Char(string="Role")
    division = fields.Char(string="Division")
    department = fields.Many2many('hr.department')
    department_code = fields.Char(string="Department Code")

    def name_get(self):
        result = []
        for record in self:
            code = record.department_code
            result.append((record.id, code))
        return result
