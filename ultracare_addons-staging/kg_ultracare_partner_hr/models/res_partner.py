# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    attachment = fields.One2many('partner.attachments', "partner_id", string="Attachment")


class PartnerAttachments(models.Model):
    _name = 'partner.attachments'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Attach Documents Related to the Partner'

    document_name = fields.Char()
    expiry = fields.Date()
    doc_attachment_partner = fields.Many2many('ir.attachment', 'doc_attach_paerner_rel', 'doc_id1', 'attach_id1',
                                              string=" Attachment",
                                              help='You can attach documents', copy=False, required=True)
    partner_id = fields.Many2one('res.partner')
    product_id = fields.Many2one('product.template', string='Product')
    override_doc = fields.Boolean('Override', default=False, tracking=True,
                                  help="If set yes, creates partner even if attachments are not added")









