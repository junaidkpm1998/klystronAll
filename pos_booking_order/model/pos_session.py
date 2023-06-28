from odoo import models, fields


class PosOrderBooking(models.Model):
    _inherit = 'pos.config'

    booking_order = fields.Boolean(string='Booking Order')


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()
        print('pos_ui')
        result += [
            'booking.order', 'book.order.line'
        ]
        return result

    def _loader_params_booking_order(self):
        return {
            'search_params': {
                'fields': ['reference_no', 'partner_id', 'phone', 'date_order', 'pickup_date', 'deliver_date', 'total',
                           "state", "note"],
            },
        }

    def _loader_params_book_order_line(self):
        return {
            'search_param': {
                'fields': ['order_id', 'product_id', 'price_unit', 'qty', 'price_subtotal', 'price_subtotal_incl',
                           'discount', 'create_date', 'tax_ids'],
            },
        }

    def _get_pos_ui_booking_order(self, params):
        # print('booking_order', params)
        # print(self.env['booking.order'].search_read(**params['search_params']))
        return self.env['booking.order'].search_read(**params['search_params'])

    def _get_pos_ui_book_order_line(self, param):
        # print('book_order_line', param)
        # print(self.env['book.order.line'].search_read(**param['search_param']))
        return self.env['book.order.line'].search_read(**param['search_param'])
