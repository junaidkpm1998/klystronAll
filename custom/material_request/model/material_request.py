from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MaterialRequest(models.Model):
    _name = 'material.request'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('res.partner', required=True)
    choice = fields.Selection([('po', 'Purchase order'), ('internal_transfer', 'Internal Transfer')], string='Choice',
                              required=True)
    po_count = fields.Integer(compute='get_po_count')
    transfer_flag = fields.Boolean(default=False)
    transfer_flag2 = fields.Boolean(default=False)
    operation_type_id = fields.Many2one('stock.picking.type', readonly=False)
    purchase_order_ids = fields.Many2many('purchase.order', readonly=True)

    order_line = fields.One2many('multiple.products', 'products')
    stock_id = fields.Many2one('stock.picking', readonly=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('submit', 'Submitted'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='draft')

    def request_material_request(self):
        print(self, "self")
        self.write({
            'state': 'submit',
        })

    def submit_material_request(self):
        print(self, "self")
        self.write({
            'state': 'approved',
        })

    def reject_material_request(self):
        print(self, "self")
        self.write({
            'state': 'rejected',
        })

    def create_rfq(self):
        return {
            'name': _('Test Wizard'),
            'type': 'ir.actions.act_window',
            'res_model': 'request.material.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_material_request_id': self.id}
        }

    def create_internal_transfer(self):
        print("k")
        if self.choice == 'internal_transfer':
            if self.order_line:
                vals = []
                for rec in self.order_line:
                    print(rec)
                    vals.append((0, 0, {
                        "name": "internal transfer",
                        'product_id': rec.product_id.id,
                        'location_id': self.operation_type_id.default_location_src_id.id,
                        'location_dest_id': self.operation_type_id.default_location_dest_id.id,
                        'product_uom_qty': rec.quantity,
                        'quantity_done': rec.quantity
                    }))

                stock = self.env['stock.picking'].create({
                    'partner_id': self.employee_id.id,
                    "picking_type_id": self.operation_type_id.id,
                    'location_id': self.operation_type_id.default_location_src_id.id,
                    'location_dest_id': self.operation_type_id.default_location_dest_id.id,
                    "move_ids": vals
                })
                print(stock.id, "stock.id")
                self.stock_id = stock.id
                print('stock_id', self.stock_id)
                self.transfer_flag2 = True

        else:
            raise ValidationError(_("Fill the line"))

    def get_po(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('material_request_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def get_po_count(self):
        for record in self:
            record.po_count = self.env['purchase.order'].search_count(
                [('material_request_id', '=', self.id)])
