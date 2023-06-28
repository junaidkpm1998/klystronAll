from odoo import api, fields, models, _
import pymssql
import xmlrpc.client
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class AccountMove(models.Model):
    _inherit = 'account.move'

    ygg_topup_id = fields.Many2one('ygg.topup')

    def action_create_commission_entry(self):
        sales = list(set(self.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')))

        for sale in sales:
            ygg_order = self.env['ygg.orders.order'].search([('sale_id', '=', sale.id)])
            vals = []
            for line in ygg_order.order_lines:
                if line.product_id.seller_ids:
                    commission = line.sub_total * line.product_id.seller_ids[0].commission_per/100
                    sign = -1 if self.move_type == 'out_refund' else 1

                    vals.append((0, 0, {
                            'name': line.product_id.name,
                            'partner_id': line.product_id.seller_ids[0].partner_id.id,
                            'account_id': self.env['ir.config_parameter'].sudo().get_param('commission_revenue_acc_id'),
                            'product_id': line.product_id.id,
                            'product_uom_id': line.product_id.uom_id.id,
                            'quantity': line.product_qty,
                            'price_unit': commission,
                            'amount_currency': -sign * commission,
                            'display_type': 'cogs',
                        }))
                    vals.append((0, 0, {
                            'name': line.product_id.name,
                            'partner_id': line.product_id.seller_ids[0].partner_id.id,
                            'account_id': self.env['ir.config_parameter'].sudo().get_param('unrealised_acc_id'),
                            'product_id': line.product_id.id,
                            'product_uom_id': line.product_id.uom_id.id,
                             'quantity': line.product_qty,
                             'price_unit': -commission,
                             'amount_currency': sign * commission,
                             'display_type': 'cogs',
                        }))

            print("=====", vals)

            move = self.env['account.move'].create({
                'ref': self.name,
                'move_type': 'entry',
                'journal_id': self.journal_id.id,
                'date': fields.Date.today(),
                'line_ids': vals,
            })
            move.action_post()
            if ygg_order:
                ygg_order.commission_entry_id = move.id

            print("move",move)

            # self.entry_ids |= move.id
        self.write({
        'state': 'posted',
        'posted_before': True,
        })


    # def action_create_commission_entry(self):
    #     for line in self.invoice_line_ids:
    #         ygg_order = self.env['ygg.orders.order'].search([('sale_id', '=', line.sale_line_ids[0].order_id.id)])
    #         if line[0].product_id.inventory_category == 'issuance_prepaid':
    #             commission = line[0].sale_line_ids[0].order_id.amount_total * line[0].product_id.seller_ids[0].commission_per
    #             sign = -1 if self.move_type == 'out_refund' else 1
    #
    #             vals = [
    #                 (0, 0, {
    #                     'name': line.product_id.name,
    #                     'partner_id': line.product_id.seller_ids[0].partner_id.id,
    #                     'account_id': self.env['ir.config_parameter'].sudo().get_param('commission_revenue_acc_id'),
    #                     'product_id': line.product_id.id,
    #                     'product_uom_id': line.product_uom_id.id,
    #                     'quantity': sum(self.invoice_line_ids.mapped('quantity')),
    #                     'price_unit': commission,
    #                     'amount_currency': -sign * commission,
    #                     'display_type': 'cogs',
    #                 }),
    #                  (0, 0, {
    #                     'name': line.product_id.name,
    #                     'partner_id': line.product_id.seller_ids[0].partner_id.id,
    #                     'account_id': self.env['ir.config_parameter'].sudo().get_param('unrealised_acc_id'),
    #                     'product_id': line.product_id.id,
    #                     'product_uom_id': line.product_uom_id.id,
    #                      'quantity': sum(self.invoice_line_ids.mapped('quantity')),
    #                      'price_unit': -commission,
    #                      'amount_currency': sign * commission,
    #                      'display_type': 'cogs',
    #                 }),]
    #
    #             print("vals", vals)
    #
    #             move = self.env['account.move'].create({
    #                 'ref': self.name,
    #                 'move_type': 'entry',
    #                 'journal_id': self.journal_id.id,
    #                 'date': fields.Date.today(),
    #                 'line_ids': vals,
    #             })
    #             move.action_post()
    #             if ygg_order:
    #                 ygg_order.commission_entry_id = move.id
    #
    #             print("move",move)
    #
    #             # self.entry_ids |= move.id
    #             self.write({
    #             'state': 'posted',
    #             'posted_before': True,
    #             })
    #         elif line[0].product_id.inventory_category == 'issuance_postpaid':
    #             commission = line.sale_line_ids[0].order_id.amount_total * line.product_id.seller_ids[0].commission_per
    #             sign = -1 if self.move_type == 'out_refund' else 1
    #
    #
    #             vals = [
    #                 (0, 0, {
    #                     'name': line.product_id.name,
    #                     'partner_id': line.product_id.seller_ids[0].partner_id.id,
    #                     'account_id': self.env['ir.config_parameter'].sudo().get_param('commission_revenue_acc_id'),
    #                     'product_id': line.product_id.id,
    #                     'product_uom_id': line.product_uom_id.id,
    #                     'quantity': sum(self.invoice_line_ids.mapped('quantity')),
    #                     'price_unit': commission,
    #                     'amount_currency': -sign * commission,
    #                     'display_type': 'cogs',
    #                 }),
    #                  (0, 0, {
    #                     'name': line.product_id.name,
    #                     'partner_id': line.product_id.seller_ids[0].partner_id.id,
    #                     'account_id': self.env['ir.config_parameter'].sudo().get_param('unrealised_acc_id'),
    #                     'product_id': line.product_id.id,
    #                     'product_uom_id': line.product_uom_id.id,
    #                      'quantity': sum(self.invoice_line_ids.mapped('quantity')),
    #                      'price_unit': -commission,
    #                      'amount_currency': sign * commission,
    #                      'display_type': 'cogs',
    #                 }),]
    #
    #             print("vals", vals)
    #
    #             move = self.env['account.move'].create({
    #                 'ref': self.name,
    #                 'move_type': 'entry',
    #                 'journal_id': self.journal_id.id,
    #                 'date': fields.Date.today(),
    #                 'line_ids': vals,
    #             })
    #             move.action_post()
    #             if ygg_order:
    #                 ygg_order.commission_entry_id = move.id
    #
    #             print("move",move)
    #
    #             # self.entry_ids |= move.id
    #             self.write({
    #             'state': 'posted',
    #             'posted_before': True,
    #             })
    #         elif line[0].product_id.inventory_category == 'redemption':
    #             commission = line.sale_line_ids[0].order_id.amount_total * line.product_id.seller_ids[0].commission_per
    #             sign = -1 if self.move_type == 'out_refund' else 1
    #
    #
    #             vals = [
    #                 (0, 0, {
    #                     'name': line.product_id.name,
    #                     'partner_id': line.product_id.seller_ids[0].partner_id.id,
    #                     'account_id': self.env['ir.config_parameter'].sudo().get_param('commission_revenue_acc_id'),
    #                     'product_id': line.product_id.id,
    #                     'product_uom_id': line.product_uom_id.id,
    #                     'quantity': sum(self.invoice_line_ids.mapped('quantity')),
    #                     'price_unit': commission,
    #                     'amount_currency': -sign * commission,
    #                     'display_type': 'cogs',
    #                 }),
    #                  (0, 0, {
    #                     'name': line.product_id.name,
    #                     'partner_id': line.product_id.seller_ids[0].partner_id.id,
    #                     'account_id': self.partner_id.clearing_acc_id.id,
    #                     'product_id': line.product_id.id,
    #                     'product_uom_id': line.product_uom_id.id,
    #                      'quantity': sum(self.invoice_line_ids.mapped('quantity')),
    #                      'price_unit': -commission,
    #                      'amount_currency': sign * commission,
    #                      'display_type': 'cogs',
    #                 }),]
    #
    #             print("vals", vals)
    #
    #             move = self.env['account.move'].create({
    #                 'ref': self.name,
    #                 'move_type': 'entry',
    #                 'journal_id': self.journal_id.id,
    #                 'date': fields.Date.today(),
    #                 'line_ids': vals,
    #             })
    #             move.action_post()
    #             if ygg_order:
    #                 ygg_order.commission_entry_id = move.id
    #
    #             print("move",move)
    #
    #             # self.entry_ids |= move.id
    #             self.write({
    #             'state': 'posted',
    #             'posted_before': True,
    #             })
    #         elif line[0].product_id.inventory_category == 'sold':
    #             commission = line.sale_line_ids[0].order_id.amount_total * line.product_id.seller_ids[0].commission_per
    #             sign = -1 if self.move_type == 'out_refund' else 1
    #             vals = [
    #                 (0, 0, {
    #                     'name': line.product_id.name,
    #                     'partner_id': line.product_id.seller_ids[0].partner_id.id,
    #                     'account_id': self.env['ir.config_parameter'].sudo().get_param('commission_revenue_acc_id'),
    #                     'product_id': line.product_id.id,
    #                     'product_uom_id': line.product_uom_id.id,
    #                     'quantity': sum(self.invoice_line_ids.mapped('quantity')),
    #                     'price_unit': commission,
    #                     'amount_currency': -sign * commission,
    #                     'display_type': 'cogs',
    #                 }),
    #                  (0, 0, {
    #                     'name': line.product_id.name,
    #                     'partner_id': line.product_id.seller_ids[0].partner_id.id,
    #                     'account_id': self.partner_id.clearing_acc_id.id,
    #                     'product_id': line.product_id.id,
    #                     'product_uom_id': line.product_uom_id.id,
    #                      'quantity': sum(self.invoice_line_ids.mapped('quantity')),
    #                      'price_unit': -commission,
    #                      'amount_currency': sign * commission,
    #                      'display_type': 'cogs',
    #                 }),]
    #
    #             print("vals", vals)
    #
    #             move = self.env['account.move'].create({
    #                 'ref': self.name,
    #                 'move_type': 'entry',
    #                 'journal_id': self.journal_id.id,
    #                 'date': fields.Date.today(),
    #                 'line_ids': vals,
    #             })
    #             move.action_post()
    #             if ygg_order:
    #                 ygg_order.commission_entry_id = move.id
    #
    #             print("move",move)
    #
    #             # self.entry_ids |= move.id
    #             self.write({
    #             'state': 'posted',
    #             'posted_before': True,
    #             })