from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ygg_sale_order_id = fields.Many2one('ygg.orders.order', string="YGG Sale Order")

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()

        return res




