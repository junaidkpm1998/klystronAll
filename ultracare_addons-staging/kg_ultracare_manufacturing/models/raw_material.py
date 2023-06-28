from odoo import models, fields, api, _
from odoo.exceptions import UserError


class kg_raw_mat_line(models.Model):
    _name = 'kg.raw.mat.line'
    _description = 'RM Lines'

    def action_open_quants(self):
        product = self.kg_product and self.kg_product.id
        action = self.env.ref('stock.product_open_quants').read()[0]
        action['domain'] = [('product_id', '=', product)]
        action['context'] = {'search_default_locationgroup': 1, 'search_default_internal_loc': 1}
        return action

    def create_purchase_req(self):
        kg_purchase_requisition_id = self.kg_purchase_requisition_id and self.kg_purchase_requisition_id.id
        if kg_purchase_requisition_id:
            raise UserError(_('Already purchase requisition created'))

        kg_product = self.kg_product and self.kg_product.id
        kg_product_uom = self.kg_product_uom and self.kg_product_uom.id
        kg_date = self.kg_date
        required_date = self.req_date
        notes = self.notes
        kg_qty = self.kg_qty
        kg_prod_plan_id = self.kg_prod_plan_id and self.kg_prod_plan_id.id
        state = 'new'
        vals = {'kg_product': kg_product,
                'kg_product_uom': kg_product_uom,
                'kg_date': kg_date,
                'required_date': required_date,
                'notes': notes,
                'kg_qty': kg_qty,
                'kg_prod_plan_id': kg_prod_plan_id,
                'state': state}
        purchase_req = self.env['kg.purhcase.req'].create(vals)
        self.kg_purchase_requisition_id = purchase_req and purchase_req.id

        return True

    def kg_quick_po(self):
        return {
            'name': 'Quick RFQ',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'kg.raw.po.wizard',
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    name = fields.Char('Name')
    kg_product = fields.Many2one('product.product', 'Product')
    kg_product_uom = fields.Many2one('uom.uom', 'UOM')
    kg_date = fields.Date('Date')
    req_date = fields.Date('Req.Date')
    kg_shift_id = fields.Many2one('shift.master', string="Shift")
    kg_qty = fields.Float('Quantity')
    req_qty = fields.Float('Req.Qty')
    notes = fields.Text('Notes')
    kg_prod_plan_id = fields.Many2one('production.planning', 'Production Plan')
    kg_purchase_requisition_id = fields.Many2one('kg.purhcase.req', 'Purchase Req.')

    @api.onchange('kg_product')
    def onchange_prod(self):
        for record in self:
            record.kg_product_uom = record.kg_product.uom_id.id
