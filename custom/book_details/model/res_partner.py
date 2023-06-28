from odoo import models, fields
from odoo.exceptions import ValidationError


class BookPartner(models.Model):
    _inherit = 'res.partner'

    # aaaa = fields.Boolean(string="Invoice_need")
    book_owner = fields.Boolean(string="Is Book Owner")
    need_invoice = fields.Boolean(string="Need invoice")
    need_dn = fields.Boolean(string="Need DB")

    def show_reservation(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reservations',
            'view_mode': 'tree',
            'res_model': 'product.reservation',
            'domain': [('customer_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def need_invoice_button(self):
        print("hhhh")
        val = self.env['product.reservation'].search([('customer_id', '=', self.id)])
        if val:
            print(val, "val")
            invoice_lines = []

            vals = {
                'product_id': val.products_ids.product_id.id
            }
            invoice_lines.append((0, 0, vals))

            inv = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': self.id,
                'invoice_line_ids': invoice_lines
            })
            inv.action_post()
            temp = self.env['book.details'].search([('partner_id', '=', self.id)])
            temp.inv_ref = inv.name
            temp.write({'inv_ref': inv.name})

            print(inv.name, "inv")

            return temp

        else:
            raise ValidationError('No product reservation available for this customer')

    def need_dn_button(self):
        print("kkk")
        invoice_lines = []
        val = self.env['product.reservation'].search([('customer_id', '=', self.id)])
        if val:
            vals = {
                'product_id': val.products_ids.product_id.id
            }
            invoice_lines.append((0, 0, vals))

            inv = self.env['stock.picking'].create({
                'picking_type_id': self.env.ref(
                    'stock.picking_type_out').id,
                'location_id': self.env.ref(
                    'stock.picking_type_out').default_location_src_id.id,
                'location_dest_id': self.env.ref(
                    'stock.picking_type_out').default_location_dest_id.id,
                'partner_id': self.id,
                'move_line_ids': invoice_lines
            })
        else:
            raise ValidationError('No product reservation available for this customer')
