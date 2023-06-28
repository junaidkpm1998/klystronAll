from odoo import api, fields, models, _
import pymssql
import xmlrpc.client
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class ResCompany(models.Model):
    _inherit = 'res.company'

    unique_id = fields.Char('Unique ID')

    _sql_constraints = [('unique_id_uniq', 'unique (unique_id)', "Unique ID already exists !")]