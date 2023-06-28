from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = 'Brand'

    name = fields.Char(string="Brand name")
    code = fields.Char("Code")
    remarks = fields.Text("Remarks")
    company_id = fields.Many2one('res.company', string="Company")

