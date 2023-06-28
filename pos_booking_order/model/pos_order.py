from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    booking_ref = fields.Many2one('booking.order', string='Booking Ref')

    @api.model
    def _order_fields(self, ui_order):
        print("pos order")
        """Passing value of booked order ref to PoS order"""
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        print(ui_order)
        if ui_order['booked_data']:
            print("name")
            order_fields['booking_ref'] = ui_order['booked_data']['id']
            print("kitrwadfs")
            self.env['booking.order'].search([('id', '=', ui_order['booked_data']['id'])]).write({'state': 'done'})
        else:
            print("gggggg")
        return order_fields



