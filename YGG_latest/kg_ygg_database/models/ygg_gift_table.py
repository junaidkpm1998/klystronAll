from odoo import api, fields, models, _
import pymssql
import xmlrpc.client
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class YggGiftTable(models.Model):
    _name = 'ygg.gift.table'
    _rec_name = 'ygag_gift_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YGG Gift Table'

    ygg_gift_id = fields.Char("Gift ID")
    ygag_gift_id = fields.Many2one('ygg.gifting.gift', string="Gift ID")
    # ygg_gift_id = fields.Many2one('ygg.gifting.gift')
    ygg_record_id = fields.Integer("YGG Record ID")
    created_on = fields.Datetime("Created On")
    modified_on = fields.Datetime("Modified On")
    db_name = fields.Char("Database name")
    date_invoiced = fields.Datetime("Invoice date")
    corporate_id = fields.Many2one('res.partner', string="Corporate")
    state = fields.Char("State")
    reference_id = fields.Char("Reference")
    base_currency_id = fields.Integer("Base Currency")
    amount_in_base_currency = fields.Float("Amount in Base Currency")
    brand_id = fields.Many2one(related="ygag_gift_id.brand_id")
    payment_ids = fields.Many2many('ygg.payment.table',)


class RewardsCorporateGift(models.Model):
    _name = 'rewards.corporate.gift'
    _rec_name = 'reference_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YGG Rewards Corporate Gift'

    ygg_record_id = fields.Integer("YGG Record ID")
    created_on = fields.Datetime("Created On")
    modified_on = fields.Datetime("Modified On")
    db_name = fields.Char("Database Name")
    amount_in_aed = fields.Float("Amount")
    reference_id = fields.Char("Reference")
    brand_id = fields.Many2one("product.product", 'Brand')
    corporate_id = fields.Many2one("res.partner", 'Corporate')
    invoice_id = fields.Many2one("account.move", 'Invoice')

    def action_create_invoice(self):
        for gift in self.browse(self.env.context['active_ids']):
            invoice = self.env['account.move'].create({
                'partner_id': gift.corporate_id.id,
                'move_type': 'out_invoice',
                'l10n_in_gst_treatment': 'regular',
                'invoice_line_ids': [
                    (0, 0, {
                        'product_id': gift.brand_id.id,
                        'quantity': 1,
                        'tax_ids': False,
                        'price_unit': gift.amount_in_aed,

                    })
                ],
            })
            # if not gift.invoice_id:
            gift.invoice_id = invoice.id
            gift.invoice_id.action_post()
            print("gift.reference_id", gift.reference_id)
            topup = self.env['ygg.topup'].search([('reference_id', '=', gift.reference_id)])
            print("topup", topup)

            debit_move_dict = {}
            credit_move_dict = {}
            for line in gift.invoice_id:
                debit_move_dict[line.move_line_id.id] = line.inv_allocate_amount
            for line in topup.payment_id:
                credit_move_dict[line.move_line_id.id] = gift.amount_in_aed

            matching_list = topup.payment_id.get_matching_dict(debit_move_dict, credit_move_dict)

            for rec_val in matching_list:
                rec = self.env['account.partial.reconcile'].create(rec_val)

    def view_invoice(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'view_mode': 'form',
            'res_id': self.invoice_id.id,
            'res_model': 'account.move',
            'context': "{'create': False}"
        }


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_topup = fields.Boolean("Is Topup")

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        res = super()._prepare_move_line_default_vals(write_off_line_vals = write_off_line_vals)
        if self.is_topup:
            if self.partner_id.topup_account_id:
                topup_account_id = self.partner_id.topup_account_id
            else:
                topup_account_id = self.env['ir.config_parameter'].sudo().get_param('topup_account_id')
            charge_list = []
            for d in res:
                if d['account_id'] == self.outstanding_account_id.id:
                    # d['amount_currency'] = d['amount_currency'] - sign * liquidity_amount_currency
                    d['account_id'] = topup_account_id

            # charge_list.extend(credit)
            charge_list.extend(res)
            res = charge_list

        return res

    def get_matching_dict(self, debit_move_dict, credit_move_dict):
        matching_list = []
        debit_dict = {}
        credit_dict = {}
        payment_type = self.payment_type
        if payment_type == 'receive_money':
            debit_dict = debit_move_dict
            credit_dict = credit_move_dict
        elif payment_type == 'send_money':
            debit_dict = credit_move_dict
            credit_dict = debit_move_dict
        print(type(payment_type), "Typeeesssss")
        print(credit_dict, "Typeeesssss")
        if payment_type == 'receive_money':
            for cred_move_id, credamt, in credit_dict.items():
                print(credamt, "Cre")
                if credamt > 0.0:
                    for deb_move_id, debamt in debit_dict.items():
                        is_full_reconcile = debit_dict['is_full_reconcile']
                        print(is_full_reconcile, "LLLL")
                        print(debamt, "DEB AMTTT")
                        print(credamt, "CRED AMTTT")
                        balance = credamt - debamt
                        print(balance, "Balanceeee")
                        if credamt <= 0.0:
                            continue
                        if debamt == 0.0:
                            continue
                        if balance > 0.0:
                            ful_rec = self.env['account.full.reconcile']
                            if is_full_reconcile == True:
                                vals = {}
                                ful_rec = self.env['account.full.reconcile'].create(vals)
                                if deb_move_id != 'is_full_reconcile':
                                    matching_list.append(
                                        {'credit_move_id': cred_move_id, 'full_reconcile_id': ful_rec.id,
                                         'debit_amount_currency': debamt, 'credit_amount_currency': debamt,
                                         'debit_move_id': deb_move_id, 'amount': debamt})
                                    debit_dict[deb_move_id] = 0.0
                        if balance < 0.0:
                            ful_rec = self.env['account.full.reconcile']
                            if is_full_reconcile == True:
                                vals = {}
                                ful_rec = self.env['account.full.reconcile'].create(vals)
                            if deb_move_id != 'is_full_reconcile':
                                matching_list.append(
                                    {'credit_move_id': cred_move_id, 'full_reconcile_id': ful_rec.id,
                                     'debit_amount_currency': credamt, 'credit_amount_currency': credamt,
                                     'debit_move_id': deb_move_id, 'amount': credamt})
                            debit_dict[deb_move_id] = abs(balance)
                            credit_dict[cred_move_id] = 0.0
                        if balance == 0.0:
                            ful_rec = self.env['account.full.reconcile']
                            if is_full_reconcile == True:
                                vals = {}
                                ful_rec = self.env['account.full.reconcile'].create(vals)
                            if deb_move_id != 'is_full_reconcile':
                                matching_list.append(
                                {'credit_move_id': cred_move_id, 'full_reconcile_id': ful_rec.id,
                                 'debit_move_id': deb_move_id, 'debit_amount_currency': debamt,
                                 'credit_amount_currency': debamt, 'amount': debamt})
                            debit_dict[deb_move_id] = 0.0
                            credit_dict[cred_move_id] = 0.0
                            credamt = 0.0
                        credamt = balance
        return matching_list

