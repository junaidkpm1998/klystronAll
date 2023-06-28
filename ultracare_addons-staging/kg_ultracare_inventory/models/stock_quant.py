from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    consumed = fields.Boolean(string="Consumed")


    @api.model
    def _get_inventory_fields_write(self):
        """ Returns a list of fields user can edit when editing a quant in `inventory_mode`."""
        res = super(StockQuant, self)._get_inventory_fields_write()
        res += ['quantity', 'consumed']
        return res
