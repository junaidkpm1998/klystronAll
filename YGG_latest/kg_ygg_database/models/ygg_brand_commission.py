from odoo import api, fields, models, _
import pymssql
import xmlrpc.client
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class YggBrandCommission(models.Model):
    _name = 'ygg.brand.commission'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'brand_id'
    _description = 'YGG Brand Commission'

    ygg_record_id = fields.Integer("YGG Record ID")
    created_on = fields.Datetime("Created On")
    modified_on = fields.Datetime("Modified On")
    db_name = fields.Char("Database name")

    gift_type = fields.Selection([('normal', 'Normal'), ('all', 'All'), ('b2c', 'B2C'), ('corporate', 'Corporate')])
    corporate_id = fields.Many2one('res.partner', string="Corporate")
    brand_id = fields.Many2one('product.product', )
    commission_type = fields.Selection([('percentage', 'Percentage'), ('fixed', 'Fixed'), ('fixed_percentage', 'Fixed Percentage'), ('denomination', 'Denomination'), ('deduct_percentage', 'Deduct Amount & Percentage')])
    commission_amount = fields.Float("Commission Amount")
    commission_percentage = fields.Float("Commission %")
    start_date = fields.Datetime("Start Date")
    end_date = fields.Datetime("End Date")
    currency_id = fields.Many2one('res.currency', string='Odoo Currency', compute='_compute_currency')
    currency = fields.Char('Currency Symbol')

    @api.depends('currency')
    @api.onchange('currency')
    def _compute_currency(self):
        for rec in self:
            if rec.currency:
                currency = self.env['res.currency'].sudo().search([('name', '=', rec.currency)], limit=1)
                rec.currency_id = currency.id
            else:
                rec.currency_id = False

    code = fields.Char('Code')

    @api.model
    def create(self, vals):
        res = super(YggBrandCommission, self).create(vals)
        for r in res:
            if r.corporate_id:
                vals = [(0, 0, {
                    'partner_id': r.corporate_id.id,
                    'commission_per': r.commission_percentage,
                    'date_start': r.start_date,
                    'date_end': r.end_date,
                    'min_qty': 1,
                })]
                r.brand_id.write({'seller_ids': vals})
        return res

