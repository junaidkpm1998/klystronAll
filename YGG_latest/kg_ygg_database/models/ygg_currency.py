from odoo import api, fields, models, _


class YggCurrency(models.Model):
    _name = 'ygg.currency'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YGG Currency'

    ygg_record_id = fields.Integer("YGG Record ID")
    created_on = fields.Datetime("Created On")
    modified_on = fields.Datetime("Modified On")
    db_name = fields.Char("Database name")
    currency_id = fields.Many2one('res.currency', string='Odoo Currency', compute='_compute_currency')
    name = fields.Char('Name', required=True)
    iso_code = fields.Char('ISO Code', required=True)
    decimal_notation = fields.Integer('Decimal Notation')

    @api.depends('iso_code')
    @api.onchange('iso_code')
    def _compute_currency(self):
        for rec in self:
            if rec.iso_code:
                currency = self.env['res.currency'].sudo().search([('name', '=', rec.iso_code)], limit=1)
                rec.currency_id = currency.id
            else:
                rec.currency_id = False

