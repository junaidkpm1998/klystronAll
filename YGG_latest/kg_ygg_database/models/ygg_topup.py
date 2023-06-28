from odoo import api, fields, models, _
import pymssql
import xmlrpc.client
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class YggTopup(models.Model):
    _name = 'ygg.topup'
    _rec_name = 'corporate_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YGG Topup'

    ygg_record_id = fields.Integer("YGG Record ID")
    created_on = fields.Datetime("Created On")
    modified_on = fields.Datetime("Modified On")
    db_name = fields.Char("Database Name")
    amount = fields.Monetary('Amount')
    amount_payable = fields.Monetary('Amount Payable')
    service_fee = fields.Monetary('Service Fee')
    currency_id = fields.Many2one('res.currency', string='Currency')
    status = fields.Selection([('created', 'Created'), ('paid', 'Paid')], default='created')
    corporate_id = fields.Many2one('res.partner', string="Corporate")
    balance_amount = fields.Monetary('Balance Amount')
    invoice_number = fields.Integer('Invoice Number')
    current_balance = fields.Monetary('Current Balance')
    top_up_date = fields.Datetime('TopUp Date')
    order_id = fields.Integer('Order ID')
    reference_id = fields.Char('Reference ID')
    move_id = fields.Many2one('account.move', string='Journal Entry')
    payment_id = fields.Many2one('account.payment', string='Payment')

    def view_payment(self):
        self.ensure_one()
        if self.payment_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Payment',
                'view_mode': 'form',
                'res_id': self.payment_id.id,
                'res_model': 'account.payment',
                'context': "{'create': False}"
            }

    def action_create_payment(self):
        for obj in self.browse(self.env.context['active_ids']):
            journal = self.env['account.journal'].browse(int(
                self.env['ir.config_parameter'].sudo().get_param('topup_journal_id')))
            # if not obj.payment_id and obj.status == 'paid':
            payment_vals = {
                'date': fields.Date.today(),
                'amount': obj.amount,
                'vz_bank_charge': obj.service_fee,
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'is_topup': True,
                'journal_id': journal.id,
                'enable_charge': True,
                'partner_id': obj.corporate_id.id,
                'payment_method_id': self.env.ref(
                    'account.account_payment_method_manual_in').id,
            }
            payment_id = self.env['account.payment'].create(payment_vals)
            obj.payment_id = payment_id.id
            payment_id.action_post()