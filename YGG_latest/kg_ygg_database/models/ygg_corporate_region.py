from odoo import api, fields, models, _


class YggCorporateRegion(models.Model):
    _name = 'ygg.corporate.region'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YGG Corporate Region'

    ygg_record_id = fields.Integer("YGG Record ID")
    date_added = fields.Datetime("Added On")
    date_modified = fields.Datetime("Modified On")
    db_name = fields.Char("Database name")
    name = fields.Char("Name")

