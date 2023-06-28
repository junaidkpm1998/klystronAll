# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    preset_code_acc_id = fields.Many2one('account.account', string='Preset Code Account')
    partner_acc_id = fields.Many2one('account.account', string='Partner Account')
    clearing_acc_id = fields.Many2one('account.account', string='Clearing Commission')

#     advance_payment_line = fields.One2many('adv.payment.line', 'partner_id')
#
#
# class AdvancePaymentLine(models.Model):
#     _name = 'adv.payment.line'
#
#     product_id = fields.Many2one('product.product', string="Product")
#     partner_id = fields.Many2one('res.partner', string="Vendor")
#     amount = fields.Monetary(string="Amount")
#     currency_id = fields.Many2one('res.currency')
#     balance = fields.Float(compute="_compute_balance_amount")
#
#     def _compute_balance_amount(self):
#         for rec in self:
#             rec.balance = rec.amount

