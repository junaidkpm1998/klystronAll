from odoo import api, fields, models


class KGStockLot(models.Model):
    _inherit = 'stock.lot'

    kg_picking_id = fields.Many2one('stock.picking', string='Picking', readonly=True)
    is_picking = fields.Boolean(default=False,string='Is Picking')

class KGStockMoveLineLot(models.Model):
    _inherit = 'stock.move.line'

    def _get_value_production_lot(self):
        self.ensure_one()
        return {
            'company_id': self.company_id.id,
            'name': self.lot_name,
            'product_id': self.product_id.id,
            'kg_picking_id':self.picking_id.id,
            'is_picking': True
        }
