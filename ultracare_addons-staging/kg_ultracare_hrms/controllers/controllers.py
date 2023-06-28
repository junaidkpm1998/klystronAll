# -*- coding: utf-8 -*-
# from odoo import http


# class KgUltracareHrms(http.Controller):
#     @http.route('/kg_ultracare_hrms/kg_ultracare_hrms', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/kg_ultracare_hrms/kg_ultracare_hrms/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('kg_ultracare_hrms.listing', {
#             'root': '/kg_ultracare_hrms/kg_ultracare_hrms',
#             'objects': http.request.env['kg_ultracare_hrms.kg_ultracare_hrms'].search([]),
#         })

#     @http.route('/kg_ultracare_hrms/kg_ultracare_hrms/objects/<model("kg_ultracare_hrms.kg_ultracare_hrms"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('kg_ultracare_hrms.object', {
#             'object': obj
#         })
