from odoo import http
from odoo.http import request


class WebsiteForm(http.Controller):
    @http.route(['/warranty'], type='http', auth="user", website=True)
    def warranty(self):
        partners = request.env['res.partner'].sudo().search([])
        invoice = request.env['account.move'].sudo().search(
            [('state', '!=', 'draft'), ('move_type', '=', 'out_invoice')])
        product = request.env['product.product'].sudo().search([])
        # product = request.env['product.product'].sudo().search([('id', '=', request.invoice.invoice_line_ids.product_id.ids)])
        lot = request.env['stock.lot'].sudo().search([])

        values = {}
        values.update({
            'partners': partners,
            'invoice': invoice,
            'product': product,
            'lot': lot

        })
        return request.render("product_warranty.online_appointment_form", values)

    @http.route(['/appointment/submit'], type='http', auth="user", website=True)
    def submit_warranty(self, **post):
        # print(post, 'invoice')
        # print(request.partners)
        print(post.get('lot'),"this is lot")
        val = request.env['warranty.model'].sudo().create({
            'invoice_id': post.get('invoice'),
            # 'customer_name': post.get('partners'),
            'product_id': post.get('product'),
            'lot_id': post.get('lot')

        })
