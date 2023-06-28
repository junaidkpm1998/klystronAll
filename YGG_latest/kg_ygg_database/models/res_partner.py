from odoo import api, fields, models, _
import pymssql
import xmlrpc.client
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class ResPartner(models.Model):
    _inherit = 'res.partner'

    selling_rate = fields.Monetary('Selling Rate')
    buying_rate = fields.Monetary('Buying Rate')
    unique_id = fields.Char('Unique ID')
    region = fields.Char('Region ID')
    order_table_ids = fields.One2many('ygg.order.table', 'partner_id')
    payment_table_ids = fields.One2many('ygg.payment.table', 'partner_id')
    currency_id = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.company.currency_id,)
    db_name = fields.Char("Database name")
    ygg_record_id = fields.Char("YGG Record ID")
    topup_account_id = fields.Many2one('account.account', string='Topup Account')
    corporate_region_id = fields.Many2one('ygg.corporate.region', string='Region')
    business_level_categ_id = fields.Many2one('ygg.business.level.category', string="Business Level Category")
    business_level_subcateg_id = fields.Many2one('ygg.business.level.subcategory', string="Business Level SubCategory")
    corporate_categ_id = fields.Many2one('ygg.corporate.category', string="Corporate Category")
    commission_fixed = fields.Float("Fixed Commission")
    commission_percentage = fields.Float("Commission %")
    contact_code = fields.Char("Code")


class YggOrderTable(models.Model):
    _name = 'ygg.order.table'
    _description = 'YGG Order Table'

    partner_id = fields.Many2one('res.partner', help="Get the client names")
    unique_id = fields.Char(related='partner_id.unique_id', help="Corporate Id")
    order_date = fields.Date('Order Date', help="Date of the Order")
    order_ref = fields.Date('Order Reference', help="Reference number")
    gift_type = fields.Char('Type of Gift/ Sales', help="Type of the Gift")
    coupon_no = fields.Char('Gift Card/ Coupon Number', help="Gift Card Number")
    coupon_value = fields.Char('Gift/ Coupon Value', help="Order Value")
    status = fields.Char('Status', help="Status of the Order")
    region = fields.Char(related='partner_id.region', string="Region of the Customer")
    sales_region = fields.Char(string="Sales Region", help="Sales Region")
    currency_rate = fields.Char(string="Currency Rate", help="Rate for Transaction")
    currency_id = fields.Many2one('res.currency', string="Currency", help="Order Currency")
    payment_status = fields.Many2one(string="Payment Status", help="Payment Status of the Order")


class YggPaymentTable(models.Model):
    _name = 'ygg.payment.table'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YGG Payment Table'

    partner_id = fields.Many2one('res.partner', help="Get the client names")
    corporate_id = fields.Many2one('res.partner', help="Get the client names")
    ygg_record_id = fields.Integer("YGG Record ID")
    date_added = fields.Datetime("Created On")
    date_modified = fields.Datetime("Modified On")
    amount = fields.Float("Amount")
    db_name = fields.Char("Database name")
    payment_reference = fields.Char("Payment Reference")
