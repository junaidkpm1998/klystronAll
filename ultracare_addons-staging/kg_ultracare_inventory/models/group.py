from odoo import models, fields, api, _


class ProductGroup(models.Model):
    _name = 'product.group'
    _description = 'Groups'

    code = fields.Char("Code")
    name = fields.Char("Name")
    company_id = fields.Many2one('res.company', string="Company")
    remarks = fields.Text("Remarks")

class KGMrpBomByproduct(models.Model):
    _inherit = 'mrp.bom.byproduct'
