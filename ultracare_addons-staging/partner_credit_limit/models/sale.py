# See LICENSE file for full copyright and licensing details.


from odoo import _, api, models, fields
from odoo.exceptions import UserError
from datetime import date


class SaleOrder(models.Model):
    _inherit = "sale.order"

    over_credit_sale = fields.Boolean(string='Over Credit', default=False, copy=False)

    @api.onchange('partner_id')
    def compute_over_credit(self):
        if self.partner_id:
            invoice = self.env['account.move'].sudo().search(
                [('partner_id', '=', self.partner_id.id), ('move_type', '=', 'out_invoice'),
                 ('invoice_date_due', '<', date.today()), ('company_id', '=', self.env.company.id)])
            if invoice:
                not_paid = invoice.filtered(lambda rec: rec.payment_state == 'not_paid')
                if not_paid:
                    self.over_credit_sale = True
                else:
                    self.over_credit_sale = False
            else:
                self.over_credit_sale = False
        else:
            self.over_credit_sale = False

    def check_limit(self):
        self.ensure_one()
        partner = self.partner_id
        user_id = self.env['res.users'].search([
            ('partner_id', '=', partner.id)], limit=1)
        if user_id and not user_id.has_group('base.group_portal') or not \
                user_id:
            moveline_obj = self.env['account.move.line']
            movelines = moveline_obj.search([('partner_id', '=', partner.id),
                                             ('move_id.move_type', 'in', ['out_invoice']),
                                             ('parent_state', '!=', 'cancel')])
            confirm_sale_order = self.search(
                [('partner_id', '=', partner.id),
                 ('state', '=', 'sale'),
                 ('invoice_status', '!=', 'invoiced')])
            debit, credit = 0.0, 0.0
            amount_total = 0.0
            for status in confirm_sale_order:
                amount_total += status.amount_total
            for line in movelines:
                credit += line.credit
                debit += line.debit
            partner_credit_limit = (debit + amount_total) - credit
            available_credit_limit = round(
                partner.credit_limit - partner_credit_limit, 2)
            if partner_credit_limit > partner.credit_limit and partner.credit_limit > 0.0:
                if self.approval_status_credit != 'approved' or self.approval_status_credit == False:
                    if not partner.over_credit:
                        msg = 'Your available credit limit' \
                              ' Amount = %s \nCheck "%s" Accounts or Credit ' \
                              'Limits.' % (available_credit_limit,
                                           self.partner_id.name)
                        raise UserError(_('You can not confirm Sale '
                                          'Order. \n' + msg))
                else:
                    return True
            return True

    def check_warning(self):
        self.ensure_one()
        partner = self.partner_id
        user_id = self.env['res.users'].search([
            ('partner_id', '=', partner.id)], limit=1)
        if user_id and not user_id.has_group('base.group_portal') or not \
                user_id:
            moveline_obj = self.env['account.move.line']
            movelines = moveline_obj.search(
                [('partner_id', '=', partner.id),
                 ('move_id.move_type', 'in', ['out_invoice']),

                 # ('account_id.user_type_id.name', 'in',
                 #    ['Receivable', 'Payable']),
                 ('parent_state', '!=', 'cancel')]
            )
            confirm_sale_order = self.search(
                [('partner_id', '=', partner.id),
                 ('state', '=', 'sale'),
                 ('invoice_status', '!=', 'invoiced')])
            debit, credit = 0.0, 0.0
            amount_total = 0.0
            for status in confirm_sale_order:
                amount_total += status.amount_total
            for line in movelines:
                credit += line.credit
                debit += line.debit
            partner_credit_limit = (
                                           debit + amount_total) - credit
            available_credit_limit = round(
                partner.warning_limit - partner_credit_limit, 2)
            if partner_credit_limit > partner.warning_limit and \
                    partner.warning_limit > 0.0 and partner_credit_limit < partner.credit_limit:
                msg = 'Your warning limit is ' \
                      '%.2f \n .You crossed this limit and reached %.2f' \
                      % (float(partner.warning_limit),
                         float(partner_credit_limit))
                return msg
            return "1"

    def invoice_due(self):
        invoice = self.env['account.move'].sudo().search(
            [('partner_id', '=', self.partner_id.id), ('move_type', '=', 'out_invoice'),
             ('invoice_date', '<', date.today()), ('company_id', '=', self.env.company.id)])
        for inv in invoice:
            if inv.payment_state == 'not_paid':
                raise UserError(
                    _('There are due date exceeded Invoices for this customer.\n '
                      'Kindly request for a approval to continue..!'))

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        invoices = self.env['account.move'].search(
            [('partner_id', '=', res.partner_id.id), ('move_type', '=', 'out_invoice'),
             ('invoice_date_due', '<', date.today()), ('payment_state', '=', 'not_paid')])
        if invoices:
            raise UserError(_("You cannot create a sales order without confirming or cancel due invoices"))
        return res

    approval_status = fields.Selection(
        [('waiting', 'Waiting'), ('rejected', 'Rejected'), ('approved', 'Approved')],
        tracking=True, default=False, copy=False)
    approval_status_credit = fields.Selection(
        [('waiting', 'Waiting'), ('rejected', 'Rejected'), ('approved', 'Approved')],
        tracking=True, default=False, copy=False)
    credit_bool = fields.Boolean(string='credit bool', default=False, help="For approved credit limit")
    unit_bool = fields.Boolean(string='Unit bool', default=False, help="For Changes of unit price")

    def button_credit_limit_approve(self):
        res_user = self.env['res.users'].search([])
        list = []
        if self.env.user.has_group('sales_team.group_sale_manager'):
            self.over_credit_sale = False
            self.approval_status_credit = 'approved'
        else:
            a = self.env['res.users'].browse(self.team_id.user_id.id)
            if a:
                list.append(a)
            partners = []
            for k in list:
                subtype_ids = self.env['mail.message.subtype'].search(
                    [('res_model', '=', 'sale.order')]).ids
                self.message_subscribe(partner_ids=[k.partner_id.id], subtype_ids=subtype_ids)
                partners.append(k.partner_id.id)
                body = _(
                    u'Sales Person ' + self.env.user.name + ' requested to approve the Credit Limit updation. Kindly check & Confirm.')
                self.message_post(body=body, partner_ids=partners)
            self.approval_status_credit = 'waiting'

    def approve_credit_manager(self):
        if self.approval_status_credit == 'waiting':
            res_user = self.env['res.users'].search([('id', '=', self.env.user.id)])
            if res_user.has_group('sales_team.group_sale_salesman_all_leads') == True:
                self.credit_bool = True
                self.over_credit_sale = False
                self.approval_status_credit = 'approved'
            else:
                raise UserError(
                    _("You have no access to Approve the Credit limit request.Kindly contact to sales manager to continue..!"))

    def reject_credit_manager(self):
        if self.approval_status_credit == 'waiting':
            res_user = self.env['res.users'].search([('id', '=', self.env.user.id)])
            if res_user.has_group('sales_team.group_sale_salesman_all_leads') == True:
                self.credit_bool = False
                self.approval_status_credit = 'rejected'
            else:
                raise UserError(
                    _("You have no access to Reject the Credit limit request.Kindly contact to sales manager to continue..!"))

    ##### For Unit price Apporval ##############

    @api.constrains('amount_total')
    def compute_amount_total(self):
        for i in self:
            if i.amount_total > 0:
                if i.partner_id.credit_limit < i.amount_total:
                    i.over_credit_sale = True
                else:
                    i.over_credit_sale = False
            else:
                i.over_credit_sale = False
            if i.partner_id:
                invoice = self.env['account.move'].sudo().search(
                    [('partner_id', '=', i.partner_id.id), ('move_type', '=', 'out_invoice'),
                     ('invoice_date_due', '<', date.today()), ('company_id', '=', self.env.company.id)])
                if invoice:
                    not_paid = invoice.filtered(lambda rec: rec.payment_state == 'not_paid')
                    if not_paid:
                        i.over_credit_sale = True
                    else:
                        i.over_credit_sale = False
                else:
                    i.over_credit_sale = False
            else:
                i.over_credit_sale = False

    @api.constrains('order_line')
    def compute_unit_price(self):
        x = 0
        for i in self:
            for rec in i.order_line:
                if rec.price_unit != rec.sp_unit_amt:
                    if rec.price_change:
                        x += 1
                else:
                    i.unit_bool = False
            if x != 0:
                i.unit_bool = True
            else:
                i.unit_bool = False

    @api.onchange('order_line')
    def onchange_sp_unit_amt(self):
        for i in self.order_line:
            if i.price_unit != i.sp_unit_amt:
                if self.approval_status == 'approved':
                    self.approval_status = False
                if self.approval_status == 'rejected':
                    self.approval_status = False
                return {
                    'warning': {
                        'title': _('Warning'),
                        'message': _(
                            "The Salesperson Changed the default unit price. Please click on the request button to approve from the manager..!"),
                    }
                }

    def button_manager_approve(self):
        price_unit_activity_not = self.env.ref('partner_credit_limit.price_unit_approved_notification')
        activity_2 = self.activity_ids.filtered(
            lambda l: l.activity_type_id == price_unit_activity_not)
        activity_2.unlink()

        price_unit_activity_reject = self.env.ref('partner_credit_limit.price_unit_rejected_notification')
        activity_3 = self.activity_ids.filtered(
            lambda l: l.activity_type_id == price_unit_activity_reject)
        activity_3.unlink()

        res_user = self.env['res.users'].search([])
        list = []
        if self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            self.unit_bool = False
            self.approval_status = 'approved'
        else:
            a = self.env['res.users'].browse(self.team_id.user_id.id)
            if a:
                list.append(a)
            partners = []
            for k in list:
                self.activity_schedule('partner_credit_limit.kg_price_unit_approval_notification',
                                       user_id=k.id,
                                       note=f'The user {self.env.user.name} requested to approve the price unit updation the Sale Order {self.name}. Please Verify and approve sale order.')

                # subtype_ids = self.env['mail.message.subtype'].search(
                #     [('res_model', '=', 'sale.order')]).ids
                # self.message_subscribe(partner_ids=[k.partner_id.id], subtype_ids=subtype_ids)
                # partners.append(k.partner_id.id)
                # body = _(
                #     u'Sales Person ' + self.env.user.name + ' requested to approve the unit price updation. Kindly check & Confirm.')
                # self.message_post(body=body, partner_ids=partners)
            self.approval_status = 'waiting'

    def approve_unit_manager(self):
        if self.approval_status == 'waiting':
            price_unit_activity_not = self.env.ref('partner_credit_limit.kg_price_unit_approval_notification')
            activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == price_unit_activity_not)
            activity_2.action_done()

            res_user = self.env['res.users'].search([('id', '=', self.env.user.id)])
            if res_user.has_group('sales_team.group_sale_salesman_all_leads') == True:
                for i in self.order_line:
                    if i.price_change:
                        i.write({
                            'price_unit': i.sp_unit_amt,
                            'diff_price': True
                        })
                self.approval_status = 'approved'
                self.unit_bool = False

                self.activity_schedule('partner_credit_limit.price_unit_approved_notification',
                                       user_id=self.user_id.id,
                                       note=f'The user {self.env.user.name} approved the price unit updation the Sale Order {self.name}. Please Verify and confirm sale order.')
            else:
                raise UserError(_("You have no access to approve"))

    def reject_unit_manager(self):
        price_unit_activity_not = self.env.ref('partner_credit_limit.kg_price_unit_approval_notification')
        activity_2 = self.activity_ids.filtered(
            lambda l: l.activity_type_id == price_unit_activity_not)
        activity_2.unlink()

        if self.approval_status == 'waiting':
            res_user = self.env['res.users'].search([('id', '=', self.env.user.id)])
            if res_user.has_group('sales_team.group_sale_salesman_all_leads') == True:
                for i in self.order_line:
                    if i.price_change:
                        i.write({
                            'sp_unit_amt': 0
                        })
                self.approval_status = 'rejected'
                self.activity_schedule('partner_credit_limit.price_unit_rejected_notification',
                                       user_id=self.user_id.id,
                                       note=f'The user {self.env.user.name} rejected the price unit updation the Sale Order {self.name}.')

            else:
                raise UserError(_("You have no access to approve"))

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()

        price_unit_activity_not = self.env.ref('partner_credit_limit.price_unit_approved_notification')
        activity_2 = self.activity_ids.filtered(
            lambda l: l.activity_type_id == price_unit_activity_not)
        activity_2.action_done()

        if self.approval_status == 'rejected':
            price_unit_activity_not_reject = self.env.ref('partner_credit_limit.price_unit_rejected_notification')
            activity_3 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == price_unit_activity_not_reject)
            activity_3.action_done()

            return super(SaleOrder, self).action_confirm()

        for order in self:
            if order.approval_status == 'waiting' or order.unit_bool or order.over_credit_sale:
                raise UserError(_("Please finish the approval to confirm the Sale Quotation"))
            if not order.credit_bool and order.approval_status_credit != 'approved':
                # order.credit_bool = True
                msg = order.check_warning()
                if order.partner_id.use_partner_credit_limit:
                    if msg != "1":
                        created_popup = self.env['sale.credit.notification'].create({'msg': msg}).id
                        return {
                            'name': _('Warning Limit Exceeded..!'),
                            'type': 'ir.actions.act_window',
                            'view_mode': 'form',
                            'view_type': 'form',
                            'res_model': 'sale.credit.notification',
                            'res_id': created_popup,
                            'views': [(self.env.ref('partner_credit_limit.view_sale_credit_exceeded').id, 'form')],
                            'view_id': self.env.ref('partner_credit_limit.view_sale_credit_exceeded').id,
                            'target': 'new'
                        }
                    order.check_limit()
                    order.invoice_due()
                else:
                    return super(SaleOrder, self).action_confirm()
            else:
                return super(SaleOrder, self).action_confirm()
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _readonly_price(self):
        res_user = self.env['res.users'].browse(self._uid)
        # if res_user.has_group('sales_team.group_sale_salesman_all_leads'):
        #     return False
        if res_user.has_group('sales_team.group_sale_manager'):
            return False
        elif res_user.has_group('sales_team.group_sale_salesman'):
            return True
        else:
            return False

    def _readonly_sales_person(self):
        res_user = self.env['res.users'].browse(self._uid)
        if res_user.has_group('sales_team.group_sale_salesman'):
            return True
        else:
            return False

    sp_unit_amt = fields.Float(string="SP Unit Price")
    price_change = fields.Boolean(string="Price Change", default=False, copy=False)
    check_price_unit_amount = fields.Boolean(default=False, compute='_readonly_sales_person', store=True, copy=False)
    price_change_check = fields.Boolean(string="check field", compute='get_user', copy=False)
    diff_price = fields.Boolean(string='Diff Price', default=False)

    @api.onchange('price_unit')
    def _onchnage_price(self):
        for rec in self:
            if rec.price_unit:
                if rec.price_unit != rec.product_id.list_price:
                    rec.diff_price = True
                else:
                    rec.diff_price = False

    @api.depends('product_id')
    def get_user(self):
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        partner_group = res_user.has_group('sales_team.group_sale_salesman') and not res_user.has_group(
            'sales_team.group_sale_manager') and not res_user.has_group(
            'sales_team.group_sale_manager')
        if partner_group:
            self.price_change_check = True
        else:
            self.price_change_check = False

    @api.onchange('sp_unit_amt')
    def _onchange_check_price_unit(self):
        for rec in self:
            if rec.sp_unit_amt != rec.price_unit:
                rec.price_change = True
                rec.order_id.write({'approval_status': 'waiting'})
            else:
                rec.price_change = False

    @api.onchange('price_unit')
    def sp_unit_price(self):
        for i in self:
            i.write({
                'sp_unit_amt': i.price_unit
            })

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        for line in self:
            # check if there is already invoiced amount. if so, the price shouldn't change as it might have been
            # manually edited
            if line.qty_invoiced > 0:
                continue
            if not line.product_uom or not line.product_id or not line.order_id.pricelist_id:
                line.price_unit = 0.0
            else:
                # if line.order_id.approval_status == False:
                if line.diff_price == False:
                    price = line.with_company(line.company_id)._get_display_price()
                    line.price_unit = line.product_id._get_tax_included_unit_price(
                        line.company_id,
                        line.order_id.currency_id,
                        line.order_id.date_order,
                        'sale',
                        fiscal_position=line.order_id.fiscal_position_id,
                        product_price_unit=price,
                        product_currency=line.currency_id
                    )
                else:
                    line.price_unit = line._origin.price_unit
