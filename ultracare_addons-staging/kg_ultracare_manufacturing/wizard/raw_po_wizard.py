from itertools import groupby
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date


class KGrawPoWizard(models.TransientModel):
    _name = 'kg.raw.po.wizard'
    _description = 'kg.raw.po.wizard'

    def delete(self):
        wiz_line = self.wiz_line

        for line in wiz_line:
            if line.select:
                line.unlink()

        return {
            "view_mode": 'form',
            'res_model': 'kg.raw.po.wizard',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    def create_po(self):
        wiz_line = self.wiz_line
        if not wiz_line:
            raise UserError(_('No Lines Found For Generating Purchase Agreement'))

        vendor_id = self.supplier_id
        agreement_type_id = self.agreement_type_id
        order_date = self.date
        line_vals_array = []

        purchase_agreement_id = self.env['purchase.requisition'].search(
            [('vendor_id', '=', vendor_id.id), ('type_id', '=', agreement_type_id.id), ('state', '=', 'draft')],
            limit=1)

        if purchase_agreement_id:
            for line in wiz_line:
                if not line.purchase_qty:
                    qty = line.qty
                if line.purchase_qty:
                    qty = line.purchase_qty
                line_vals = (0, 0, {
                    'product_id': line.product_id.id,
                    'product_qty': qty,
                    'product_uom_id': line.product_uom.id,
                    'price_unit': line.product_id.standard_price
                })
                line_vals_array.append(line_vals)
            purchase_agreement_id.write({'line_ids': line_vals_array})
            for line in wiz_line:
                line.requisition_id.rfq_id = purchase_agreement_id.id
                line.requisition_id.state = 'pa_created'

        if not purchase_agreement_id:
            for line in wiz_line:
                if not line.purchase_qty:
                    qty = line.qty
                if line.purchase_qty:
                    qty = line.purchase_qty
                line_vals = (0, 0, {
                    'product_id': line.product_id.id,
                    'product_qty': qty,
                    'product_uom_id': line.product_uom.id,
                    'price_unit': line.product_id.standard_price
                })
                line_vals_array.append(line_vals)

            vals = {
                'vendor_id': vendor_id.id,
                'line_ids': line_vals_array,
                'type_id': agreement_type_id.id,
                'ordering_date': order_date,
                'state': 'draft'
            }
            purchase_agreement_id = self.env['purchase.requisition'].create(vals)
            for line in wiz_line:
                line.requisition_id.rfq_id = purchase_agreement_id.id
                line.requisition_id.state = 'pa_created'

    @api.model
    def default_get(self, fields_list):
        res = super(KGrawPoWizard, self).default_get(fields_list)
        ids = self._context.get('active_ids', [])
        purchase_req = self.env['kg.purchase.req'].browse(ids)
        line_vals_array = []
        agreement = self.env['purchase.requisition.type'].search([('name', '=', 'Call For Tender')], limit=1)
        for line in purchase_req:
            if line.rfq_id:
                raise UserError("Already Purchase Agreement Created")
            product_id = line.kg_product and line.kg_product.id
            product_uom_qty = line.kg_qty
            name = line.kg_product.name
            product_uom = line.kg_product_uom and line.kg_product_uom.id

            vals = (0, 0,
                    {'product_id': product_id, 'qty': product_uom_qty, 'wiz_id': self.id, 'product_uom': product_uom,
                     'name': name, 'requisition_id': line.id, 'available_qty': line.kg_available_qty,
                     'purchase_qty': line.purchasing_qty})
            line_vals_array.append(vals)

        res.update({'wiz_line': line_vals_array,
                    'agreement_type_id': agreement.id})
        return res

    wiz_line = fields.One2many('kg.raw.po.wizard.line', 'wiz_id', string='Wiz Line', )
    supplier_id = fields.Many2one('res.partner', string='Vendor')
    date = fields.Date('Date', default=date.today())
    agreement_type_id = fields.Many2one('purchase.requisition.type', string="Agreement Type")
    is_tender = fields.Boolean(string="Is Tender", compute='compute_is_tender')

    @api.onchange('agreement_type_id')
    @api.depends('agreement_type_id')
    def compute_is_tender(self):
        agreement = self.env['purchase.requisition.type'].search([('name', '=', 'Call For Tender')], limit=1)
        if agreement:
            if self.agreement_type_id.id == agreement.id:
                self.is_tender = True
            else:
                self.is_tender = False
        else:
            self.is_tender = False


class KGrawPoWizardLine(models.TransientModel):
    _name = 'kg.raw.po.wizard.line'
    _description = 'kg.raw.po.wizard.line'
    wiz_id = fields.Many2one('kg.raw.po.wizard', string='Wiz')
    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Char(string='Description', )
    qty = fields.Float(string="Qty")
    unit_price = fields.Float(string="Cost")
    tax_id = fields.Many2one('account.tax', string='Vat')
    product_uom = fields.Many2one('uom.uom', string='Product Unit of Measure')
    select = fields.Boolean('Select')
    requisition_id = fields.Many2one('kg.purchase.req', string='Requisition')
    available_qty = fields.Float(string='Available Qty')
    purchase_qty = fields.Float(string="Purchase Quantity")
