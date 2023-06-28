from odoo import models, fields, api


class RelatedBook(models.Model):
    _inherit = 'product.product'

    related_book = fields.Many2one('book.details')
    # product_res = fields.Many2one('product.reservation')
    @api.onchange('related_book')
    def onchange_related_book(self):
        print("hiii")
        # self.write({'lst_price': self.related_book.book_price})
        self.lst_price = self.related_book.book_price
        self.default_code = self.related_book.isbn
