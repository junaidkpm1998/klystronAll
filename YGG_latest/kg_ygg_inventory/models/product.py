# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    inventory_category = fields.Selection([
        ('issuance_prepaid', 'Issuance Basis Prepaid'),
        ('issuance_postpaid', 'Issuance Basis Post-paid'),
        ('redemption', 'Redemption Basis'),
        ('sold', 'Sold Basis')], string="Inventory Category")

    unrealised_commission_per = fields.Float('Unrealised Commission')

