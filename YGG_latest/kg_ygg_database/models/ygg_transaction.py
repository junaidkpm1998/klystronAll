from odoo import api, fields, models, _
import pymssql
import xmlrpc.client
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class YggTransaction(models.Model):
    _name = 'ygg.transaction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "YGG Transaction"

    ygg_record_id = fields.Integer("YGG Record ID")
    created_on = fields.Datetime("Created On")
    modified_on = fields.Datetime("Modified On")
    db_name = fields.Char("Database name")
    amount = fields.Monetary('Amount')
    customer_name = fields.Char('Customer Name')
    customer_email = fields.Char('Customer Email')
    currency_id = fields.Many2one('res.currency', string='Odoo Currency', compute='_compute_currency')
    currency = fields.Char('Currency Symbol')
    status = fields.Selection([('Pending', 'Pending'),('Paid', 'Paid'),('Declined', 'Declined')], default='pending')
    response_summary = fields.Char('Response Summary')
    payment_method = fields.Char('Payment Method')
    payment_scheme = fields.Char('Payment Scheme')
    card_bin = fields.Char('Card Bin')
    card_last4 = fields.Char('Card Last4')
    object_id = fields.Integer('Object ID')
    content_type_id = fields.Many2one('ygg.content.type', string="Content Type")

    @api.depends('currency')
    @api.onchange('currency')
    def _compute_currency(self):
        for rec in self:
            if rec.currency:
                currency = self.env['res.currency'].sudo().search([('name', '=', rec.currency)], limit=1)
                rec.currency_id = currency.id
            else:
                rec.currency_id = False
