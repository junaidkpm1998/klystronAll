from odoo import api, fields, models, _
import pymssql
import xmlrpc.client
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class ProductProduct(models.Model):
    _inherit = 'product.product'

    db_name = fields.Char("Database name")
    ygg_record_id = fields.Integer("YGG Record ID")
    is_generic = fields.Boolean('Is Generic', default=False)
    is_brand = fields.Boolean('Brand Product', default=False)
    product_code = fields.Char('Code', default=False)
