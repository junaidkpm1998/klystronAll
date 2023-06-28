from odoo import models, fields


class WarrantyOnInvoice(models.Model):
    _inherit = 'account.move'

    invoice_warranty = fields.One2many('warranty.model', "invoice_id")
