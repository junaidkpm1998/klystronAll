from odoo import models, fields


class MultipleProducts(models.Model):
    _name = 'multiple.products'

    products = fields.Many2one('material.request')
    product_id = fields.Many2one('product.product', string='products', required=True)
    quantity = fields.Integer(string='Quantity', required=True)
    price = fields.Float(string='price', readonly=True, compute='_price_calculation')
    unit_price = fields.Float(related='product_id.list_price', string="Unit Price", readonly=True)

    def _price_calculation(self):
        self.price = self.quantity * self.product_id.list_price
