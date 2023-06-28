from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockLot(models.Model):
    _inherit = 'stock.lot'

    def name_get(self):
        result = []
        for account in self:
            name = account.name + '  (' + str(account.product_qty) + ' Qty)'
            result.append((account.id, name))
        return result
