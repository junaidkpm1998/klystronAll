from odoo import models, fields, api


class AutomaticSoWizard(models.TransientModel):
    _name = 'automaticso.wizard'

    customer_id = fields.Many2one('res.partner', string='customer')
    quantity = fields.Integer(default=1)
    price = fields.Float(readonly=True, string="Unit Price")
    total_price = fields.Float(readonly=True)
    product_id = fields.Many2one('product.product')

    # description = fields.Text()

    def automatic_so_confirm(self):
        order = self.env['sale.order'].search([('partner_id', '=', self.customer_id.id), ('state', '=', 'draft')],
                                              limit=1)
        if order:
            order.write({
                'order_line': [(0, 0, {'product_id': self.product_id.id,
                                       'product_uom_qty': self.quantity
                                       })]
            })
        else:
            order = self.env['sale.order'].create({
                'partner_id': self.customer_id.id,
                'order_line': [(0, 0, {'product_id': self.product_id.id,
                                       'product_uom_qty': self.quantity,
                                       # 'name': "test"
                                       })]
            })
        order.action_confirm()

    @api.onchange('quantity')
    def onchange_quantity(self):
        self.total_price = self.price * self.quantity
