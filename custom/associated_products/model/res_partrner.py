from odoo import models, fields


class CustomerProduct(models.Model):
    _inherit = 'res.partner'

    associated_products = fields.Many2many('product.product', string="Associated product")
