# -*- coding: utf-8 -*-
# from odoo import http


# class KgUltracareSalesmanwiseReport(http.Controller):
#     @http.route('/kg_ultracare_salesmanwise_report/kg_ultracare_salesmanwise_report', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/kg_ultracare_salesmanwise_report/kg_ultracare_salesmanwise_report/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('kg_ultracare_salesmanwise_report.listing', {
#             'root': '/kg_ultracare_salesmanwise_report/kg_ultracare_salesmanwise_report',
#             'objects': http.request.env['kg_ultracare_salesmanwise_report.kg_ultracare_salesmanwise_report'].search([]),
#         })

#     @http.route('/kg_ultracare_salesmanwise_report/kg_ultracare_salesmanwise_report/objects/<model("kg_ultracare_salesmanwise_report.kg_ultracare_salesmanwise_report"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('kg_ultracare_salesmanwise_report.object', {
#             'object': obj
#         })
