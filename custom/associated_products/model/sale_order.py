from odoo import models, fields, api


class AssociatedproductSale(models.Model):
    _inherit = 'sale.order'

    associated_product_bool = fields.Boolean(default=False)

    @api.onchange('associated_product_bool')
    def _onchange_associated_product_bool(self):
        print("ss")
        if self.associated_product_bool:
            for rec in self.partner_id.associated_products:
                self.order_line = [(0, 0, {'product_id': rec, 'product_uom_qty':1})]
                print(rec.name,", rec name")

            # print(self.partner_id.associated_products.name)
            # for line in self.partner_id.associated_products.name:
            #     print()
            #     print(line,"linee")
            # self.order_line = [(0,0,{'product_id': line})]
            #     line_vals.append([(0, 0, {'product': line, 'saleorder_number': self.ids})])
            # print(line_vals,"line valsss")
            #
            # record = self.env['sale.order.line'].create({
            #     # 'order_id': 1,
            #     'product_template_id': line_vals,
            #     # 'name': "jjjjjjj",
            #     # 'product_uom_qty': 1,
            #     # 'price_unit': 100,
            # })

            # self.x_field = record.id
