from collections import defaultdict

from odoo import models, fields, api, _


class StockMove(models.Model):
    _inherit = 'stock.move'
    _description = 'Stock Move'

    normal_wastage = fields.Float(string="Normal Wastage")
    total_cost = fields.Float('Total Cost', default=0.00, compute='_compute_total_cost', store=True)
    jumbo_roll = fields.Boolean(related='product_id.jumbo_roll', string="Jumbo Roll", default=False)
    vendor_name = fields.Many2one(string="Vendor", related='picking_id.partner_id')
    is_vendor = fields.Boolean(string="Is Vendor", default=False, compute='_compute_vendor_list')
    final_qty = fields.Float(string="Final Qty", compute='compute_final_qty')

    @api.depends('normal_wastage', 'product_uom_qty')
    def compute_final_qty(self):
        for i in self:
            if i.state == 'done':
                i.final_qty = i.product_uom_qty - i.normal_wastage
            else:
                i.final_qty = 0.00

    @api.depends('product_id')
    def _compute_vendor_list(self):
        for rec in self:
            if rec.picking_id.picking_type_code == 'incoming':
                rec.is_vendor = True
            else:
                rec.is_vendor = False

    @api.depends('product_uom_qty', 'product_id.standard_price')
    def _compute_total_cost(self):
        for rec in self:
            if rec.product_id:
                rec.total_cost = rec.product_uom_qty * rec.product_id.standard_price
            else:
                rec.total_cost = 0.00

    @api.depends('normal_wastage')
    def onchange_normal_wastage(self):
        for i in self:
            if i.normal_wastage > 0:
                wastage_qty = i.normal_wastage
                a = i.product_uom_qty - wastage_qty
                i.write({'normal_wastage': a})

    @api.depends('move_line_ids.qty_done', 'move_line_ids.product_uom_id', 'move_line_nosuggest_ids.qty_done')
    def _quantity_done_compute(self):
        """ This field represents the sum of the move lines `qty_done`. It allows the user to know
        if there is still work to do.

        We take care of rounding this value at the general decimal precision and not the rounding
        of the move's UOM to make sure this value is really close to the real sum, because this
        field will be used in `_action_done` in order to know if the move will need a backorder or
        an extra move.
        """
        if not any(self._ids):
            # onchange
            for move in self:
                move.quantity_done = move._quantity_done_sml()
        else:
            # compute
            move_lines_ids = set()
            for move in self:
                move_lines_ids |= set(move._get_move_lines().ids)

            data = self.env['stock.move.line']._read_group(
                [('id', 'in', list(move_lines_ids)), ('is_wastage', '=', False)],
                ['move_id', 'product_uom_id', 'qty_done'], ['move_id', 'product_uom_id'],
                lazy=False
            )

            rec = defaultdict(list)
            for d in data:
                rec[d['move_id'][0]] += [(d['product_uom_id'][0], d['qty_done'])]

            for move in self:
                uom = move.product_uom
                move.quantity_done = sum(
                    self.env['uom.uom'].browse(line_uom_id)._compute_quantity(qty, uom, round=False)
                    for line_uom_id, qty in rec.get(move.ids[0] if move.ids else move.id, [])
                )


class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    _description = 'MRP Production'

    def _get_default_machine(self):
        res = self.env['maintenance.equipment'].search([('technician_user_id', '=', self.env.user.id)])
        return res and res[0] or False

    machine_id = fields.Many2one('maintenance.equipment', string="Machine", default=_get_default_machine)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    _description = 'Move Line'

    is_normal_wastage = fields.Boolean(string="Is Normal Wastage", default=False)
    is_wastage = fields.Boolean(string="Is Wastage", default=False)


