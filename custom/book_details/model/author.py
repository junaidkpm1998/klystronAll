from odoo import models, fields


class BookAuthor(models.Model):
    _name = 'book.author'

    name = fields.Char(string="Author Name")
