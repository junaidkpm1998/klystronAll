from odoo import api, fields, models, _
import pymssql
import xmlrpc.client
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class YggTopup(models.Model):
    _name = 'ygg.corporate.payment'
    _rec_name = 'corporate_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YGG Corporate Payment'

    ygg_record_id = fields.Integer("YGG Record ID")
    date_added = fields.Datetime("Created On")
    date_modified = fields.Datetime("Modified On")
    db_name = fields.Char("Database Name")
    corporate_id = fields.Many2one('res.partner', string="Corporate")
    amount = fields.Monetary('Amount')
    currency_id = fields.Many2one('res.currency', string='Currency')
    payment_reference = fields.Char('Payment Reference')
    invoice_number = fields.Integer('Invoice Number')
    current_balance = fields.Monetary('Current Balance')
    top_up_date = fields.Datetime('TopUp Date')

    def view_entry(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Journal Entry',
            'view_mode': 'form',
            'res_id': self.move_id.id,
            'res_model': 'account.move',
            'domain': [('ygg_topup_id', '=', self.id)],
            'context': "{'create': False}"
        }
