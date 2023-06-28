from odoo import models, fields, api, _
from odoo.exceptions import UserError


class kg_purhcase_req(models.Model):
    _name = 'kg.purchase.req'
    _rec_name = 'kg_product'
    _description = "Purchase Request"
    _inherit = ['mail.thread']

    @api.onchange('kg_product')
    def _onchange_product(self):
        product = self.kg_product
        if product:
            self.kg_product_uom = product.uom_po_id and product.uom_po_id.id

    def action_open_quants(self):
        product = self.kg_product and self.kg_product.id
        action = self.env.ref('stock.product_open_quants').read()[0]
        action['domain'] = [('product_id', '=', product)]
        action['context'] = {'search_default_locationgroup': 1, 'search_default_internal_loc': 1}
        return action

    kg_product = fields.Many2one('product.product', 'Product')
    rfq_id = fields.Many2one('purchase.requisition', 'Purchase Agreement')
    kg_product_uom = fields.Many2one('uom.uom', 'UOM')
    kg_date = fields.Date('Date')
    required_date = fields.Date('Required Date')
    notes = fields.Text('Notes')
    kg_qty = fields.Float('Quantity')
    # kg_prod_plan_id = fields.Many2one('production.planning', 'Production Plan')
    kg_sf_id = fields.Many2one('kg.sales.forecast', 'Sales Forecast')
    production_planning = fields.Many2one('production.planning', string="Production Planning")
    kg_available_qty = fields.Float(string="Available Qty", compute='compute_kg_available_qty')
    location_id = fields.Many2one('stock.location')
    state = fields.Selection([
        ('new', 'New'),
        ('pa_created', 'PA Created')], string='State',
        copy=False, default='new', track_visibility='onchange')
    purchasing_qty = fields.Float(string="Purchase Quantity")

    def action_open_po(self):
        if not self.rfq_id.id:
            raise UserError("Please create Purchase Requisition request for open Purchase Agreement")
        else:
            return {
                "view_mode": 'form',
                'res_model': 'purchase.requisition',
                'res_id': self.rfq_id.id,
                'type': 'ir.actions.act_window',
                'target': 'current'
            }

    @api.onchange('kg_qty', 'kg_available_qty')
    def onchange_purchase_qty(self):
        if self.kg_qty:
            self.purchasing_qty = self.kg_qty - self.kg_available_qty

    @api.depends('kg_product')
    def compute_kg_available_qty(self):
        for i in self:
            if i.kg_product:
                parameter_obj = self.env['stock.location'].search(
                    [('name', '=', 'Stock'), ('usage', '=', 'internal')])
                quant = self.env['stock.quant'].search(
                    [('location_id', '=', parameter_obj.id), ('product_id', '=', i.kg_product.id)])
                i.kg_available_qty = sum(quant.mapped('quantity'))
            else:
                i.kg_available_qty = 0
