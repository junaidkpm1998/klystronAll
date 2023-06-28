# -*- coding: utf-8 -*-
from docutils.nodes import date

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    adv_payment_id = fields.Many2one('ygg.advance.payment', copy=False)
    # entry_line_ids = fields.One2many(
    #     'account.move.line',
    #     'move_id',
    #     string='Journal Items',
    #     copy=True,
    #     readonly=True,
    #     states={'draft': [('readonly', False)]},
    # )

    def action_create_entry(self):
        if self.invoice_line_ids[0].product_id.inventory_category == 'issuance_prepaid':
            # commission = self.amount_untaxed_signed * self.invoice_line_ids[0].product_id.unrealised_commission_per
            commission = self.amount_untaxed_signed * self.invoice_line_ids[0].product_id.seller_ids[0].commission_per
            sign = -1 if self.move_type == 'out_refund' else 1


            vals = [
                (0, 0, {
                    'name': self.invoice_line_ids[0].product_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': self.env['ir.config_parameter'].sudo().get_param('commission_revenue_acc_id'),
                    'product_id': self.invoice_line_ids[0].product_id.id,
                    'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                    'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                    'price_unit': commission,
                    'amount_currency': -sign * commission,
                    'display_type': 'cogs',
                    'tax_ids': [],
                }),
                 (0, 0, {
                    'name': self.invoice_line_ids[0].product_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': self.env['ir.config_parameter'].sudo().get_param('unrealised_acc_id'),
                    'product_id': self.invoice_line_ids[0].product_id.id,
                    'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                     'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                     'price_unit': -commission,
                     'amount_currency': sign * commission,
                     'display_type': 'cogs',
                     'tax_ids': [],
                }),]

            print("vals", vals)

            move = self.env['account.move'].create({
                'ref': self.name,
                'move_type': 'entry',
                'journal_id': self.journal_id.id,
                'date': fields.Date.today(),
                'line_ids': vals,
            })
            move.action_post()

            print("move",move)

            # self.entry_ids |= move.id
            self.write({
            'state': 'posted',
            'posted_before': True,
            })



    def action_confirm(self):
        if self.invoice_line_ids[0].product_id.inventory_category == 'issuance_prepaid':
            commission = self.amount_untaxed_signed * self.invoice_line_ids[0].product_id.seller_ids[0].commission_per
            sign = -1 if self.move_type == 'out_refund' else 1
            print("1", self.invoice_line_ids[0].product_id.categ_id.property_stock_valuation_account_id.id)
            print("2", self.env['ir.config_parameter'].sudo().get_param('receivable_clearing_acc_id'))
            print("4", self.invoice_line_ids[0].product_id.categ_id.property_account_expense_categ_id.id)

            vals = [
                # (0, 0, {
                #     'name': self.invoice_line_ids[0].product_id.name,
                #     'partner_id': self.partner_id.id,
                #     'account_id': self.invoice_line_ids[0].product_id.categ_id.property_stock_valuation_account_id.id,
                #     # 'account_id': self.partner_id.preset_code_acc_id.id,
                #     'product_id': self.invoice_line_ids[0].product_id.id,
                #     'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                #     'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                #     'price_unit': self.amount_untaxed_signed,
                #     'amount_currency': -sign * self.amount_untaxed_signed,
                #     'display_type': 'cogs',
                #     'tax_ids': [],
                # }),
                # (0, 0, {
                #     'name': self.invoice_line_ids[0].product_id.name,
                #     'partner_id': self.partner_id.id,
                #     'account_id': self.env['ir.config_parameter'].sudo().get_param('receivable_clearing_acc_id'),
                #     'product_id': self.invoice_line_ids[0].product_id.id,
                #     'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                #     'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                #     'price_unit': -self.amount_untaxed_signed,
                #     'amount_currency': sign * self.amount_untaxed_signed,
                #     'display_type': 'cogs',
                #     'tax_ids': [],
                # }),

                # (0, 0, {
                #     'name': self.invoice_line_ids[0].product_id.name,
                #     'partner_id': self.partner_id.id,
                #     'account_id': self.env['ir.config_parameter'].sudo().get_param('receivable_clearing_acc_id'),
                #     'product_id': self.invoice_line_ids[0].product_id.id,
                #     'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                #     'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                #     'price_unit': self.amount_untaxed_signed,
                #     'amount_currency': -sign * self.amount_untaxed_signed,
                #     'display_type': 'cogs',
                #     'tax_ids': [],
                # }),
                # (0, 0, {
                #     'name': self.invoice_line_ids[0].product_id.name,
                #     'partner_id': self.partner_id.id,
                #     'account_id': self.invoice_line_ids[0].product_id.categ_id.property_account_expense_categ_id.id,
                #     'product_id': self.invoice_line_ids[0].product_id.id,
                #     'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                #     'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                #     'price_unit': -self.amount_untaxed_signed,
                #     'amount_currency': sign * self.amount_untaxed_signed,
                #     'display_type': 'cogs',
                #     'tax_ids': [],
                # }),
                (0, 0, {
                    'name': self.invoice_line_ids[0].product_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': self.env['ir.config_parameter'].sudo().get_param('commission_revenue_acc_id'),
                    'product_id': self.invoice_line_ids[0].product_id.id,
                    'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                    'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                    'price_unit': commission,
                    'amount_currency': -sign * commission,
                    'display_type': 'cogs',
                    'tax_ids': [],
                }),
                 (0, 0, {
                    'name': self.invoice_line_ids[0].product_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': self.env['ir.config_parameter'].sudo().get_param('unrealised_acc_id'),
                    'product_id': self.invoice_line_ids[0].product_id.id,
                    'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                     'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                     'price_unit': -commission,
                     'amount_currency': sign * commission,
                     'display_type': 'cogs',
                     'tax_ids': [],
                }),]

            print("vals", vals)

            self.line_ids = vals
            self.write({
            'state': 'posted',
            'posted_before': True,
            })
        elif self.invoice_line_ids[0].product_id.inventory_category == 'issuance_postpaid':
            commission = self.amount_untaxed_signed * self.invoice_line_ids[0].product_id.unrealised_commission_per
            sign = -1 if self.move_type == 'out_refund' else 1
            std_price = sum(self.invoice_line_ids.mapped('quantity')) * self.invoice_line_ids[0].product_id.standard_price
            std_commission = std_price * self.invoice_line_ids[0].product_id.unrealised_commission_per
            self.line_ids = [
                (0, 0, {
                    'name': self.invoice_line_ids[0].product_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': self.invoice_line_ids[0].product_id.categ_id.property_stock_valuation_account_id.id,
                    # 'account_id': self.partner_id.preset_code_acc_id.id,
                    'product_id': self.invoice_line_ids[0].product_id.id,
                    'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                    'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                    'price_unit': -std_price,
                    'amount_currency': sign * std_price,
                    'display_type': 'cogs',
                    'tax_ids': [],
                }),
                (0, 0, {
                    'name': self.invoice_line_ids[0].product_id.name,
                    'partner_id': self.partner_id.id,
                    'date_maturity': fields.Date.today(),
                    'account_id': self.partner_id.partner_acc_id.id,
                    'product_id': self.invoice_line_ids[0].product_id.id,
                    'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                    'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                    'price_unit': std_price - std_commission,
                    'amount_currency': -sign * (std_price - std_commission),
                    'display_type': 'cogs',
                    'tax_ids': [],
                }),
                (0, 0, {
                    'name': self.invoice_line_ids[0].product_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': self.env['ir.config_parameter'].sudo().get_param('unrealised_acc_id'),
                    'product_id': self.invoice_line_ids[0].product_id.id,
                    'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                    'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                    'price_unit': std_commission,
                    'amount_currency': -sign * std_commission,
                    'display_type': 'cogs',
                    'tax_ids': [],
                }),
                (0, 0, {
                    'name': self.invoice_line_ids[0].product_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': self.invoice_line_ids[0].product_id.categ_id.property_stock_valuation_account_id.id,
                    # 'account_id': self.partner_id.preset_code_acc_id.id,
                    'product_id': self.invoice_line_ids[0].product_id.id,
                    'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                    'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                    'price_unit': self.amount_untaxed_signed,
                    'amount_currency': -sign * self.amount_untaxed_signed,
                    'display_type': 'cogs',
                    'tax_ids': [],
                }),
                (0, 0, {
                    'name': self.invoice_line_ids[0].product_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': self.env['ir.config_parameter'].sudo().get_param('receivable_clearing_acc_id'),
                    'product_id': self.invoice_line_ids[0].product_id.id,
                    'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                    'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                    'price_unit': -self.amount_untaxed_signed,
                    'amount_currency': sign * self.amount_untaxed_signed,
                    'display_type': 'cogs',
                    'tax_ids': [],
                }),

                (0, 0, {
                    'name': self.invoice_line_ids[0].product_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': self.env['ir.config_parameter'].sudo().get_param('receivable_clearing_acc_id'),
                    'product_id': self.invoice_line_ids[0].product_id.id,
                    'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                    'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                    'price_unit': self.amount_untaxed_signed,
                    'amount_currency': -sign * self.amount_untaxed_signed,
                    'display_type': 'cogs',
                    'tax_ids': [],
                }),
                (0, 0, {
                    'name': self.invoice_line_ids[0].product_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': self.invoice_line_ids[0].product_id.categ_id.property_account_expense_categ_id.id,
                    'product_id': self.invoice_line_ids[0].product_id.id,
                    'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                    'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                    'price_unit': -self.amount_untaxed_signed,
                    'amount_currency': sign * self.amount_untaxed_signed,
                    'display_type': 'cogs',
                    'tax_ids': [],
                }),
                (0, 0, {
                    'name': self.invoice_line_ids[0].product_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': self.env['ir.config_parameter'].sudo().get_param('commission_revenue_acc_id'),
                    'product_id': self.invoice_line_ids[0].product_id.id,
                    'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                    'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                    'price_unit': commission,
                    'amount_currency': -sign * commission,
                    'display_type': 'cogs',
                    'tax_ids': [],
                }),
                 (0, 0, {
                    'name': self.invoice_line_ids[0].product_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': self.env['ir.config_parameter'].sudo().get_param('unrealised_acc_id'),
                    'product_id': self.invoice_line_ids[0].product_id.id,
                    'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                     'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                     'price_unit': -commission,
                     'amount_currency': sign * commission,
                     'display_type': 'cogs',
                     'tax_ids': [],
                }),]
            self.write({
            'state': 'posted',
            'posted_before': True,
        })
        elif self.invoice_line_ids[0].product_id.inventory_category in ['redemption', 'sold']:
            commission = self.amount_untaxed_signed * self.invoice_line_ids[0].product_id.unrealised_commission_per
            sign = -1 if self.move_type == 'out_refund' else 1
            self.line_ids = [
                (0, 0, {
                    'name': self.invoice_line_ids[0].product_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': self.invoice_line_ids[0].product_id.categ_id.property_stock_valuation_account_id.id,
                    # 'account_id': self.partner_id.preset_code_acc_id.id,
                    'product_id': self.invoice_line_ids[0].product_id.id,
                    'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                    'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                    'price_unit': -self.invoice_line_ids[0].product_id.standard_price,
                    'amount_currency': sign * self.invoice_line_ids[0].product_id.standard_price,
                    'display_type': 'cogs',
                    'tax_ids': [],
                }),
                (0, 0, {
                    'name': self.invoice_line_ids[0].product_id.name,
                    'partner_id': self.partner_id.id,
                    'date_maturity': fields.Date.today(),
                    'account_id': self.partner_id.partner_acc_id.id,
                    'product_id': self.invoice_line_ids[0].product_id.id,
                    'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                    'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                    'price_unit': self.invoice_line_ids[0].product_id.standard_price,
                    'amount_currency': -sign * self.invoice_line_ids[0].product_id.standard_price,
                    'display_type': 'cogs',
                    'tax_ids': [],
                }),
                (0, 0, {
                    'name': self.invoice_line_ids[0].product_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': self.invoice_line_ids[0].product_id.categ_id.property_stock_valuation_account_id.id,
                    # 'account_id': self.partner_id.preset_code_acc_id.id,
                    'product_id': self.invoice_line_ids[0].product_id.id,
                    'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                    'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                    'price_unit': self.amount_untaxed_signed,
                    'amount_currency': -sign * self.amount_untaxed_signed,
                    'display_type': 'cogs',
                    'tax_ids': [],
                }),
                (0, 0, {
                    'name': self.invoice_line_ids[0].product_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': self.env['ir.config_parameter'].sudo().get_param('receivable_clearing_acc_id'),
                    'product_id': self.invoice_line_ids[0].product_id.id,
                    'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                    'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                    'price_unit': -self.amount_untaxed_signed,
                    'amount_currency': sign * self.amount_untaxed_signed,
                    'display_type': 'cogs',
                    'tax_ids': [],
                }),

                (0, 0, {
                    'name': self.invoice_line_ids[0].product_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': self.env['ir.config_parameter'].sudo().get_param('receivable_clearing_acc_id'),
                    'product_id': self.invoice_line_ids[0].product_id.id,
                    'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                    'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                    'price_unit': self.amount_untaxed_signed,
                    'amount_currency': -sign * self.amount_untaxed_signed,
                    'display_type': 'cogs',
                    'tax_ids': [],
                }),
                (0, 0, {
                    'name': self.invoice_line_ids[0].product_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': self.invoice_line_ids[0].product_id.categ_id.property_account_expense_categ_id.id,
                    'product_id': self.invoice_line_ids[0].product_id.id,
                    'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                    'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                    'price_unit': -self.amount_untaxed_signed,
                    'amount_currency': sign * self.amount_untaxed_signed,
                    'display_type': 'cogs',
                    'tax_ids': [],
                }),
                (0, 0, {
                    'name': self.invoice_line_ids[0].product_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': self.env['ir.config_parameter'].sudo().get_param('commission_revenue_acc_id'),
                    'product_id': self.invoice_line_ids[0].product_id.id,
                    'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                    'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                    'price_unit': commission,
                    'amount_currency': -sign * commission,
                    'display_type': 'cogs',
                    'tax_ids': [],
                }),
                 (0, 0, {
                    'name': self.invoice_line_ids[0].product_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': self.partner_id.clearing_acc_id.id,
                    'product_id': self.invoice_line_ids[0].product_id.id,
                    'product_uom_id': self.invoice_line_ids[0].product_uom_id.id,
                     'quantity': sum(self.invoice_line_ids.mapped('quantity')),
                     'price_unit': -commission,
                     'amount_currency': sign * commission,
                     'display_type': 'cogs',
                     'tax_ids': [],
                }),]
            self.write({
            'state': 'posted',
            'posted_before': True,
        })