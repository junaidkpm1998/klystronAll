from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class KGPurchaseRequisitionTypeInherit(models.Model):
    _name = 'purchase.requisition.type'
    _description = "Purchase Requisition Type"
    _inherit = ["purchase.requisition.type", "mail.thread", "mail.activity.mixin"]

    name = fields.Char(string='Agreement Type', required=True, translate=True, tracking=True)

    @api.constrains('name')
    def _constrains_name(self):
        for rec in self:
            if rec.name:
                name_id = self.env['purchase.requisition.type'].search([('name', '=', rec.name)])
                if len(name_id) > 1:
                    raise ValidationError(_('Purchase Agreement Type Should Be Unique'))


class KGPurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    @api.model_create_multi
    def create(self, vals_list):
        for rec in vals_list:
            purchae_agreement_seq = self.env['ir.sequence'].next_by_code('kg.purchase.requisition.seq.code')
            update_seq = {'name': purchae_agreement_seq}
            rec.update(update_seq)
        return super(KGPurchaseRequisition, self).create(vals_list)
