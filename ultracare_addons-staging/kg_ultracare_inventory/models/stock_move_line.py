from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockmoveLine(models.Model):
    _inherit = 'stock.move.line'

    consumed = fields.Boolean(string="Consumed", store=True)
    vendor_name = fields.Many2one(string="Vendor", related='picking_id.partner_id')
    is_vendor = fields.Boolean(string="Is Vendor", default=False, compute='_compute_vendor_list')

    @api.depends('product_id')
    def _compute_vendor_list(self):
        for rec in self:
            if rec.picking_id.picking_type_code == 'incoming':
                rec.is_vendor = True
            else:
                rec.is_vendor = False

    @api.constrains('qty_done')
    def constraints_qty_done(self):
        for i in self:
            if i.lot_id and not i.is_inventory:
                if i.lot_id.product_qty < i.qty_done:
                    raise UserError("You cannot consume quantities more than available.")
