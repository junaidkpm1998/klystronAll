from datetime import datetime

from odoo import models, fields, api, _


class kgPeriod(models.Model):
    _name = 'kg.period'
    _description = 'Period'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name")
    date_from = fields.Date(string="Date From", default=datetime.today())
    date_to = fields.Date(string="Date To")
