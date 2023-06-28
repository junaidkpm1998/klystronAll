from odoo import api, fields, models, _


class YggCountry(models.Model):
    _name = 'ygg.country'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YGG Country'

    ygg_record_id = fields.Integer("YGG Record ID")
    created_on = fields.Datetime("Created On")
    modified_on = fields.Datetime("Modified On")
    db_name = fields.Char("Database name")
    currency_id = fields.Many2one('res.currency', string='Odoo Currency')
    country_id = fields.Many2one('res.country', 'Country', compute='_compute_country')
    name = fields.Char('Name', required=True)
    iso_code = fields.Char('ISO Code', required=True)

    @api.depends('iso_code')
    @api.onchange('iso_code')
    def _compute_country(self):
        for rec in self:
            if rec.iso_code:
                country = self.env['res.country'].sudo().search([('code', '=', rec.iso_code)], limit=1)
                rec.country_id = country.id
            else:
                rec.country_id = False

