from odoo import models, fields


class WarrantyOnProductForm(models.Model):
    _inherit = "product.product"

    warranty_periods = fields.Integer()
    warranty_type = fields.Selection(
        [('servie_warranty', 'Service Warranty'), ('replacement_warranty', 'Replacement warranty')],
        string='Warranty Type')
    warranty = fields.Boolean(default=True)
    stock_connection = fields.Many2many('stock.lot')

