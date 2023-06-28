from odoo import models, fields, api


class AutomaticPurchaseOrder(models.TransientModel):
    _name = 'automaticpo.wizard'

    customer_id = fields.Many2one('res.partner', string='Customer')
    quantity = fields.Integer(string="Quantity", default=1)
    price = fields.Float(string="price", readonly=True)
    product_id = fields.Many2one('product.product', readonly=True)
    total_price = fields.Float(readonly=True)

    @api.onchange('quantity')
    def onchange_quantity(self):
        self.total_price = self.price * self.quantity

    def automatic_po_confirm(self):
        print("hi")
        order = self.env['purchase.order'].search([('partner_id', '=', self.customer_id.id), ('state', '=', 'draft')],
                                                  limit=1)
        if order:
            order.write({
                'order_line': [(0, 0, {'product_id': self.product_id.id,
                                       'product_qty': self.quantity
                                       })]
            })
        else:
            order = self.env['purchase.order'].create({
                'partner_id': self.customer_id.id,
                'order_line': [(0, 0, {'product_id': self.product_id.id,
                                       'product_qty': self.quantity,
                                       # 'name': "test"
                                       })]
            })
        order.button_confirm()
