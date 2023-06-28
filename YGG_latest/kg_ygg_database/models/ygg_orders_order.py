from odoo import api, fields, models, _
import pymssql
import xmlrpc.client
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class YggOrdersOrder(models.Model):
    _name = 'ygg.orders.order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YGG Orders'
    _order = 'id desc'

    name = fields.Char("Name", default="New", required=True, readonly=True)
    ygg_record_id = fields.Integer("YGG Record ID")
    db_name = fields.Char("Database name")
    amount = fields.Monetary('Amount')
    created_on = fields.Datetime("Created On")
    modified_on = fields.Datetime("Modified On")
    status = fields.Selection([('pending', 'Pending'),('completed', 'Completed'),('invoice', 'Invoice Created'), ('cancelled', 'Cancelled')], default='pending', copy=False)
    # country_id = fields.Many2one()
    # customer_id = fields.Many2one()
    # currency_id = fields.Many2one()
    country_id = fields.Many2one('res.country', string="Country")
    customer_id = fields.Many2one('res.partner', string="Corporate")
    currency_id = fields.Many2one('res.currency', string='Currency')
    credit_consumed = fields.Monetary('Credit Consumed')
    amount_payable = fields.Monetary('Amount Payable')
    service_fee = fields.Monetary('Service Fee')
    vat_fee = fields.Monetary('Vat Fee')
    payment_id = fields.Many2one('account.payment')
    product_id = fields.Many2one('product.product', string="Brand")
    sale_id = fields.Many2one('sale.order', string="Sale Order", copy=False)
    commission_entry_id = fields.Many2one('account.move', string="Commission Entry", copy=False)
    order_lines = fields.One2many('orders.order.line', 'order_id', copy=True)

    inv_status = fields.Selection([('pending', 'Pending'), ('invoiced', 'Invoiced')], default='pending')
    payment_status = fields.Selection([('pending', 'Pending'),('paid', 'Paid'),('cancelled', 'Cancelled')], default='pending')
    cart_id = fields.Integer("Cart ID")

    # def action_create_invoice(self):
    #     action = self.env["ir.actions.actions"]._for_xml_id("sale.action_view_sale_advance_payment_inv")
    #     so_ids = (self.sale_order_id | self.task_ids.sale_order_id).filtered(lambda so: so.invoice_status == 'to invoice').ids
    #     action['context'] = {
    #         'active_id': so_ids[0] if len(so_ids) == 1 else False,
    #         'active_ids': so_ids
    #     }
    #     if not self.has_any_so_to_invoice:
    #         action['context']['default_advance_payment_method'] = 'percentage'
    #     return action

    def action_create_invoice(self):
        invoice_lines = []
        ygg_so = self.env['ygg.orders.order'].browse(self.env.context['active_ids'])
        partners = ygg_so.mapped('customer_id')
        print("partners", partners)
        if len(partners) > 1:
            raise UserError(_("Corporate should be same"))
        for obj in ygg_so:
            if obj.sale_id.invoice_status == 'to invoice':
                for line in obj.sale_id.order_line:
                    vals = {
                        'name': line.name,
                        'price_unit': line.price_unit,
                        'quantity': line.product_uom_qty,
                        'product_id': line.product_id.id,
                        'product_uom_id': line.product_uom.id,
                        'tax_ids': [(6, 0, line.tax_id.ids)],
                        'sale_line_ids': [(6, 0, [line.id])],
                    }
                    invoice_lines.append((0, 0, vals))

        print("invoice_lines", invoice_lines)
        if invoice_lines:
            invoice_id = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'invoice_origin': ygg_so[0].sale_id.name,
                'invoice_user_id': ygg_so[0].sale_id.user_id.id,
                'partner_id': ygg_so[0].sale_id.partner_invoice_id.id,
                'currency_id': ygg_so[0].sale_id.pricelist_id.currency_id.id,
                'invoice_line_ids': invoice_lines
            })
            invoice_id.action_post()
            invoice_id.action_create_commission_entry()

            for obj in ygg_so:
                lines = (obj.payment_id.line_ids + obj.sale_id.invoice_ids.line_ids).filtered(
                    lambda line: line.account_id == obj.payment_id.destination_account_id and 'Bank Charges' not in line.name and not line.reconciled
                )
                lines.reconcile()
                obj.status = 'invoice'

    def view_payment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment',
            'view_mode': 'form',
            'res_id': self.payment_id.id,
            'res_model': 'account.payment',
            'context': "{'create': False}"
        }

    def view_sale(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'view_mode': 'form',
            'res_id': self.sale_id.id,
            'res_model': 'sale.order',
            'context': "{'create': False}"
        }

    # @api.model
    # def create(self, vals):
    #     vals['name'] = self.env['ir.sequence'].next_by_code('ygg.orders.order') or _('New')
    #     vals['service_fee'] = 10
    #     if vals['customer_id']:
    #         sale_obj = self.env['sale.order'].create({'partner_id': vals['customer_id'],
    #                                                   'order_line': [(0, 0, {
    #                                                         'product_id': vals.get('product_id'),
    #                                                         'product_uom_qty': 1,
    #                                                         'price_unit': vals.get('amount'),
    #                                                         'tax_id': False,
    #                                                     })],})
    #         vals['sale_id'] = sale_obj.id
    #     res = super(YggOrdersOrder, self).create(vals)
    #     for obj in res:
    #         obj.sale_id.ygg_sale_order_id = obj.id
    #         obj.sale_id.action_confirm()
    #         invoice_lines = []
    #         for line in obj.sale_id.order_line:
    #             vals = {
    #                 'name': line.name,
    #                 'price_unit': line.price_unit,
    #                 'quantity': line.product_uom_qty,
    #                 'product_id': line.product_id.id,
    #                 'product_uom_id': line.product_uom.id,
    #                 'tax_ids': [(6, 0, line.tax_id.ids)],
    #                 'sale_line_ids': [(6, 0, [line.id])],
    #             }
    #             invoice_lines.append((0, 0, vals))
    #         invoice_id = self.env['account.move'].create({
    #             'move_type': 'out_invoice',
    #             'invoice_origin': obj.sale_id.name,
    #             'invoice_user_id': obj.sale_id.user_id.id,
    #             'partner_id': obj.sale_id.partner_invoice_id.id,
    #             'currency_id': obj.sale_id.pricelist_id.currency_id.id,
    #             'invoice_line_ids': invoice_lines
    #         })
    #         invoice_id.action_post()
    #         # obj.sale_id.corporate_category = obj.customer_id.corporate_categ_id.id
    #         journal = self.env['account.journal'].browse(int(
    #             self.env['ir.config_parameter'].sudo().get_param('sale_payment_journal_id')))
    #         if not obj.payment_id and obj.status == 'completed':
    #             payment_vals = {
    #                 'date': fields.Date.today(),
    #                 'amount': obj.amount,
    #                 'vz_bank_charge': obj.service_fee,
    #                 'payment_type': 'inbound',
    #                 'partner_type': 'customer',
    #                 'journal_id': journal.id,
    #                 'enable_charge': True,
    #                 'partner_id': obj.customer_id.id,
    #                 'payment_method_id': self.env.ref(
    #                     'account.account_payment_method_manual_in').id,
    #             }
    #             payment_id = self.env['account.payment'].create(payment_vals)
    #             obj.payment_id = payment_id.id
    #             payment_id.action_post()
    #             lines = (payment_id.line_ids + obj.sale_id.invoice_ids.line_ids).filtered(
    #                 lambda line: line.account_id == payment_id.destination_account_id and not line.reconciled
    #             )
    #             lines.reconcile()
    #     return res

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('ygg.orders.order') or _('New')
        # vals['service_fee'] = 10
        print("vals", vals)
        if vals['customer_id']:
            lines = []
            for l in vals['order_lines']:
                print("+++", l[2])
                lines.append((0,0, {'product_id': l[2]['product_id'],
                                                    'product_uom_qty': l[2]['product_qty'],
                                                    'tax_id': False,
                                                    'price_unit': l[2]['price_unit'],}))
            sale_obj = self.env['sale.order'].create({'partner_id': vals['customer_id'],
                                                      'order_line': lines,})
            vals['sale_id'] = sale_obj.id
        res = super(YggOrdersOrder, self).create(vals)
        for obj in res:
            obj.sale_id.ygg_sale_order_id = obj.id
            obj.sale_id.action_confirm()
            for line in obj.sale_id.picking_ids.mapped('move_ids_without_package'):
                line.quantity_done = line.product_uom_qty
            obj.sale_id.picking_ids.with_context(skip_backorder=True, skip_immediate=True).button_validate()
            print("obj.sale_id.picking_ids-------------", obj.sale_id.picking_ids)
            # invoice_lines = []
            # for line in obj.sale_id.order_line:
            #     vals = {
            #         'name': line.name,
            #         'price_unit': line.price_unit,
            #         'quantity': line.product_uom_qty,
            #         'product_id': line.product_id.id,
            #         'product_uom_id': line.product_uom.id,
            #         'tax_ids': [(6, 0, line.tax_id.ids)],
            #         'sale_line_ids': [(6, 0, [line.id])],
            #     }
            #     invoice_lines.append((0, 0, vals))
            # invoice_id = self.env['account.move'].create({
            #     'move_type': 'out_invoice',
            #     'invoice_origin': obj.sale_id.name,
            #     'invoice_user_id': obj.sale_id.user_id.id,
            #     'partner_id': obj.sale_id.partner_invoice_id.id,
            #     'currency_id': obj.sale_id.pricelist_id.currency_id.id,
            #     'invoice_line_ids': invoice_lines
            # })
            # invoice_id.action_post()
            # obj.sale_id.corporate_category = obj.customer_id.corporate_categ_id.id
            journal = self.env['account.journal'].browse(int(
                self.env['ir.config_parameter'].sudo().get_param('sale_payment_journal_id')))
            obj.status = 'completed'
            obj.payment_id = False
            # if not obj.payment_id and obj.status == 'completed' and obj.product_id.inventory_category:
            if not obj.payment_id and obj.status == 'completed':
                payment_vals = {
                    'date': fields.Date.today(),
                    'amount': obj.amount,
                    'vz_bank_charge': obj.service_fee,
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'journal_id': journal.id,
                    'enable_charge': True,
                    'partner_id': obj.customer_id.id,
                    'payment_method_id': self.env.ref(
                        'account.account_payment_method_manual_in').id,
                }
                payment_id = self.env['account.payment'].create(payment_vals)
                obj.payment_id = payment_id.id
                payment_id.action_post()
                # lines = (payment_id.line_ids + obj.sale_id.invoice_ids.line_ids).filtered(
                #     lambda line: line.account_id == payment_id.destination_account_id and not line.reconciled
                # )
                # lines.reconcile()


        return res

    def write(self, vals):
        result = super(YggOrdersOrder, self).write(vals)
        for obj in self:
            # if not obj.payment_id and obj.status == 'completed' and obj.product_id.inventory_category:
            if not obj.payment_id and obj.status == 'completed':
                journal = self.env['account.journal'].browse(int(
                    self.env['ir.config_parameter'].sudo().get_param('sale_payment_journal_id')))
                payment_vals = {
                    'date': fields.Date.today(),
                    'amount': obj.sale_id.amount_total,
                    'vz_bank_charge': obj.service_fee,
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'journal_id': journal.id,
                    'enable_charge': True,
                    'partner_id': obj.customer_id.id,
                    'payment_method_id': self.env.ref(
                        'account.account_payment_method_manual_in').id,
                }
                payment_id = self.env['account.payment'].create(payment_vals)
                obj.payment_id = payment_id.id
                payment_id.action_post()
                (payment_id.line_ids + obj.sale_id.invoice_ids.line_ids).filtered(
                    lambda line: line.account_id == payment_id.destination_account_id and not line.reconciled
                ).reconcile()
            elif obj.status == 'canceled' and obj.payment_id and obj.sale_id:
                obj.payment_id.action_draft()
                obj.payment_id.action_cancel()

        return result


class OrdersOrderLine(models.Model):
    _name = 'orders.order.line'

    order_id = fields.Many2one('ygg.orders.order')
    product_id = fields.Many2one('product.product', string="Product")
    product_qty = fields.Float("Quantity")
    price_unit = fields.Float("Price Unit")
    sub_total = fields.Float("Sub Total")

    @api.onchange('product_qty', 'price_unit')
    def _onchange_sub_total(self):
        self.sub_total = self.product_qty * self.price_unit


