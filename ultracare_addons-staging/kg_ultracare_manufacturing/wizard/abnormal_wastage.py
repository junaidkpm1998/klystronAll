from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AbnormalWastage(models.TransientModel):
    _name = 'abnormal.wastage'
    _description = 'Abnormal Wastage'

    user_id = fields.Many2one('res.users', string="Responsible", required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    qty = fields.Float(string='Quantity', required=True, default=1)
    bill_of_material = fields.Many2one('mrp.bom', string="Bill of Material")
    wastage_lines = fields.One2many('abnormal.wastage.line', 'pro_id', string="Wastage Lines")
    manufacturing_id = fields.Many2one('mrp.production', string='MRP ID')
    uom = fields.Many2one('uom.uom', string="UoM")

    @api.onchange('manufacturing_id')
    def onchange_manufacturing_id(self):
        if self.manufacturing_id:
            lines = []
            self.wastage_lines = False
            for line in self.manufacturing_id.move_raw_ids:
                vals = {
                    'product_id': line.product_id.id,
                    'qty': line.product_uom_qty,
                    'uom_id': line.product_uom.id,
                    'move_id': line.id,
                    # 'price': line.price
                }
                lines.append((0, 0, vals))
            self.wastage_lines = lines
        else:
            self.wastage_lines = False

    def action_add_abnormal_wastage(self):
        if self.wastage_lines:
            lines = []
            for i in self.wastage_lines:
                print(i.move_id,"MOVEEEEE Wizarddd")
                vals = ((0, 0, {
                    'product_id': i.product_id.id,
                    'qty': i.qty,
                    'waste_qty': i.waste_qty,
                    'uom_id': i.uom_id.id,
                    'mrp_id': i.pro_id.manufacturing_id.id,
                    'move_id': i.move_id.id
                }))
                lines.append(vals)
            self.manufacturing_id.write({'abnormal_wastage_id': lines})


class AbnormalWastageLine(models.TransientModel):
    _name = 'abnormal.wastage.line'
    _description = 'Abnormal Wastage'

    pro_id = fields.Many2one('abnormal.wastage', string="ID")
    product_id = fields.Many2one('product.product', string="Product", required=True)
    qty = fields.Float(string="Quantity", default=0)
    waste_qty = fields.Float(string="Wastage Quantity", default=0)
    uom_id = fields.Many2one('uom.uom', string="Unit Of Measure")
    mrp_id = fields.Many2one('mrp.production', string='MRP Id')
    move_id = fields.Many2one('stock.move', string="Move Id")

    @api.onchange('product_id')
    def onchange_product(self):
        for line in self:
            if line.product_id:
                self.uom_id = line.product_id.uom_id.id
