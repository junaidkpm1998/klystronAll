from odoo import models, fields


class RequestMaterialWizard(models.TransientModel):
    _name = 'request.material.wizard'

    customer_ids = fields.Many2many('res.partner', string='vendor')
    material_request_id = fields.Many2one('material.request')

    def create_po(self):
        lst = []
        for product in self.material_request_id.order_line:
            lst.append((0, 0, {'product_id': product.product_id.id,
                               'product_qty': product.quantity
                               }))

        for customer in self.customer_ids:
            order = self.env['purchase.order'].create({
                'partner_id': customer.id,
                'order_line': lst
            })
            order.button_confirm()
            self.material_request_id.purchase_order_ids |= order
            self.material_request_id.transfer_flag = True
            print("self.material_request_id", self.material_request_id)
            self.material_request_id.purchase_order_ids.material_request_id = self.material_request_id
