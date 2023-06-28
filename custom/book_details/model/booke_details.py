from odoo import models, fields, api
from datetime import date


class BookDetails(models.Model):
    _name = 'book.details'

    name = fields.Char(string="Book Name")
    image = fields.Image()
    author_ids = fields.Many2many('book.author')
    category = fields.Selection(
        [('history', 'History'), ('action', 'Action'), ('classics', 'Classics'), ('novel', 'Novel')])
    isbn = fields.Char(string="ISBN Number")
    publisher = fields.Many2one('book.publisher')
    serial_number = fields.Char(string="Serial Number")
    published_date = fields.Date("published Date")
    is_available = fields.Boolean(string="Is Available")
    partner_id = fields.Many2one('res.partner', domain="[('book_owner', '=', True)]")
    current_user_id = fields.Many2one('res.users', 'Current User', default=lambda self: self.env.user)
    # current_user_id = fields.Char("User ID",default=lambda self: self.env.user.name)
    extra_info = fields.Text()
    book_price = fields.Integer()
    product_res = fields.Many2one('product.reservation')
    product_id = fields.Many2one('product.product')
    quantity = fields.Integer()
    price = fields.Integer()
    today = date.today()
    inv_ref = fields.Char()

    def book_reservation_auto_archive(self):
        print("hiiiiii")
        print(self.today,"toze")
        expired_records = self.env['product.reservation'].search([('exp_date', '<', self.today)])
        expired_records.write({'active': False})

