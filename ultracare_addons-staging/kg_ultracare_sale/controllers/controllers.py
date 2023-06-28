# -*- coding: utf-8 -*-
# from odoo import http


# class KgUltracareSale(http.Controller):
#     @http.route('/kg_ultracare_sale/kg_ultracare_sale', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/kg_ultracare_sale/kg_ultracare_sale/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('kg_ultracare_sale.listing', {
#             'root': '/kg_ultracare_sale/kg_ultracare_sale',
#             'objects': http.request.env['kg_ultracare_sale.kg_ultracare_sale'].search([]),
#         })

#     @http.route('/kg_ultracare_sale/kg_ultracare_sale/objects/<model("kg_ultracare_sale.kg_ultracare_sale"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('kg_ultracare_sale.object', {
#             'object': obj
#         })
