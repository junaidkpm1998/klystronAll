from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # kg_invoice_id = fields.Many2one('account.invoice', string='Invoice', copy=False, )
    kg_sm_approved = fields.Boolean('Sales Manager Approved', default=False)
    kg_prod_plan_id = fields.Many2one('production.planning', string='Production Plan')
    kg_supply_place = fields.Char(string='Place Of Supply')
    kg_pan_it_no = fields.Char(string='PAN/IT No')
    payment_term_id = fields.Many2one('account.payment.term', string="Payment Terms", readonly=True)

    def do_new_transfer(self):
        if self.picking_type_code == 'outgoing' and not self.kg_sm_approved:
            raise UserError(_('Cannot Validate\n Sales manager approval required!'))
        return super(StockPicking, self).do_new_transfer()

    def sales_manager_approval(self):
        for record in self:
            if record.state != 'done':
                record.kg_sm_approved = True

    def create_invoice_from_delivery(self):
        if self.kg_invoice_id and self.kg_invoice_id.id:
            raise UserError(_('Invoice Already created'))
        if self.picking_type_code != 'outgoing':
            raise UserError(_('this option only for delivery orders'))
        sale_order_obj = self.sale_id
        min_date_obj = datetime.strptime(self.min_date, '%Y-%m-%d %H:%M:%S') + timedelta(minutes=240)
        date_value = min_date_obj.strftime("%Y-%m-%d %H:%M:%S")
        result = sale_order_obj.action_invoice_create(grouped=False)
        self.kg_invoice_id = result and result[0] or False
        if self.kg_invoice_id and self.kg_invoice_id.id:
            self.kg_invoice_id.kg_do_id = self.id
            self.kg_invoice_id.date_invoice = date_value
            self.kg_invoice_id.action_invoice_open()
        return True

    def refund_invoice_from_delivery(self):
        invoice_obj = self.env['account.invoice']
        sale_obj = self.env['sale.order']
        sale_line_obj = self.env['sale.order.line']
        i_line_obj = self.env['account.invoice.line']
        sale_journal = self.env['account.journal'].search([('type', '=', 'sale')])[0]
        sale_journal_id = sale_journal.id
        if self.kg_invoice_id and self.kg_invoice_id.id:
            raise UserError(_('Refund Already created'))
        if self.location_id.usage != 'customer':
            raise UserError(_('this option only for refunds'))
            # ~ sale_order_obj = self.sale_id
        min_date_obj = datetime.strptime(self.min_date, '%Y-%m-%d %H:%M:%S') + timedelta(minutes=240)
        date_value = min_date_obj.strftime("%Y-%m-%d %H:%M:%S")
        inv_id = invoice_obj.create({
            'partner_id': self.partner_id.id,
            'picking_id': self.id,
            'date_invoice': self.min_date,
            'tax_id_sale': 18,
            'type': 'out_refund',
            'journal_id': sale_journal_id,
            'warehouse_id': self.picking_type_id.warehouse_id.id,
            'account_id': self.partner_id.property_account_receivable_id.id,
        })
        for i in self.move_lines:
            accounts = i.product_id.product_tmpl_id.get_product_accounts()
            sale_order = sale_obj.search([('name', '=', self.group_id.name)])
            sale_line = sale_line_obj.search(
                [('order_id', '=', sale_order.id), ('product_id', '=', i.product_id.id), ('price_unit', '!=', 0)])
            price_unit = sale_line.price_unit or i.product_id.standard_price
            i_line_id = i_line_obj.create({
                'invoice_id': inv_id.id,
                'product_id': i.product_id.id,
                'price_unit': price_unit,
                'name': i.name,
                'account_id': accounts.get('income') and accounts['income'].id or False,
                'quantity': i.product_uom_qty,
                'uom_id': i.product_uom.id,
                'invoice_line_tax_ids': [(6, 0, [inv_id.tax_id_sale.id])],
            })
        self.kg_invoice_id = inv_id and inv_id[0] or False
        if self.kg_invoice_id and self.kg_invoice_id.id:
            self.kg_invoice_id.kg_do_id = self.id
            self.kg_invoice_id.date_invoice = date_value
            self.kg_invoice_id.compute_taxes()
            self.kg_invoice_id.action_invoice_open()
        return True

