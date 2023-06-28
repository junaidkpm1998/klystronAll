# See LICENSE file for full copyright and licensing details.


from odoo import _, api, models
from odoo.exceptions import UserError
from datetime import date


class AccountMove(models.Model):
    _inherit = "account.move"

    def check_limit(self):
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
            confirm_sale_order = self.env['sale.order'].search(
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
                partner.credit_limit - partner_credit_limit, 2)
            if partner_credit_limit > partner.credit_limit and \
                    partner.credit_limit > 0.0:
                if not partner.over_credit:
                    msg = 'Your available credit limit' \
                          ' Amount = %s \nCheck "%s" Accounts or Credit ' \
                          'Limits.' % (available_credit_limit,
                                       self.partner_id.name)
                    raise UserError(_('You can not confirm this '
                                      'invoice. \n' + msg))
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
            confirm_sale_order = self.env['sale.order'].search(
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

    # def _build_credit_warning_message(self, record, updated_credit):
    #     print("PARTNERRRR", record.partner_id.id)
    #     sale = self.env['sale.order'].search(
    #         [('partner_id', '=', record.partner_id.id), ('state', 'in', ['sale', 'done'])])
    #     print("AAAAAA",sale)
    #     if len(sale) > 0:
    #         return super(AccountMove, self)._build_credit_warning_message(record, updated_credit)

    # def check_pdc(self):
    #     pdc_entries = self.env['pdc.wizard'].search([('partner_id','=',self.partner_id.id),('state','in',['bounced','returned'])])
    #     if len(pdc_entries) > 0:
    #         raise UserError(_('You can not confirm Sale '
    #                                   'Order.PDC Payment %s is bounced or returned \n')%(pdc_entries[0].name))

    # def invoice_due(self):
    #     invoice=self.env['account.move'].search([('partner_id','=',self.partner_id.id),('move_type', '=', 'out_invoice'),('invoice_date_due','<',date.today())])
    #     for inv in invoice:
    #         if inv.payment_state == 'not_paid':
    #             raise UserError(_('There are unpaid Invoices for the Customer.'))

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for order in self:
            msg = order.check_warning()
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
            # order.invoice_due()

        return res

    # @api.constrains('amount_total')
    # def check_amount(self):
    #     for order in self:
    #         order.check_limit()

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        if res.partner_id.credit_limit > 0.0 and \
                not res.partner_id.over_credit:
            res.check_limit()
        return res
