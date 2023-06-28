from odoo import models, fields, api


class SaleOrderBookDetails(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        # print("jjj")
        order = self.env['product.reservation'].search([('customer_id', '=', self.partner_id.id)])
        if order:
            print(order, "ordr")
            print(order.products_ids.quantity, "qty")
            print(order.products_ids.product_id.name, "prdct")
            self.order_line = [(0, 0, {'product_id': order.products_ids.product_id,
                                       'product_uom_qty': order.products_ids.quantity
                                       })]

        # print(self.products_ids.product_id,"eee")
        # order.write({
        #     self.order_line: [(0, 0, {'product_id': order.products_ids.product_id,
        #                               'product_uom_qty': order.products_ids.quantity
        #                               })]
        # })

        else:
            print("illa")
