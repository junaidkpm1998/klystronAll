from odoo import _, api, fields, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_stationary_consumption = fields.Boolean('Stationary Consumption')

