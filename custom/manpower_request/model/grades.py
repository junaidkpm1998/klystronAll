from odoo import models, fields


class Grades(models.Model):
    _name = 'grades'

    name = fields.Char(string="grades")
    department = fields.Many2one('hr.department', string="Department")
    grade_name = fields.Char(string="Grade Name")
    createdby_id = fields.Many2one('res.users')
    sequence = fields.Integer(string="Sequence")
    table = fields.Char(string="Table")
    salary_structure_id = fields.Many2one('hr.payroll.structure', string="Salary Structure")
    gratituty_period = fields.Integer(string="Gratituty Period  in Months")
    payscale_ids = fields.One2many('salary.splitup','salary_split_ids')


class Payscale(models.Model):
    _inherit = 'salary.splitup'

    salary_split_ids = fields.Many2one('grades')
