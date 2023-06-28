from odoo import models, fields


class BookPublisher(models.Model):
    _name = 'book.publisher'

    name = fields.Char(string="Publisher name")
