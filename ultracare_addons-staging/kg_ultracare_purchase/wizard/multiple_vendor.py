from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseorderMultivendor(models.TransientModel):
    _name = 'purchase.order.multi.vendor'
    _description = 'Purchase Order Multi Vendor'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    vendor_ids = fields.Many2many('res.partner', 'vendor_multilevel_rel', string="Vendors", required=True)
    purchase_order = fields.Many2many('purchase.order','purchase_order_rel', string='Purchase Orders')

    def action_send_vendors(self):
        subtype_ids = self.env['mail.message.subtype'].search(
            [('res_model', '=', 'purchase.order.multi.vendor')]).ids
        partners = []
        for i in self.purchase_order:
            partners.append(i.name)
        listToStr = ','.join([str(elem) for elem in partners])
        for user in self.vendor_ids:
            self.message_subscribe(partner_ids=[user.id], subtype_ids=subtype_ids)
            body = _(
                u'Sales coordinator approved the Sales Quotaion ' + listToStr + '. Please check and Confirm.')
            self.message_post(body=body, partner_ids=[user.id or []])
