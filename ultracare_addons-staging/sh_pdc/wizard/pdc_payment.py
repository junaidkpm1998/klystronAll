# Copyright (C) Softhealer Technologies.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from datetime import timedelta


class Attachment(models.Model):
    _inherit = 'ir.attachment'

    pdc_id = fields.Many2one('pdc.wizard')


class PDC_wizard(models.Model):
    _name = "pdc.wizard"
    _description = "PDC Wizard"

    def open_attachments(self):
        [action] = self.env.ref('base.action_attachment').read()
        ids = self.env['ir.attachment'].search([('pdc_id', '=', self.id)])
        id_list = []
        for pdc_id in ids:
            id_list.append(pdc_id.id)
        action['domain'] = [('id', 'in', id_list)]
        return action

    def open_journal_items(self):
        [action] = self.env.ref('account.action_account_moves_all').read()
        ids = self.env['account.move.line'].search([('pdc_id', '=', self.id)])
        id_list = []
        for pdc_id in ids:
            id_list.append(pdc_id.id)
        action['domain'] = [('id', 'in', id_list)]
        return action

    def open_journal_entry(self):
        [action] = self.env.ref(
            'sh_pdc.sh_pdc_action_move_journal_line').read()
        ids = self.env['account.move'].search([('pdc_id', '=', self.id)])
        id_list = []
        for pdc_id in ids:
            id_list.append(pdc_id.id)
        action['domain'] = [('id', 'in', id_list)]
        return action

    @api.model
    def default_get(self, fields):
        rec = super(PDC_wizard, self).default_get(fields)
        active_ids = self._context.get('active_ids')
        active_model = self._context.get('active_model')

        # Check for selected invoices ids
        if not active_ids or active_model != 'account.move':
            return rec
        invoices = self.env['account.move'].browse(active_ids)
        if invoices:
            invoice = invoices[0]
            if invoice.move_type in ('out_invoice', 'out_refund'):
                rec.update({'payment_type': 'receive_money'})
            elif invoice.move_type in ('in_invoice', 'in_refund'):
                rec.update({'payment_type': 'send_money'})

            rec.update({'partner_id': invoice.partner_id.id,
                        'payment_amount': invoice.amount_residual,
                        'invoice_id': invoice.id,
                        'due_date': invoice.invoice_date_due,
                        'memo': invoice.name})

        return rec

    name = fields.Char("Name", default='New', readonly=1)
    # check_amount_in_words = fields.Char(string="Amount in Words",compute='_compute_check_amount_in_words')
    payment_type = fields.Selection([('receive_money', 'Receive Money'), (
        'send_money', 'Send Money')], string="Payment Type", default='receive_money')
    partner_id = fields.Many2one('res.partner', string="Partner")
    payment_amount = fields.Monetary("Payment Amount")
    currency_id = fields.Many2one(
        'res.currency', string="Currency", default=lambda self: self.env.company.currency_id)
    reference = fields.Char("Cheque Reference")
    journal_id = fields.Many2one('account.journal', string="Payment Journal", domain=[
        ('type', '=', 'bank')], required=1)
    cheque_status = fields.Selection([('draft', 'Draft'), ('deposit', 'Deposit'), ('paid', 'Paid')],
                                     string="Cheque Status", default='draft')
    payment_date = fields.Date(
        "Payment Date", default=fields.Date.today(), required=1)
    due_date = fields.Date("Due Date", required=1)
    cheque_date = fields.Date("Cheque Date", required=1)
    cheque_clearance_date = fields.Date(string="Cheque Cleared Date")
    memo = fields.Char("Memo")
    agent = fields.Char("Agent")
    bank_id = fields.Many2one('res.bank', string="Bank")
    attachment_ids = fields.Many2many('ir.attachment', string='Cheque Image')
    company_id = fields.Many2one('res.company', string='company', default=lambda self: self.env.company)
    invoice_id = fields.Many2one('account.move', string="Invoice/Bill")
    state = fields.Selection([('draft', 'Draft'), ('registered', 'Registered'), ('returned', 'Returned'),
                              ('deposited', 'Deposited'), ('bounced', 'Bounced'), ('done', 'Done'),
                              ('cancel', 'Cancelled')], string="State", default='draft')

    deposited_debit = fields.Many2one('account.move.line')
    deposited_credit = fields.Many2one('account.move.line')
    type = fields.Selection([('pdc', 'PDC'), ('cdc', 'CDC')], default='pdc', string='Type')

    kg_invoice_ids = fields.Many2many('account.move', 'account_move_rel', string='Select invoices')
    partner_invoice_id = fields.Many2many('account.move', 'account_move_rel_1', string='Partner Invoice')

    pdc_line_aml_ids = fields.One2many('kg.pdc.move.line', 'kg_pdc_id', string="Invoice Lines Details")
    balance_amt = fields.Float(string="Balance_Amount")
    is_balance = fields.Boolean('Is Balance Available', compute='compute_balance_amount', default=False, store=True)

    @api.depends('pdc_line_aml_ids')
    def compute_balance_amount(self):
        for i in self:
            if i.pdc_line_aml_ids:
                amt = sum(i.pdc_line_aml_ids.mapped('amount_residual'))
                if amt > 0:
                    i.is_balance = True
                    i.balance_amt = amt
                else:
                    i.is_balance = False
                    i.balance_amt = 0

            # Register pdc payment

    def button_register(self):
        if self:
            if self.cheque_status == 'draft':
                self.write({'state': 'draft'})

            if self.cheque_status == 'deposit':
                self.action_register()
                self.action_deposited()
                self.write({'state': 'deposited'})

            if self.cheque_status == 'paid':
                self.action_register()
                self.action_deposited()
                self.action_done()
                self.write({'state': 'done'})

    def action_register(self):
        self.check_payment_amount()
        rec_amt = 0
        inv_amt = 0
        for rec in self:
            if rec.kg_invoice_ids:
                rec_amt += rec.payment_amount
                for i in rec.kg_invoice_ids:
                    inv_amt += i._origin.amount_residual_signed
                if rec_amt > inv_amt:
                    raise UserError(_('Payment Amount must be less than Due Amount'))
                else:
                    rec.write({'state': 'registered'})
            else:
                rec.write({'state': 'registered'})

    def check_payment_amount(self):
        if self.payment_amount <= 0.0:
            raise UserError("Amount must be greater than zero!")

    @api.constrains('payment_amount')
    def check_allocated_amount(self):
        if self.payment_amount and self.kg_invoice_ids:
            if not self.payment_amount == sum(self.pdc_line_aml_ids.mapped('allocated_amount')):
                raise UserError('The amount should be matching in lines and payment amount')

    def check_pdc_account(self):
        if self.type == 'pdc':
            if self.payment_type == 'receive_money':
                if not self.env.company.pdc_customer:
                    raise UserError(
                        "Please Set PDC payment account for Customer !")
                else:
                    return self.env.company.pdc_customer.id

            else:
                if not self.env.company.pdc_vendor:
                    raise UserError(
                        "Please Set PDC payment account for Supplier !")
                else:
                    return self.env.company.pdc_vendor.id
        if self.type == 'cdc':
            if self.payment_type == 'receive_money':
                if not self.env.company.cdc_customer:
                    raise UserError(
                        "Please Set CDC payment account for Customer !")
                else:
                    return self.env.company.cdc_customer.id

            else:
                if not self.env.company.cdc_vendor:
                    raise UserError(
                        "Please Set CDC payment account for Supplier !")
                else:
                    return self.env.company.cdc_vendor.id

    def get_partner_account(self):
        if self.payment_type == 'receive_money':
            return self.partner_id.property_account_receivable_id.id
        else:
            return self.partner_id.property_account_payable_id.id

    def action_returned(self):
        self.check_payment_amount()
        self.write({'state': 'returned'})

    def get_credit_move_line(self, account):
        return {
            'pdc_id': self.id,
            #             'partner_id': self.partner_id.id,
            'account_id': account,
            'credit': self.payment_amount,
            'ref': self.memo,
            'date': self.payment_date,
            'date_maturity': self.due_date,
        }

    def get_debit_move_line(self, account):
        return {
            'pdc_id': self.id,
            #             'partner_id': self.partner_id.id,
            'account_id': account,
            'debit': self.payment_amount,
            'ref': self.memo,
            'date': self.payment_date,
            'date_maturity': self.due_date,
        }

    def get_move_vals(self, debit_line, credit_line):
        return {
            'pdc_id': self.id,
            'date': self.payment_date,
            'journal_id': self.journal_id.id,
            #             'partner_id': self.partner_id.id,
            'ref': self.memo,
            'line_ids': [(0, 0, debit_line),
                         (0, 0, credit_line)]
        }

    def action_deposited(self):
        move = self.env['account.move']

        self.check_payment_amount()  # amount must be positive
        pdc_account = self.check_pdc_account()
        partner_account = self.get_partner_account()

        # Create Journal Item
        move_line_vals_debit = {}
        move_line_vals_credit = {}
        if self.payment_type == 'receive_money':
            move_line_vals_debit = self.get_debit_move_line(pdc_account)
            move_line_vals_credit = self.get_credit_move_line(partner_account)
        else:
            move_line_vals_debit = self.get_debit_move_line(partner_account)
            move_line_vals_credit = self.get_credit_move_line(pdc_account)

        # create move and post it
        move_vals = self.get_move_vals(
            move_line_vals_debit, move_line_vals_credit)
        move_id = move.create(move_vals)
        move_id.action_post()

        self.write({'state': 'deposited', 'deposited_debit': move_id.line_ids.filtered(lambda x: x.debit > 0),
                    'deposited_credit': move_id.line_ids.filtered(lambda x: x.credit > 0)})

    def action_bounced(self):
        move = self.env['account.move']

        self.check_payment_amount()  # amount must be positive
        pdc_account = self.check_pdc_account()
        partner_account = self.get_partner_account()

        # Create Journal Item
        move_line_vals_debit = {}
        move_line_vals_credit = {}

        if self.payment_type == 'receive_money':
            move_line_vals_debit = self.get_debit_move_line(partner_account)
            move_line_vals_credit = self.get_credit_move_line(pdc_account)
        else:
            move_line_vals_debit = self.get_debit_move_line(pdc_account)
            move_line_vals_credit = self.get_credit_move_line(partner_account)

        if self.memo:
            move_line_vals_debit.update({'name': 'PDC Payment :' + self.memo})
            move_line_vals_credit.update({'name': 'PDC Payment :' + self.memo})
        else:
            move_line_vals_debit.update({'name': 'PDC Payment'})
            move_line_vals_credit.update({'name': 'PDC Payment'})
        # create move and post it
        move_vals = self.get_move_vals(
            move_line_vals_debit, move_line_vals_credit)
        move_id = move.create(move_vals)
        move_id.action_post()

        self.write({'state': 'bounced'})

    def get_matching_dict(self, debit_move_dict, credit_move_dict):
        matching_list = []
        debit_dict = {}
        credit_dict = {}
        payment_type = self.payment_type
        if payment_type == 'receive_money':
            debit_dict = debit_move_dict
            credit_dict = credit_move_dict
        elif payment_type == 'send_money':
            debit_dict = credit_move_dict
            credit_dict = debit_move_dict
        print(type(payment_type), "Typeeesssss")
        print(credit_dict, "Typeeesssss")
        if payment_type == 'receive_money':
            for cred_move_id, credamt, in credit_dict.items():
                print(credamt, "Cre")
                if credamt > 0.0:
                    for deb_move_id, debamt in debit_dict.items():

                        is_full_reconcile = debit_dict['is_full_reconcile']
                        print(is_full_reconcile, "LLLL")
                        print(debamt, "DEB AMTTT")
                        print(credamt, "CRED AMTTT")
                        balance = credamt - debamt
                        print(balance, "Balanceeee")
                        if credamt <= 0.0:
                            continue
                        if debamt == 0.0:
                            continue
                        if balance > 0.0:
                            ful_rec = self.env['account.full.reconcile']
                            if is_full_reconcile == True:
                                vals = {}
                                ful_rec = self.env['account.full.reconcile'].create(vals)
                            if deb_move_id != 'is_full_reconcile':
                                matching_list.append(
                                    {'credit_move_id': cred_move_id, 'full_reconcile_id': ful_rec.id,
                                     'debit_amount_currency': debamt, 'credit_amount_currency': debamt,
                                     'debit_move_id': deb_move_id, 'amount': debamt})
                            debit_dict[deb_move_id] = 0.0

                        if balance < 0.0:
                            ful_rec = self.env['account.full.reconcile']
                            if is_full_reconcile == True:
                                vals = {}
                                ful_rec = self.env['account.full.reconcile'].create(vals)
                            if deb_move_id != 'is_full_reconcile':
                                matching_list.append(
                                    {'credit_move_id': cred_move_id, 'full_reconcile_id': ful_rec.id,
                                     'debit_amount_currency': credamt, 'credit_amount_currency': credamt,
                                     'debit_move_id': deb_move_id, 'amount': credamt})
                            debit_dict[deb_move_id] = abs(balance)
                            credit_dict[cred_move_id] = 0.0

                        if balance == 0.0:
                            ful_rec = self.env['account.full.reconcile']
                            if is_full_reconcile == True:
                                vals = {}
                                ful_rec = self.env['account.full.reconcile'].create(vals)
                            if deb_move_id != 'is_full_reconcile':
                                matching_list.append(
                                    {'credit_move_id': cred_move_id, 'full_reconcile_id': ful_rec.id,
                                     'debit_move_id': deb_move_id, 'debit_amount_currency': debamt,
                                     'credit_amount_currency': debamt, 'amount': debamt})
                            debit_dict[deb_move_id] = 0.0
                            credit_dict[cred_move_id] = 0.0
                            credamt = 0.0
                        credamt = balance
        return matching_list

    def action_done(self):
        move = self.env['account.move']

        self.check_payment_amount()  # amount must be positive
        pdc_account = self.check_pdc_account()
        #         bank_account = self.journal_id.payment_debit_account_id.id or self.journal_id.payment_credit_account_id.id
        bank_account = self.journal_id._get_journal_inbound_outstanding_payment_accounts()
        bank_account = bank_account[0].id if bank_account else False

        # Create Journal Item
        move_line_vals_debit = {}
        move_line_vals_credit = {}
        if self.payment_type == 'receive_money':
            move_line_vals_debit = self.get_debit_move_line(bank_account)
            move_line_vals_credit = self.get_credit_move_line(pdc_account)
        else:
            move_line_vals_debit = self.get_debit_move_line(pdc_account)
            move_line_vals_credit = self.get_credit_move_line(bank_account)

        if self.memo:
            move_line_vals_debit.update({'name': 'PDC Payment :' + self.memo, 'partner_id': self.partner_id.id})
            move_line_vals_credit.update({'name': 'PDC Payment :' + self.memo, 'partner_id': self.partner_id.id})
        else:
            move_line_vals_debit.update({'name': 'PDC Payment', 'partner_id': self.partner_id.id})
            move_line_vals_credit.update({'name': 'PDC Payment', 'partner_id': self.partner_id.id})

        # create move and post it
        move_vals = self.get_move_vals(
            move_line_vals_debit, move_line_vals_credit)
        if self.cheque_clearance_date:
            move_vals.update({'date': self.cheque_clearance_date})
            print(move_vals, "VALSSS")
        move_id = move.create(move_vals)
        move_id.action_post()
        print(move_id, "MOVEEE")
        invoice = self.env['account.move'].sudo().search([('name', '=', move_id.name)])
        if invoice:
            print('INV')
            if self.payment_type == 'receive_money':
                # reconcilation Entry for Invoice
                debit_move_id = self.env['account.move.line'].sudo().search([('move_id', '=', invoice.id),
                                                                             ('debit', '>', 0.0)], limit=1)

                credit_move_id = self.env['account.move.line'].sudo().search([('move_id', '=', move_id.id),
                                                                              ('credit', '>', 0.0)], limit=1)

                if debit_move_id and credit_move_id:
                    full_reconcile_id = self.env['account.full.reconcile'].sudo().create({})
                    amount = 0.0
                    if move_line_vals_debit['debit'] > 0.0:
                        amount = move_line_vals_debit['debit']
                    else:
                        amount = move_line_vals_debit['credit']
                    # if invoice.move_type == 'out_invoice':
                    #     if invoice.line_ids.filtered(lambda l: l.credit == 0):
                    #         val_2 = invoice.line_ids.filtered(lambda l: l.credit == 0)[0].id
                    # elif invoice.move_type == 'in_invoice':
                    #     if invoice.line_ids.filtered(lambda l: l.debit == 0):
                    #         val_2 = invoice.line_ids.filtered(lambda l: l.debit == 0)[0].id

                    debit_move_dict = {}
                    credit_move_dict = {}
                    for line in self.pdc_line_aml_ids:
                        # debit_move_dict[line.move_line_id.id] = line.inv_allocate_amount
                        val_2 = line.inv_line_id.id
                        print(val_2, "va;lll")

                        if line.inv_line_id.move_id.move_type == 'out_invoice':
                            if line.inv_line_id.move_id.line_ids.filtered(lambda l: l.credit == 0):
                                val_2 = line.inv_line_id.move_id.line_ids.filtered(lambda l: l.credit == 0)[0].id
                        elif line.inv_line_id.move_id.move_type == 'in_invoice':
                            if line.inv_line_id.move_id.line_ids.filtered(lambda l: l.debit == 0):
                                val_2 = line.inv_line_id.move_id.line_ids.filtered(lambda l: l.debit == 0)[0].id
                        print(val_2, "??????????")
                        debit_move_dict[val_2] = line.allocated_amount
                        print(debit_move_dict, "ssssssssss")
                        # if line.debit == 0:
                        #     val_1 = line.id
                        ##            May be Wrong               ##
                        credit_move_dict[line.inv_line_id.id] = self.balance_amt
                    for line in self.pdc_line_aml_ids:
                        if self.payment_type == "receive_money":
                            if line.amount_residual == line.allocated_amount:
                                debit_move_dict['is_full_reconcile'] = True
                            else:
                                debit_move_dict['is_full_reconcile'] = False
                        else:
                            if line.amount_residual == line.allocated_amount:
                                credit_move_dict['is_full_reconcile'] = True
                            else:
                                credit_move_dict['is_full_reconcile'] = False

                    print(debit_move_dict, "debittt")
                    print(credit_move_dict, "credittt")
                    matching_list = self.get_matching_dict(debit_move_dict, credit_move_dict)
                    print(matching_list, "MATTT")
                    for rec_val in matching_list:
                        rec = self.env['account.partial.reconcile'].create(rec_val)
                        print(rec, "REcCCCC")
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.model
    def create(self, vals):
        if vals.get('payment_type') == 'receive_money':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'pdc.payment.customer')
        elif vals.get('payment_type') == 'send_money':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'pdc.payment.vendor')

        return super(PDC_wizard, self).create(vals)

    # ==============================
    #    CRON SCHEDULER CUSTOMER
    # ==============================
    @api.model
    def notify_customer_due_date(self):
        emails = []
        if self.env.company.is_cust_due_notify:
            notify_day_1 = self.env.company.notify_on_1
            notify_day_2 = self.env.company.notify_on_2
            notify_day_3 = self.env.company.notify_on_3
            notify_day_4 = self.env.company.notify_on_4
            notify_day_5 = self.env.company.notify_on_5
            notify_date_1 = False
            notify_date_2 = False
            notify_date_3 = False
            notify_date_4 = False
            notify_date_5 = False
            if notify_day_1:
                notify_date_1 = fields.date.today() + timedelta(days=int(notify_day_1) * -1)
            if notify_day_2:
                notify_date_2 = fields.date.today() + timedelta(days=int(notify_day_2) * -1)
            if notify_day_3:
                notify_date_3 = fields.date.today() + timedelta(days=int(notify_day_3) * -1)
            if notify_day_4:
                notify_date_4 = fields.date.today() + timedelta(days=int(notify_day_4) * -1)
            if notify_day_5:
                notify_date_5 = fields.date.today() + timedelta(days=int(notify_day_5) * -1)

            records = self.search([('payment_type', '=', 'receive_money')])
            for user in self.env.company.sh_user_ids:
                if user.partner_id and user.partner_id.email:
                    emails.append(user.partner_id.email)
            email_values = {
                'email_to': ','.join(emails),
            }
            view = self.env.ref("sh_pdc.sh_pdc_payment_form_view", raise_if_not_found=False).sudo()
            view_id = view.id if view else 0
            for record in records:
                if (record.due_date == notify_date_1
                        or record.due_date == notify_date_2
                        or record.due_date == notify_date_3
                        or record.due_date == notify_date_4
                        or record.due_date == notify_date_5):

                    if self.env.company.is_notify_to_customer:
                        # template_download_id = record.env['ir.model.data'].get_object(
                        #     'sh_pdc', 'sh_pdc_company_to_customer_notification_1'
                        #     )
                        template_download_id = self.env.ref('sh_pdc.sh_pdc_company_to_customer_notification_1')
                        _ = record.env['mail.template'].browse(
                            template_download_id.id
                        ).send_mail(record.id, notif_layout='mail.mail_notification_light', force_send=True)
                    if self.env.company.is_notify_to_user and self.env.company.sh_user_ids:
                        url = ''
                        base_url = request.env['ir.config_parameter'].sudo(
                        ).get_param('web.base.url')
                        url = base_url + "/web#id=" + \
                              str(record.id) + \
                              "&&model=pdc.wizard&view_type=form&view_id=" + str(view_id)
                        ctx = {
                            "customer_url": url,
                        }
                        # template_download_id = record.env['ir.model.data'].get_object(
                        #     'sh_pdc', 'sh_pdc_company_to_int_user_notification_1'
                        #     )
                        template_download_id = self.env.ref('sh_pdc.sh_pdc_company_to_int_user_notification_1')
                        _ = request.env['mail.template'].sudo().browse(template_download_id.id).with_context(
                            ctx).send_mail(
                            record.id, email_values=email_values, notif_layout='mail.mail_notification_light',
                            force_send=True)

    # ==============================
    #    CRON SCHEDULER VENDOR
    # ==============================
    @api.model
    def notify_vendor_due_date(self):
        emails = []
        if self.env.company.is_vendor_due_notify:
            notify_day_1_ven = self.env.company.notify_on_1_vendor
            notify_day_2_ven = self.env.company.notify_on_2_vendor
            notify_day_3_ven = self.env.company.notify_on_3_vendor
            notify_day_4_ven = self.env.company.notify_on_4_vendor
            notify_day_5_ven = self.env.company.notify_on_5_vendor
            notify_date_1_ven = False
            notify_date_2_ven = False
            notify_date_3_ven = False
            notify_date_4_ven = False
            notify_date_5_ven = False
            if notify_day_1_ven:
                notify_date_1_ven = fields.date.today() + timedelta(days=int(notify_day_1_ven) * -1)
            if notify_day_2_ven:
                notify_date_2_ven = fields.date.today() + timedelta(days=int(notify_day_2_ven) * -1)
            if notify_day_3_ven:
                notify_date_3_ven = fields.date.today() + timedelta(days=int(notify_day_3_ven) * -1)
            if notify_day_4_ven:
                notify_date_4_ven = fields.date.today() + timedelta(days=int(notify_day_4_ven) * -1)
            if notify_day_5_ven:
                notify_date_5_ven = fields.date.today() + timedelta(days=int(notify_day_5_ven) * -1)

            records = self.search([('payment_type', '=', 'send_money')])
            for user in self.env.company.sh_user_ids_vendor:
                if user.partner_id and user.partner_id.email:
                    emails.append(user.partner_id.email)
            email_values = {
                'email_to': ','.join(emails),
            }
            view = self.env.ref("sh_pdc.sh_pdc_payment_form_view", raise_if_not_found=False)
            view_id = view.id if view else 0
            for record in records:
                if (record.due_date == notify_date_1_ven
                        or record.due_date == notify_date_2_ven
                        or record.due_date == notify_date_3_ven
                        or record.due_date == notify_date_4_ven
                        or record.due_date == notify_date_5_ven):

                    if self.env.company.is_notify_to_vendor:
                        # template_download_id = record.env['ir.model.data'].get_object(
                        #     'sh_pdc', 'sh_pdc_company_to_customer_notification_1'
                        #     )
                        template_download_id = self.env.ref('sh_pdc.sh_pdc_company_to_customer_notification_1')
                        _ = record.env['mail.template'].browse(
                            template_download_id.id
                        ).send_mail(record.id, notif_layout='mail.mail_notification_light', force_send=True)
                    if self.env.company.is_notify_to_user_vendor and self.env.company.sh_user_ids_vendor:
                        url = ''
                        base_url = request.env['ir.config_parameter'].sudo(
                        ).get_param('web.base.url')
                        url = base_url + "/web#id=" + \
                              str(record.id) + \
                              "&&model=pdc.wizard&view_type=form&view_id=" + str(view_id)
                        ctx = {
                            "customer_url": url,
                        }
                        # template_download_id = record.env['ir.model.data'].get_object(
                        #     'sh_pdc', 'sh_pdc_company_to_int_user_notification_1'
                        #     )
                        template_download_id = self.env.ref('sh_pdc.sh_pdc_company_to_int_user_notification_1')
                        _ = request.env['mail.template'].sudo().browse(template_download_id.id).with_context(
                            ctx).send_mail(
                            record.id, email_values=email_values, notif_layout='mail.mail_notification_light',
                            force_send=True)

    # Multi Action Starts for change the state of PDC check

    def action_state_register(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        if len(active_ids) > 0:
            active_models = self.env[active_model].browse(active_ids)
            states = active_models.mapped('state')

            if len(set(states)) == 1:
                if states[0] == 'draft':
                    for active_model in active_models:
                        active_model.action_register()
                else:
                    raise UserError(
                        "Only Draft state PDC check can switch to Register state!!")
            else:
                raise UserError(
                    "States must be same!!")

    def action_state_return(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        if len(active_ids) > 0:
            active_models = self.env[active_model].browse(active_ids)
            states = active_models.mapped('state')

            if len(set(states)) == 1:
                if states[0] == 'registered':
                    for active_model in active_models:
                        active_model.action_returned()
                else:
                    raise UserError(
                        "Only Register state PDC check can switch to return state!!")
            else:
                raise UserError(
                    "States must be same!!")

    def action_state_deposit(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        if len(active_ids) > 0:
            active_models = self.env[active_model].browse(active_ids)
            states = active_models.mapped('state')

            if len(set(states)) == 1:
                if states[0] in ['registered', 'returned', 'bounced']:
                    for active_model in active_models:
                        active_model.action_deposited()
                else:
                    raise UserError(
                        "Only Register,Return and Bounce state PDC check can switch to Deposit state!!")
            else:
                raise UserError(
                    "States must be same!!")

    def action_state_bounce(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        if len(active_ids) > 0:
            active_models = self.env[active_model].browse(active_ids)
            states = active_models.mapped('state')

            if len(set(states)) == 1:
                if states[0] == 'deposited':
                    for active_model in active_models:
                        active_model.action_bounced()
                else:
                    raise UserError(
                        "Only Deposit state PDC check can switch to Bounce state!!")
            else:
                raise UserError(
                    "States must be same!!")

    def action_state_done(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        if len(active_ids) > 0:
            active_models = self.env[active_model].browse(active_ids)
            states = active_models.mapped('state')

            if len(set(states)) == 1:
                if states[0] == 'deposited':
                    for active_model in active_models:
                        active_model.action_done()
                else:
                    raise UserError(
                        "Only Deposit state PDC check can switch to Done state!!")
            else:
                raise UserError(
                    "States must be same!!")

    def action_state_cancel(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        if len(active_ids) > 0:
            active_models = self.env[active_model].browse(active_ids)
            states = active_models.mapped('state')

            if len(set(states)) == 1:
                if states[0] in ['registered', 'returned', 'bounced']:
                    for active_model in active_models:
                        active_model.action_cancel()
                else:
                    raise UserError(
                        "Only Register,Return and Bounce state PDC check can switch to Cancel state!!")
            else:
                raise UserError(
                    "States must be same!!")

    @api.onchange('partner_id', 'payment_type')
    def _onchange_partner_invoices(self):
        list = []
        for rec in self:
            if rec.kg_invoice_ids:
                rec.kg_invoice_ids = False
            if rec.partner_id:
                if rec.payment_type == 'receive_money':
                    account_move_id = self.env['account.move'].search(
                        [('state', 'not in', ['draft', 'cancel']), ('payment_state', 'in', ['not_paid', 'partial']),
                         ('move_type', '=', 'out_invoice'), ('partner_id', '=', rec.partner_id.id)])
                    if not account_move_id:
                        raise UserError(_('There is no due amount for this customer'))
                    if account_move_id:
                        for i in account_move_id:
                            list.append(i.id)
                    rec.partner_invoice_id = list
                if rec.payment_type == 'send_money':
                    account_move_id = self.env['account.move'].search(
                        [('state', 'not in', ['draft', 'cancel']), ('payment_state', 'in', ['not_paid', 'partial']),
                         ('move_type', '=', 'in_invoice'), ('partner_id', '=', rec.partner_id.id)])
                    if not account_move_id:
                        raise UserError(_('There is no due amount for this customer'))
                    if account_move_id:
                        for i in account_move_id:
                            list.append(i.id)
                    rec.partner_invoice_id = list

    @api.onchange('kg_invoice_ids')
    def _onchange_move_del(self):
        data = []
        for rec in self:
            if rec.kg_invoice_ids:
                for i in rec.kg_invoice_ids:
                    val_2 = 0
                    if i._origin.move_type == 'out_invoice':
                        if i._origin.line_ids.filtered(lambda l: l.credit == 0):
                            val_2 = i._origin.line_ids.filtered(lambda l: l.credit == 0)[0].id
                            print(val_2, "VAAAA")
                    elif i._origin.move_type == 'in_invoice':
                        if i._origin.line_ids.filtered(lambda l: l.debit == 0):
                            val_2 = i._origin.line_ids.filtered(lambda l: l.debit == 0)[0].id

                    vals = {
                        'name': i.name,
                        'invoice_date': i.invoice_date,
                        'invoice_date_due': i.invoice_date_due,
                        'amount_total_signed': i.amount_total_signed,
                        'amount_residual': i._origin.amount_residual_signed,
                        'allocated_amount': i._origin.amount_residual_signed,
                        'invoice_line_id': i._origin.id,
                        'inv_line_id': val_2
                        # 'line_id' :
                    }
                    data.append((0, 0, vals))
        self.pdc_line_aml_ids = False
        self.write({'pdc_line_aml_ids': data})


class KGPDCMoveLineLine(models.Model):
    _name = 'kg.pdc.move.line'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string='Invoice Number')
    currency_id = fields.Many2one(
        'res.currency', string="Currency", default=lambda self: self.env.company.currency_id)
    invoice_date = fields.Date(string='Invoice Date')
    invoice_date_due = fields.Date(string='Due Date')
    amount_total_signed = fields.Monetary(string='Invoice Amount')
    amount_residual = fields.Monetary(string='Due Amount')
    kg_pdc_id = fields.Many2one('pdc.wizard')
    allocated_amount = fields.Float('Allocated Amount')
    invoice_line_id = fields.Many2one('account.move', "Invoice Id")
    inv_line_id = fields.Many2one('account.move.line', "Invoice Line Id")
