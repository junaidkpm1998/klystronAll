from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    attachment = fields.One2many('hr.attachments', "hr_employee", string="Attachment")


class EmployeeAttachments(models.Model):
    _name = 'hr.attachments'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Attach Documents Related to the Employee'

    document_name = fields.Char()
    expiry = fields.Date()
    doc_attachment_partner = fields.Many2many('ir.attachment', 'attachment_ir_hr', 'doc_id1', 'attach_id1',
                                              string=" Attachment",
                                              help='You can attach documents', copy=False, required=True)
    hr_employee = fields.Many2one('hr.employee')
    product_id = fields.Many2one('product.template', string='Product')
    override_doc = fields.Boolean('Override', default=False, tracking=True,
                                  help="If set yes, creates partner even if attachments are not added")
