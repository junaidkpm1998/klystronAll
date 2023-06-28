from odoo import api, fields, models, _
import pymssql
import xmlrpc.client
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class YggGiftTable(models.Model):
    _name = 'ygg.gifting.gift'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'code'
    _description = 'YGG Gifting Gift'

    # ygg_gift_id = fields.Char("Gift ID")
    ygag_gift_id = fields.Many2one('ygg.gift.table', string="Gift ID")
    ygg_record_id = fields.Integer("YGG Record ID")
    db_name = fields.Char("Database name")
    code = fields.Char("Code")
    corporate_id = fields.Many2one('res.partner', string="Corporate")
    amount = fields.Float("Amount")
    amount_in_currency = fields.Float("Amount in Currency")
    brand_id = fields.Many2one('product.product', string="Brand")

