# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    vendor_code = fields.Char(string="Vendor Code", default="NEW", store=True, copy=False)
    purchase_credit_limit = fields.Float(string="Purchase Credit Limit", default=0.00)

    @api.model
    def create(self, vals):
        if 'supplier_rank' in vals and int(vals['supplier_rank']) > 0:
            vals['vendor_code'] = self.env['ir.sequence'].next_by_code('vendorcode.sequence')
        res = super(ResPartner, self).create(vals)
        return res
