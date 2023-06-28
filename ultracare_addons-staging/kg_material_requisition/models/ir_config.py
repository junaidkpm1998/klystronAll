from odoo import models, fields, api, _


class MaterialConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'

    source_location = fields.Many2one('stock.location', string='Source Location')
    dest_location = fields.Many2one('stock.location', string='Destination Location')

    def get_values(self):
        res = super(MaterialConfiguration, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        source_location = params.get_param('source_location', default=False)
        dest_location = params.get_param('dest_location', default=False)
        res.update(
            source_location=int(source_location),
            dest_location=int(dest_location),
        )
        return res

    def set_values(self):
        res = super(MaterialConfiguration, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("source_location", self.source_location.id)
        self.env['ir.config_parameter'].sudo().set_param("dest_location", self.dest_location.id)
        return res