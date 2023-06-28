from ast import literal_eval
from datetime import datetime, date

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    creating_date = fields.Datetime(string="Create Date", default=datetime.today())
    approval_status = fields.Selection(
        [('waiting', 'Waiting'), ('rejected', 'Rejected'), ('approved', 'Approved'),
         ('finance_approve', 'Finance Approve'), ('operations_approve', 'Operation Approve')],
        tracking=True)
    finance_ids = fields.Many2one('res.users')
    operations_ids = fields.Many2one('res.users')
    director_ids = fields.Many2one('res.users')
    is_user = fields.Boolean(string="Is User", default=False)
    is_invoice = fields.Boolean(string="Is Invoice", default=False)
    is_approved = fields.Boolean(string="Is Approved")
    is_done = fields.Boolean(string="Is Done")
    attachment = fields.One2many('purchase.attachments', "purchase_order_id", string="Attachment")
    gm_approve_exceeds = fields.Boolean(string='GM Approve', default=False, compute='_compute_gm_approve_exceeds',
                                        store=True)
    finance_approve = fields.Char(string='Finance Approve')
    finance_approve_date = fields.Datetime(string='Finance Approve Date')
    operation_approve = fields.Char(string='Operation Approve')
    operation_approve_date = fields.Datetime(string='Operation Approve Date')
    director_approve = fields.Char(string='Director Approve')
    director_approve_date = fields.Datetime(string='Director Approve Date')

    kg_is_alternative = fields.Boolean('Is Alternative', default=False)
    selected_total = fields.Float(string="Selected Total", compute='compute_selected_total')
    # subtotal_words = fields.Char()

    @api.depends('order_line')
    def compute_selected_total(self):
        for i in self:
            if i.order_line:
                amt = sum(i.order_line.filtered(lambda x: x.is_select).mapped('price_subtotal'))
                if amt:
                    i.selected_total = amt
                else:
                    i.selected_total = 0
            else:
                i.selected_total = 0

    @api.depends('amount_total')
    def _compute_gm_approve_exceeds(self):
        for rec in self:
            mininum_amount = self.env['ir.config_parameter'].sudo().get_param('kg_ultracare_purchase.kg_minimum_amount')
            if float(mininum_amount) <= rec.amount_total:
                rec.gm_approve_exceeds = True
            else:
                rec.gm_approve_exceeds = False

    def write(self, vals):
        for po in self:
            if po.order_line and po.state == 'purchase':
                if not self.env.user.has_group('purchase.group_purchase_manager'):
                    raise UserError('You Have No Access To Update The Purchase Order Lines After Purchase Order')
        return super(PurchaseOrder, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for i in vals_list:
            req_for_quo = self.env['ir.sequence'].next_by_code('kg.req.for.quot')
            update_seq = {'name': req_for_quo}
            i.update(update_seq)
        res = super(PurchaseOrder, self).create(vals_list)
        config_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_ultracare_purchase.finance_ids', self.finance_ids)
        user_list = []
        if literal_eval(config_approve_users):
            for i in literal_eval(config_approve_users):
                users = self.env['res.users'].browse(i)
                user_list.append(users)
            approve_users = ','.join([str(elem) for elem in user_list])
            login_user = self.env.user.name
            partners = []
            subtype_ids = self.env['mail.message.subtype'].search(
                [('res_model', '=', 'purchase.order')]).ids
            for user in user_list:
                res.activity_schedule('kg_ultracare_purchase.finance_approval', user_id=user.id,
                                      note=f'User created the Purchase Order {res.name}. Please Verify and approve.')
                res.message_subscribe(partner_ids=[user.partner_id.id], subtype_ids=subtype_ids)
                partners.append(user.partner_id.id)
            body = _(u'Admin approves the design request ' + res.name + '.')
            res.message_post(body=body, partner_ids=partners)
            # message.
            res.finance_ids = self.env.user.id
            res.update({'approval_status': 'waiting'})
        else:
            raise ValidationError(_('Please select users in configuration'))
        return res

    # def kg_button_confirm(self):
    #     return self.with_context({'skip_alternative_check': True}).button_confirm()

    def button_confirm(self):
        approve_activity = self.env.ref('kg_ultracare_purchase.approve_purchase_order')
        approve_activity_2 = self.activity_ids.filtered(
            lambda l: l.activity_type_id == approve_activity)
        approve_activity_2.action_done()
        if self.approval_status == 'approved':
            self.name = self.env['ir.sequence'].next_by_code('kg.purchase.order.seq.code')
            for k in self.order_line:
                for line in k.product_id.variant_seller_ids:
                    if line.partner_id.id == k.partner_id.id:
                        line.price = k.price_unit
            res = super(PurchaseOrder, self).button_confirm()
            pick = self.env['stock.picking'].search([('origin', '=', self.name)])
            print(pick, "PICKKK")
            for i in self.order_line:
                if not i.is_select:
                    for l in pick.move_ids_without_package:
                        if l.purchase_line_id.id == i.id:
                            l.write({'state': 'draft'})
                            l.unlink()
            return res
        else:
            raise UserError(_("You cannot confirm until the quotation is approved"))

    def action_reject(self):
        self.approval_status = 'rejected'
        self.button_cancel()

    def action_finance_approve(self):
        approve_activity = self.env.ref('kg_ultracare_purchase.finance_approval')
        approve_activity_2 = self.activity_ids.filtered(
            lambda l: l.activity_type_id == approve_activity)
        approve_activity_2.action_done()
        for rec in self:
            config_approve_users = self.env['ir.config_parameter'].sudo().get_param(
                'kg_ultracare_purchase.operations_ids', self.operations_ids)
            config_approve_users_finance = self.env['ir.config_parameter'].sudo().get_param(
                'kg_ultracare_purchase.finance_ids', self.finance_ids)
            prev_users = []
            for j in literal_eval(config_approve_users_finance):
                users = self.env['res.users'].browse(j)
                prev_users.append(users.name)
            user_list = []
            user_ids = []
            if literal_eval(config_approve_users):
                for i in literal_eval(config_approve_users):
                    users = self.env['res.users'].browse(i)
                    user_list.append(users)
                    user_ids.append(users.name)
                approve_users = ','.join([str(elem) for elem in user_list])
                login_user = self.env.user.name
                if login_user in prev_users:
                    partners = []
                    subtype_ids = self.env['mail.message.subtype'].search(
                        [('res_model', '=', 'purchase.order')]).ids
                    for user in user_list:
                        rec.activity_schedule('kg_ultracare_purchase.operation_approval', user_id=user.id,
                                              note=f'The user {self.env.user.name} is approved the finance approval and requested to approve the PO {rec.name}. Please Verify and approve.')
                        rec.message_subscribe(partner_ids=[user.partner_id.id], subtype_ids=subtype_ids)
                        partners.append(user.partner_id.id)
                    body = _(u'Admin approves the design request ' + rec.name + '.')
                    rec.message_post(body=body, partner_ids=partners)
                    rec.operations_ids = self.env.user.id
                    rec.approval_status = 'finance_approve'
                else:
                    raise ValidationError(_('You have no permission to approve'))
            else:
                raise ValidationError(_('Please select users in configuration'))
        self.finance_approve = self.env.user.name
        self.finance_approve_date = datetime.now()

    def invoice_due(self):
        invoice = self.env['account.move'].search(
            [('partner_id', '=', self.partner_id.id), ('move_type', '=', 'in_invoice'),
             ('invoice_date_due', '<', date.today())])
        for inv in invoice:
            if inv.payment_state == 'not_paid':
                return True

    def action_operation_approve(self):
        if self.gm_approve_exceeds != True:
            approve_activity = self.env.ref('kg_ultracare_purchase.operation_approval')
            approve_activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == approve_activity)
            approve_activity_2.action_done()
            self.write({'approval_status': 'approved'})
            self.with_context({'skip_alternative_check': True}).button_confirm()
        else:
            approve_activity = self.env.ref('kg_ultracare_purchase.operation_approval')
            approve_activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == approve_activity)
            approve_activity_2.action_done()
            for rec in self:
                config_approve_users = self.env['ir.config_parameter'].sudo().get_param(
                    'kg_ultracare_purchase.director_ids', self.director_ids)
                config_approve_users_operation = self.env['ir.config_parameter'].sudo().get_param(
                    'kg_ultracare_purchase.operations_ids', self.operations_ids)
                prev_users = []
                for j in literal_eval(config_approve_users_operation):
                    users = self.env['res.users'].browse(j)
                    prev_users.append(users.name)
                user_list = []
                user_ids = []
                if literal_eval(config_approve_users):
                    for i in literal_eval(config_approve_users):
                        users = self.env['res.users'].browse(i)
                        user_list.append(users)
                        user_ids.append(users.name)
                    approve_users = ','.join([str(elem) for elem in user_list])
                    login_user = self.env.user.name
                    if login_user in prev_users:
                        partners = []
                        subtype_ids = self.env['mail.message.subtype'].search(
                            [('res_model', '=', 'purchase.order')]).ids
                        for user in user_list:
                            rec.activity_schedule('kg_ultracare_purchase.director_approval', user_id=user.id,
                                                  note=f'The user {self.env.user.name} is approved the Operation Approval and requested to approve the PO {rec.name} to Director Approval. \nPlease Verify and approve.')
                            rec.message_subscribe(partner_ids=[user.partner_id.id], subtype_ids=subtype_ids)
                            partners.append(user.partner_id.id)
                        body = _(u'Admin approves the design request ' + rec.name + '.')
                        rec.message_post(body=body, partner_ids=partners)
                        rec.operations_ids = self.env.user.id
                        rec.approval_status = 'operations_approve'
                    else:
                        raise ValidationError(_('You have no permission to approve'))
                else:
                    raise ValidationError(_('Please select users in configuration'))
        self.operation_approve = self.env.user.name
        self.operation_approve_date = datetime.now()

    def action_director_approve(self):
        for rec in self:
            user_list = list(self.user_id)
            config_approve_users_director = self.env['ir.config_parameter'].sudo().get_param(
                'kg_ultracare_purchase.director_ids', self.director_ids)
            prev_users = []
            for j in literal_eval(config_approve_users_director):
                users = self.env['res.users'].browse(j)
                prev_users.append(users.name)
            if prev_users:
                login_user = self.env.user.name
                if login_user in prev_users:
                    partners = []
                    subtype_ids = self.env['mail.message.subtype'].search(
                        [('res_model', '=', 'purchase.order')]).ids
                    for user in user_list:
                        rec.activity_schedule('kg_ultracare_purchase.director_approval', user_id=user.id,
                                              note=f'The user {self.env.user.name} is approved the Operation Approval and requested to approve the PO {rec.name} to Director Approval. \nPlease Verify and approve.')
                        rec.message_subscribe(partner_ids=[user.partner_id.id], subtype_ids=subtype_ids)
                        partners.append(user.partner_id.id)
                    body = _(
                        u'The user ' + self.env.user.name + ' is approved the Operation Approval and requested to approve the PO ' + rec.name + ' to Director Approval. \nPlease Verify and approve.')
                    rec.message_post(body=body, partner_ids=partners)
                    rec.operations_ids = self.env.user.id
                    rec.approval_status = 'approved'
                else:
                    raise ValidationError(_('You have no permission to approve'))
            else:
                raise ValidationError(_('Please select users in configuration'))
        self.director_approve = self.env.user.name
        self.director_approve_date = datetime.now()

        approve_activity = self.env.ref('kg_ultracare_purchase.director_approval')
        approve_activity_2 = self.activity_ids.filtered(
            lambda l: l.activity_type_id == approve_activity)
        approve_activity_2.action_done()
        return self.with_context({'skip_alternative_check': True}).button_confirm()

    def action_approvals(self):
        self.is_invoice = True

    def kg_purchase_order_report(self):
        return self.env.ref('kg_ultracare_purchase.purchase_order_report').report_action(self)

    def action_create_invoice(self):
        res = super(PurchaseOrder, self).action_create_invoice()
        if self.is_approved:
            return res
        if self.approval_status == 'approved':
            for i in self:
                if self.amount_total > self.partner_id.purchase_credit_limit:
                    self.invoice_due()
                    if i.date_planned:
                        today = datetime.today()
                        if i.date_planned < today:
                            self.is_invoice = True
                            self.onchange_is_invoice()
                        else:
                            return res
                    else:
                        raise UserError("Please Update the Expected Arrival Date")
                else:
                    return res
        else:
            raise ValidationError(_("Please Wait until the Purchase Order is approved"))

    def action_request_approval(self):
        if self.is_invoice:
            sale_man = self.env['ir.config_parameter'].sudo().get_param('kg_ultracare_purchase.director_ids',
                                                                        self.director_ids)
            user_list = []
            user_ids = []
            if literal_eval(sale_man):
                for i in literal_eval(sale_man):
                    users = self.env['res.users'].browse(i)
                    user_list.append(users)
                    user_ids.append(users.name)
                approve_users = ','.join([str(elem) for elem in user_list])
                login_user = self.env.user.name
                if login_user in user_list:
                    partners = []
                    subtype_ids = self.env['mail.message.subtype'].search(
                        [('res_model', '=', 'purchase.order')]).ids
                    for user in user_list:
                        self.activity_schedule('kg_ultracare_purchase.approve_purchase_order', user_id=user.id,
                                               note=f'Sales coordinator approved the Sales Quotaion ' + self.name + '. Please check and Confirm.')
                        self.message_subscribe(partner_ids=[user.partner_id.id], subtype_ids=subtype_ids)
                        partners.append(user.partner_id.id)
                    body = _(
                        u'Sales coordinator approved the Sales Quotaion ' + self.name + '. Please check and Confirm.')
                    self.message_post(body=body, partner_ids=partners)
                self.is_done = True
                self.is_invoice = False

    def action_approve(self):
        approve_activity = self.env.ref('kg_ultracare_purchase.approve_purchase_order')
        approve_activity_2 = self.activity_ids.filtered(
            lambda l: l.activity_type_id == approve_activity)
        approve_activity_2.action_done()
        for rec in self:
            user_list = list(rec.user_id)
            config_approve_users_director = self.env['ir.config_parameter'].sudo().get_param(
                'kg_ultracare_purchase.director_ids', rec.director_ids)
            prev_users = []
            for j in literal_eval(config_approve_users_director):
                users = self.env['res.users'].browse(j)
                prev_users.append(users.name)
            if rec.user_id:
                login_user = self.env.user.name
                if login_user in prev_users:
                    partners = []
                    subtype_ids = self.env['mail.message.subtype'].search(
                        [('res_model', '=', 'purchase.order')]).ids
                    for user in user_list:
                        rec.activity_schedule('kg_ultracare_purchase.approve_purchase_order', user_id=user.id,
                                              note=f'The user {self.env.user.name} is approved the Operation Approval and requested to approve the PO {rec.name} to Director Approval. \nPlease Verify and approve.')
                        rec.message_subscribe(partner_ids=[user.partner_id.id], subtype_ids=subtype_ids)
                        partners.append(user.partner_id.id)
                    body = _(
                        u'The user ' + self.env.user.name + ' is approved the Operation Approval and requested to approve the PO ' + rec.name + ' to Director Approval. \nPlease Verify and approve.')
                    rec.message_post(body=body, partner_ids=partners)
                    rec.operations_ids = self.env.user.id
                    rec.approval_status = 'approved'
                    rec.is_user = True
                    rec.is_approved = True
            else:
                rec.is_user = False
            if rec.is_user != True:
                raise UserError(_("You have no access to approve"))

    @api.onchange('is_invoice')
    def onchange_is_invoice(self):
        if self.date_planned:
            return {
                'warning': {
                    'title': _('Warning'),
                    'message': _(
                        "Either the due date is over or the partner purchase credit limit is above for this Purchase Payment.\n Kindly click on the Send to Manager button for approval if it is neccessary..!"),
                }
            }

    def action_multi_vendor(self):
        action = {
            'name': 'Multi Vendor',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'purchase.order.multi.vendor',
            'context': {'default_purchase_order': self.ids},
            'target': 'new'
        }
        return action


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    is_select = fields.Boolean(string="Select", default=True)

    def action_choose(self):
        order_lines = (self.order_id | self.order_id.alternative_po_ids).mapped('order_line')
        order_lines = order_lines.filtered(
            lambda l: l.product_qty and l.product_id.id in self.product_id.ids and l.id not in self.ids)
        if order_lines:
            return order_lines.action_clear_quantities()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Nothing to clear"),
                'message': _("There are no quantities to clear."),
                'sticky': False,
            }
        }

    def action_clear_quantities(self):
        zeroed_lines = self.filtered(lambda l: l.state not in ['cancel', 'purchase', 'done'])
        # zeroed_lines.write({'product_qty': 0})
        zeroed_lines.write({
            'is_select': False
        })
        if len(self) > len(zeroed_lines):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Some not cleared"),
                    'message': _("Some quantities were not cleared because their status is not a RFQ status."),
                    'sticky': False,
                }
            }
        return False


class PurchaseAttachments(models.Model):
    _name = 'purchase.attachments'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Attach Documents Related to the purchase'

    document_name = fields.Char()
    expiry = fields.Date()
    doc_attachment_partner = fields.Many2many('ir.attachment', 'attachment_ir_purchase', 'doc_id1', 'attach_id1',
                                              string=" Attachment",
                                              help='You can attach documents', copy=False, required=True)
    purchase_order_id = fields.Many2one('purchase.order')
    product_id = fields.Many2one('product.template', string='Product')
    override_doc = fields.Boolean('Override', default=False, tracking=True,
                                  help="If set yes, creates partner even if attachments are not added")
