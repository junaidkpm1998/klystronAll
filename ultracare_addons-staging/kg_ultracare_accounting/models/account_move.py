# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import json

from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def get_default_purchase_order(self):
        purchase_id = self.env['purchase.order'].search([])
        if purchase_id:
            list = []
            for i in purchase_id:
                list.append(i.id)
            return list

    purchase_order_ids = fields.Many2many('purchase.order', default=get_default_purchase_order, string='Purchase Order',
                                          store=True)
    purchase_vendor_bill_id = fields.Many2one('purchase.bill.union',
                                              states={'draft': [('readonly', False)]},
                                              string='Auto-complete',
                                              domain="[('purchase_order_id', 'in', purchase_order_ids),('partner_id','=',partner_id)]",
                                              help="Auto-complete from a past bill / purchase order.")

    @api.onchange('purchase_vendor_bill_id', 'purchase_id')
    def _onchange_purchase_auto_complete(self):
        if self.purchase_vendor_bill_id:
            self.invoice_line_ids = False
            return super(AccountMove, self)._onchange_purchase_auto_complete()

    @api.constrains('ref')
    def constraints_ref(self):
        if not self.ref and self.move_type == 'in_invoice':
            raise UserError('Please Add Bill Reference and Continue!')

    # def action_post(self):
    #     res = super(AccountMove, self).action_post()
    #     self.reversed_entry_id.amount_residual = self.reversed_entry_id.amount_residual - self.amount_residual
    #     return res
    #
    # def button_draft(self):
    #     res = super(AccountMove, self).button_draft()
    #     self.reversed_entry_id.amount_residual = self.reversed_entry_id.amount_residual + self.amount_residual
    #     return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_reconciled = fields.Boolean('Reconciled')
    analytic_distribution_amount = fields.Json(string="Analytic Amount")

    @api.onchange('analytic_distribution', 'price_subtotal')
    def _onchange_analytic_amount(self):
        vals = []
        analytic_key = []
        for rec in self:
            if rec.analytic_distribution:
                for i in rec.analytic_distribution.values():
                    value_amount = (float(i) * rec.price_subtotal) / 100
                    vals.append(value_amount)
                for j in rec.analytic_distribution:
                    analytic_key.append(j)

            vals_dict = zip(analytic_key, vals)
            rec.analytic_distribution_amount = dict(vals_dict)
