from odoo import api, fields, models, _
import pymssql
import xmlrpc.client
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_payment_journal_id = fields.Many2one('account.journal', string='Sales Payment Journal')
    topup_journal_id = fields.Many2one('account.journal', string='Topup Journal')
    topup_account_id = fields.Many2one('account.account', string='Default Topup Account')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        sale_payment_journal_id = params.get_param('sale_payment_journal_id', default=False)
        topup_journal_id = params.get_param('topup_journal_id', default=False)
        topup_account_id = params.get_param('topup_account_id', default=False)
        res.update(
            sale_payment_journal_id=int(sale_payment_journal_id),
            topup_journal_id=int(topup_journal_id),
            topup_account_id=int(topup_account_id),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("sale_payment_journal_id", self.sale_payment_journal_id.id)
        self.env['ir.config_parameter'].sudo().set_param("topup_account_id", self.topup_account_id.id)
        self.env['ir.config_parameter'].sudo().set_param("topup_journal_id", self.topup_journal_id.id)


class YggBusinessLevelCategory(models.Model):
    _name = 'ygg.business.level.category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Business Level Category'

    name = fields.Char("Name", required=True)
    ygg_record_id = fields.Integer("YGG Record ID")
    date_added = fields.Datetime("Added Date")
    date_modified = fields.Datetime("Modified Date")
    db_name = fields.Char("Database name")


class YggCorporateSubCategory(models.Model):
    _name = 'ygg.business.level.subcategory'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Business Level SubCategory'

    name = fields.Char("Name", required=True)
    ygg_record_id = fields.Integer("YGG Record ID")
    date_added = fields.Datetime("Added Date")
    date_modified = fields.Datetime("Modified Date")
    business_level_categ_id = fields.Many2one('ygg.business.level.category', string="Business Level Category")
    db_name = fields.Char("Database name")


class YggCorporateCategory(models.Model):
    _name = 'ygg.corporate.category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Corporate Category'

    name = fields.Char("Name", required=True)
    ygg_record_id = fields.Integer("YGG Record ID")
    date_added = fields.Datetime("Added Date")
    date_modified = fields.Datetime("Modified Date")
    business_level_subcateg_id = fields.Many2one('ygg.business.level.subcategory', string="Business Level SubCategory")
    db_name = fields.Char("Database name")



