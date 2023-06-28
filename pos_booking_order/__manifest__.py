{
    'name': 'POS Book Order',
    'version': '16.0.1.0.0',
    'summary': """Booking orders in pos of junaid""",
    'description': 'Book orders for customers in POS',
    'category': 'Point of Sale',
    'sequence': -1,
    'installable': True,
    'application': True,
    'depends': ['base', 'point_of_sale', 'product', 'stock'],
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/pos_session_view.xml',
        # 'views/booking_order_view.xml',
        # 'views/menu.xml'
    ],
    'demo': [],
    'assets': {
        # 'point_of_sale.assets': ['pos_booking_order/static/src/xml/session_button.xml',
        #                          'pos_booking_order/static/src/xml/session_booked.xml',
        #                          'pos_booking_order/static/src/xml/recipt_view.xml',
        #
        #                          'pos_booking_order/static/src/js/session_button.js',
        #                          'pos_booking_order/static/src/js/session_booked.js',
        #                          'pos_booking_order/static/src/js/popup_widget.js',
        #                          'pos_booking_order/static/src/js/booked_orders.js',
        #                          'pos_booking_order/static/src/js/model.js',
        #                          ],
    },
    'images': [],
    'qweb': [],
    'license': 'AGPL-3',

}
