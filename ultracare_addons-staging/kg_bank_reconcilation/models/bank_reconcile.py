# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
from odoo.exceptions import ValidationError, UserError
from odoo.tools import date_utils, io, xlsxwriter
from dateutil.relativedelta import relativedelta


class BankReconcilation(models.Model):
    _name = 'kg.bank.reconcilation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Bank Reconcilation Form'

    @api.depends('journal_id', 'date_from', 'date_to')
    def _get_lines(self):
        self.account_id = self.journal_id.default_account_id.id
        self.currency_id = self.journal_id.currency_id or self.journal_id.company_id.currency_id or self.env.user.company_id.currency_id
        domain = [('account_id', '=', self.account_id.id), ('statement_date', '=', False),
                  ('parent_state', '=', 'posted')]
        if self.date_to:
            domain += [('date', '<=', self.date_to)]
        if self.date_from:
            start = self.date_from - relativedelta(months=1)
            if start:
                domain += [('date', '>=', start)]
        s_lines = []
        lines = self.env['account.move.line'].sudo().search(domain)
        # self.statement_lines.with_context(force_delete=True).unlink()
        # self.statement_lines.write({'bank_statement_id': False})
        self.statement_lines = False
        self.statement_lines = lines
        for line in self.statement_lines:
            line.bank_statement_id = self.id

    @api.depends('statement_lines.statement_date', 'statement_lines', 'closing_balance', 'move_lines',
                 'statement_lines_open')
    def _compute_final_amount(self):
        self.unbalance_credit_final += sum([line.debit for line in self.statement_lines_open])
        self.unbalance_debit_final += sum([line.credit for line in self.statement_lines_open])

    @api.depends('statement_lines.statement_date', 'statement_lines', 'closing_balance', 'move_lines')
    def _compute_amount(self):
        gl_balance = 0
        bank_balance = 0
        debits = 0
        credits = 0
        current_update = 0
        domain = [('account_id', '=', self.account_id.id)]
        lines = self.env['account.move.line'].search(domain)
        domain += [('date', '>=', self.date_from), ('date', '<=', self.date_to), ('parent_state', '=', 'posted')]
        lines = self.env['account.move.line'].search(domain)
        bank_lines = self.env['account.move.line'].search(
            [('account_id', '=', self.account_id.id), ('statement_date', '<', self.date_from),
             ('parent_state', '=', 'posted')])
        gl_lines = self.env['account.move.line'].search(
            [('account_id', '=', self.account_id.id), ('date', '<=', self.date_to), ('date', '>=', self.date_from),
             ('parent_state', '=', 'posted')])
        gl_balance = sum([line.debit - line.credit for line in gl_lines])
        domain += [('id', 'not in', self.statement_lines.ids), ('statement_date', '!=', False),
                   ('parent_state', '=', 'posted')]
        bank_balance = sum([line.balance if line.statement_date else 0 for line in bank_lines])
        bal_credits = sum([line.debit if line.statement_date else 0 for line in self.statement_lines])
        credits = sum([line.debit if not line.statement_date else 0 for line in self.statement_lines])
        bal_debits = sum([line.credit if line.statement_date else 0 for line in self.statement_lines])
        debits = sum([line.credit if not line.statement_date else 0 for line in self.statement_lines])
        current_update += sum([line.debit - line.credit if line.statement_date else 0 for line in bank_lines])

        self.gl_balance = gl_balance
        self.balance_difference = gl_balance - current_update
        self.unbalance_credit = credits
        self.unbalance_debit = debits
        self.bank_balance = bank_balance + bal_credits - bal_debits
        self.statement_difference = self.closing_balance - self.bank_balance

    name = fields.Many2one('account.journal', related="journal_id", invisible=True)
    journal_id = fields.Many2one('account.journal', 'Bank', domain=[('type', '=', 'bank')])
    account_id = fields.Many2one('account.account', 'Bank Account')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    move_lines = fields.One2many('account.move', 'bank_statement_id')
    statement_lines = fields.One2many('account.move.line', 'bank_statement_id', compute="_get_lines", store=True)
    statement_lines_open = fields.One2many('account.move.line', 'bk_reconcile_id')
    closing_balance = fields.Monetary('Closing Balance')
    unbalance_credit = fields.Monetary('Unbalanced Credit', readonly=True, compute='_compute_amount')
    unbalance_debit = fields.Monetary('Unbalanced Debit', readonly=True, compute='_compute_amount')
    gl_balance = fields.Monetary('Balance as per Company Books', readonly=True, compute='_compute_amount')
    bank_balance = fields.Monetary('Balance as per Bank', readonly=True, compute='_compute_amount')
    balance_difference = fields.Monetary('Amounts not Reflected in Bank', readonly=True, compute='_compute_amount')
    statement_difference = fields.Monetary('Difference', readonly=True, compute='_compute_amount')
    statement_difference_final = fields.Monetary('Difference', readonly=True, compute='_compute_amount')
    current_update = fields.Monetary('Balance of entries updated now')
    currency_id = fields.Many2one('res.currency', string='Currency')
    unbalance_credit_final = fields.Monetary('Unbalanced Credit', readonly=True, compute='_compute_final_amount')
    unbalance_debit_final = fields.Monetary('Unbalanced Debit', readonly=True, compute='_compute_final_amount')
    state = fields.Selection([('draft', 'Unreconcile'), ('done', 'Reconciled'), ('cancel', 'Cancel')], default='draft',
                             track_visibility='onchange', )
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get('bank.statement'))

    @api.constrains('date_from', 'date_to')
    def _constrains_date(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                if rec.date_from > rec.date_to:
                    raise ValidationError(_('Start Date must be less than End Date'))

    def action_approve(self):
        for li in self.statement_lines:
            if not li.statement_date:
                li.bk_reconcile_id = self.id
                li.bank_statement_id = False
        self.state = 'done'

    def action_draft(self):
        self.unbalance_credit_final = 0
        self.unbalance_debit_final = 0
        for li in self.statement_lines_open:
            li.bk_reconcile_id = False
        self.state = 'draft'

    def action_cancel(self):
        self.state = 'cancel'

    def action_refresh(self):
        self.account_id = self.journal_id.default_account_id.id
        self.currency_id = self.journal_id.currency_id or self.journal_id.company_id.currency_id or self.env.user.company_id.currency_id
        domain = [('account_id', '=', self.account_id.id), ('statement_date', '=', False),
                  ('parent_state', '=', 'posted')]
        if self.date_to and self.date_from:
            domain += [('date', '<=', self.date_to), ('date', '>=', self.date_from)]
        s_lines = []
        lines = self.env['account.move.line'].search(domain)
        lines = lines.filtered(lambda x: x.id not in self.statement_lines.ids)
        self.statement_lines += lines

    def print_xlsx_report(self):
        data = {
            'ids': self.ids,
            'model': "kg.bank.reconcilation",
            'start_date': self.date_from,
            'end_date': self.date_to,
            'account_id': self.account_id.id,
            'company_id': self.company_id.id,

        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'kg.bank.reconcilation',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Bank Reconcilation Report',
                     },
            'report_type': 'xlsx'
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        statement_lines = []
        currency = self.env.user.company_id.currency_id.symbol or ''
        round_curr = self.env.user.company_id.currency_id.round

        company = data['company_id']
        date_start = data['start_date']
        date_end = data['end_date']
        account_id = data['account_id']
        account = self.env['account.account'].browse(account_id)
        statement = self.env['kg.bank.reconcilation'].browse(data['ids'][0])
        format1 = workbook.add_format({'font_size': 16, 'align': 'vcenter', 'bg_color': '#D3D3D3', 'bold': True})
        format1.set_font_color('#000080')
        format2 = workbook.add_format({'font_size': 12})
        format3 = workbook.add_format({'font_size': 12, 'bold': True, 'align': 'vcenter'})
        format4 = workbook.add_format({'font_size': 10})
        format41 = workbook.add_format({'num_format': 'dd-mm-yyyy'})
        currency_format = workbook.add_format({'num_format': '0.000', 'bold': True, })
        format5 = workbook.add_format({'font_size': 12, 'bold': True, 'bg_color': '#D3D3D3', 'align': 'vcenter'})
        format1.set_align('center')
        format2.set_align('left')
        format3.set_align('left')
        format4.set_align('center')
        prod_row = 0
        prod_col = 0
        if statement and statement.statement_lines:
            rc_dr_total = 0
            rc_cr_total = 0
            un_dr_total = 0
            un_cr_total = 0
            sheet.merge_range(prod_row, prod_col, prod_row, prod_col + 1, 'Report Name :', format3)
            sheet.merge_range(prod_row, prod_col + 3, prod_row, prod_col + 2, "Bank Reconcilation", format2)
            prod_row += 1
            sheet.merge_range(prod_row, prod_col, prod_row, prod_col + 1, 'Ledger :', format3)
            sheet.merge_range(prod_row, prod_col + 3, prod_row, prod_col + 2, account.display_name, format2)
            prod_row += 1
            sheet.merge_range(prod_row, prod_col, prod_row, prod_col + 1, 'Statement Period:', format3)
            sheet.merge_range(prod_row, prod_col + 3, prod_row, prod_col + 2, date_start + "  " + date_end, format2)
            prod_row += 1
            sheet.merge_range(prod_row, prod_col, prod_row, prod_col + 1, 'Closing Balance:', format3)
            sheet.merge_range(prod_row, prod_col + 3, prod_row, prod_col + 2, statement.closing_balance,
                              currency_format)
            prod_row += 1
            sheet.merge_range(prod_row, prod_col, prod_row, prod_col + 1, 'Balance as per Book:', format3)
            sheet.merge_range(prod_row, prod_col + 3, prod_row, prod_col + 2, statement.gl_balance, currency_format)
            prod_row += 1
            sheet.merge_range(prod_row, prod_col, prod_row, prod_col + 1, 'Unbalanced Credit', format3)
            sheet.merge_range(prod_row, prod_col + 3, prod_row, prod_col + 2, statement.unbalance_credit,
                              currency_format)
            prod_row += 1
            sheet.merge_range(prod_row, prod_col, prod_row, prod_col + 1, 'Unbalanced Debit', format3)
            sheet.merge_range(prod_row, prod_col + 3, prod_row, prod_col + 2, statement.unbalance_debit,
                              currency_format)
            prod_row += 1
            sheet.merge_range(prod_row, prod_col, prod_row, prod_col + 1, 'Difference', format3)
            sheet.merge_range(prod_row, prod_col + 3, prod_row, prod_col + 2, statement.statement_difference,
                              currency_format)
            prod_row += 1
            sheet.merge_range(prod_row, prod_col, prod_row, prod_col + 3, "Reconciled Entries", format5)
            prod_row += 1
            sheet.write(prod_row, prod_col, 'Date', format5)
            sheet.write(prod_row, prod_col + 1, 'Ref', format5)
            sheet.write(prod_row, prod_col + 2, 'Debit', format5)
            sheet.write(prod_row, prod_col + 3, 'Credit', format5)
            sheet.write(prod_row, prod_col + 4, 'Reconciled', format5)
            prod_row = prod_row + 1
            for li in statement.statement_lines.filtered(lambda x: x.statement_date != False).sorted(
                    key=lambda x: x.date):
                sheet.write(prod_row, prod_col, li.date, format41)
                sheet.write(prod_row, prod_col + 1, li.name)
                sheet.write(prod_row, prod_col + 2, li.credit, currency_format)
                sheet.write(prod_row, prod_col + 3, li.debit, currency_format)
                sheet.write(prod_row, prod_col + 4, li.statement_date, currency_format)
                rc_dr_total = rc_dr_total + li.credit
                rc_cr_total = rc_cr_total + li.debit
                prod_row = prod_row + 1
            sheet.merge_range(prod_row, prod_col, prod_row, prod_col + 1, "Total", format5)
            sheet.write(prod_row, prod_col + 2, rc_dr_total, currency_format)
            sheet.write(prod_row, prod_col + 3, rc_cr_total, currency_format)
            prod_row = prod_row + 1
            sheet.merge_range(prod_row, prod_col, prod_row, prod_col + 3, "Unreconciled Entries", format5)
            prod_row = prod_row + 1
            for li in statement.statement_lines.filtered(lambda r: r.statement_date == False).sorted(
                    key=lambda r: r.date):
                sheet.write(prod_row, prod_col, li.date, format41)
                sheet.write(prod_row, prod_col + 1, li.name)
                sheet.write(prod_row, prod_col + 2, li.credit, currency_format)
                sheet.write(prod_row, prod_col + 3, li.debit, currency_format)
                sheet.write(prod_row, prod_col + 4, li.statement_date, currency_format)
                un_dr_total = un_dr_total + li.credit
                un_cr_total = un_cr_total + li.debit
                prod_row = prod_row + 1
        sheet.merge_range(prod_row, prod_col, prod_row, prod_col + 1, "Total", format5)
        sheet.write(prod_row, prod_col + 2, un_dr_total, currency_format)
        sheet.write(prod_row, prod_col + 3, un_cr_total, currency_format)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
