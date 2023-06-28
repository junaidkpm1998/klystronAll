from odoo import models, fields, api, _


class InventoryValuation(models.Model):
    _inherit = 'stock.valuation.layer'

    product_category_id = fields.Many2one(related='product_id.categ_id', store = True)
