from odoo import api, fields, models, _
import pymssql
import xmlrpc.client
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class YggContentType(models.Model):
    _name = 'ygg.content.type'
    _rec_name = 'app_label'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YGG Content Type'

    ygg_record_id = fields.Integer("YGG Record ID")
    app_label = fields.Char("App Label")
    model = fields.Char("Model")
    db_name = fields.Char("Database Name")
