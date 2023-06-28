from odoo import models, fields, api, _


class SubGroup(models.Model):
    _name = 'product.sub.group'
    _description = 'Sub Groups'

    code = fields.Char("Code")
    name = fields.Char("Name")
    company_id = fields.Many2one('res.company', string="Company")
    remarks = fields.Text("Remarks")
