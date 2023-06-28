import time
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo.tools import date_utils


class StatementAccountReport(models.AbstractModel):
    _name = 'report.kg_ultracare_salesmanwise_report.salesman_statement_tem'
    _description = 'Salesperson-wise Statement Account Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        company_id = data['form'].get('company_id')

        date_end_report = data['form'].get('date_to', time.strftime('%Y-%m-%d'))
        date_end = datetime.strptime(date_end_report, '%Y-%m-%d').date()
        date_from = date_utils.start_of(date_end, 'year')
        account_type = data['form'].get('account_type')

        browsed_currency_id = data['form'].get('currency_id')
        currency_id = self.env['res.currency'].browse(browsed_currency_id[0])
        browsed_company = self.env['res.company'].browse(company_id[0])

        data = []
        if account_type == 'asset_receivable':

            user_id = self.env['res.users'].search([])
            for user in user_id:
                user_name = str(user.name).upper()
                user_code = str(user.sale_man_code).upper()
                sales_person_vals = {'type': 'users',
                                     'user_name': user_name,
                                     'user_code': user_code,
                                     'partners': []
                                     }
                account_move_lines = self.env['account.move.line'].search(
                    [('date', '>=', date_from), ('date', '<=', date_end),
                     ('move_id.state', '=', 'posted'),
                     ('account_id.account_type', '=', 'asset_receivable'),
                     ('move_id.invoice_user_id', '=', user.id),
                     ])
                partners = list(set((account_move_lines.mapped('partner_id'))))
                date_30 = date_from + timedelta(days=30)
                date_31 = date_30 + timedelta(days=1)
                date_60 = date_from + timedelta(days=60)
                date_61 = date_60 + timedelta(days=1)
                date_90 = date_from + timedelta(days=90)
                date_91 = date_90 + timedelta(days=1)

                for partner in partners:
                    total_60 = 0
                    total_90 = 0
                    total_above_90 = 0
                    if date_30 < date_end:
                        lines_30 = account_move_lines.filtered(lambda x: x.partner_id.id == partner.id and x.date >= date_from and x.date <= date_30)
                        total_30 = sum(lines_30.mapped('balance'))
                    else:
                        lines_30 = account_move_lines.filtered(lambda x: x.partner_id.id == partner.id and x.date >= date_from and x.date <= date_end)
                        total_30 = sum(lines_30.mapped('balance'))

                    if date_31 < date_end and date_60 < date_end:
                        lines_60 = account_move_lines.filtered(lambda x: x.partner_id.id == partner.id and x.date >= date_31 and x.date <= date_60)
                        total_60 = sum(lines_60.mapped('balance'))
                    elif date_31 < date_end:
                        lines_60 = account_move_lines.filtered(lambda x: x.partner_id.id == partner.id and x.date >= date_31 and x.date <= date_end)
                        total_60 = sum(lines_60.mapped('balance'))

                    if date_61 < date_end and date_90 < date_end:
                        lines_90 = account_move_lines.filtered(lambda x: x.partner_id.id == partner.id and x.date >= date_61 and x.date <= date_90)
                        total_90 = sum(lines_90.mapped('balance'))
                    elif date_31 < date_end:
                        lines_90 = account_move_lines.filtered(lambda x: x.partner_id.id == partner.id and x.date >= date_61 and x.date <= date_end)
                        total_90 = sum(lines_90.mapped('balance'))

                    if date_91 < date_end:
                        lines_above_90 = account_move_lines.filtered(lambda x: x.partner_id.id == partner.id and x.date >= date_91 and x.date <= date_end)
                        total_above_90 = sum(lines_above_90.mapped('balance'))

                    ageing_total = total_30 + total_60 + total_90 + total_above_90
                    aging_lines = []
                    aging_val = {
                        'total_30': total_30,
                        'total_60': total_60,
                        'total_90': total_90,
                        'total_above_90': total_above_90,
                        'ageing_total': ageing_total,
                    }
                    aging_lines.append(aging_val)

                    partner_vals = {'name': partner.name,
                                    'code': partner.customer_code,
                                    'country_name': partner.country_id.name,
                                    'country_code': partner.country_code,
                                    'tel': partner.phone,
                                    'aging_lines': aging_lines,
                                    'lines': []}
                    filt = account_move_lines.filtered(lambda x: x.partner_id.id == partner.id)
                    for vals in filt:
                        partner_id = vals.partner_id.name
                        date = vals.date
                        doc_type = vals.journal_id.type
                        doc_no = vals.ref
                        due_date = vals.date_maturity
                        description = vals.move_name
                        if vals.debit:
                            invoice_amount = vals.debit
                        else:
                            invoice_amount = vals.credit
                        balance = vals.balance
                        pdc_amount = vals.move_id.total_pdc_payment
                        account_move_vals = {'type': 'data',
                                             'partner_id': partner_id,
                                             'date': date,
                                             'doc_no': doc_no,
                                             'doc_type': str(doc_type).upper(),
                                             'due_date': due_date,
                                             'description': description,
                                             'invoice_amount': invoice_amount,
                                             'balance': balance,
                                             'pdc_amount': pdc_amount,
                                             }
                        partner_vals['lines'].append(account_move_vals)

                    sales_person_vals['partners'].append(partner_vals)
                if sales_person_vals['partners']:
                    data.append(sales_person_vals)

        if account_type == 'liability_payable':
            user_id = self.env['res.users'].search([])
            for user in user_id:
                user_name = str(user.name).upper()
                user_code = str(user.sale_man_code).upper()
                sales_person_vals = {'type': 'users',
                                     'user_name': user_name,
                                     'user_code': user_code,
                                     'partners': []
                                     }
                account_move_lines = self.env['account.move.line'].search(
                    [('date', '>=', date_from), ('date', '<=', date_end),
                     ('move_id.state', '=', 'posted'),
                     ('account_id.account_type', '=', 'liability_payable'), ('move_id.invoice_user_id', '=', user.id),
                     ])
                partners = list(set((account_move_lines.mapped('partner_id'))))
                date_30 = date_from + timedelta(days=30)
                date_31 = date_30 + timedelta(days=1)
                date_60 = date_from + timedelta(days=60)
                date_61 = date_60 + timedelta(days=1)
                date_90 = date_from + timedelta(days=90)
                date_91 = date_90 + timedelta(days=1)

                for partner in partners:
                    total_60 = 0
                    total_90 = 0
                    total_above_90 = 0
                    if date_30 < date_end:
                        lines_30 = account_move_lines.filtered(
                            lambda x: x.partner_id.id == partner.id and x.date >= date_from and x.date <= date_30)
                        total_30 = sum(lines_30.mapped('balance'))
                    else:
                        lines_30 = account_move_lines.filtered(
                            lambda x: x.partner_id.id == partner.id and x.date >= date_from and x.date <= date_end)
                        total_30 = sum(lines_30.mapped('balance'))

                    if date_31 < date_end and date_60 < date_end:
                        lines_60 = account_move_lines.filtered(
                            lambda x: x.partner_id.id == partner.id and x.date >= date_31 and x.date <= date_60)
                        total_60 = sum(lines_60.mapped('balance'))
                    elif date_31 < date_end:
                        lines_60 = account_move_lines.filtered(
                            lambda x: x.partner_id.id == partner.id and x.date >= date_31 and x.date <= date_end)
                        total_60 = sum(lines_60.mapped('balance'))

                    if date_61 < date_end and date_90 < date_end:
                        lines_90 = account_move_lines.filtered(
                            lambda x: x.partner_id.id == partner.id and x.date >= date_61 and x.date <= date_90)
                        total_90 = sum(lines_90.mapped('balance'))
                    elif date_31 < date_end:
                        lines_90 = account_move_lines.filtered(
                            lambda x: x.partner_id.id == partner.id and x.date >= date_61 and x.date <= date_end)
                        total_90 = sum(lines_90.mapped('balance'))

                    if date_91 < date_end:
                        lines_above_90 = account_move_lines.filtered(
                            lambda x: x.partner_id.id == partner.id and x.date >= date_91 and x.date <= date_end)
                        total_above_90 = sum(lines_above_90.mapped('balance'))

                    ageing_total = total_30 + total_60 + total_90 + total_above_90
                    aging_lines = []
                    aging_val = {
                        'total_30': total_30,
                        'total_60': total_60,
                        'total_90': total_90,
                        'total_above_90': total_above_90,
                        'ageing_total': ageing_total,
                    }
                    aging_lines.append(aging_val)

                    partner_vals = {'name': partner.name,
                                    'code': partner.customer_code,
                                    'country_name': partner.country_id.name,
                                    'country_code': partner.country_code,
                                    'tel': partner.phone,
                                    'aging_lines': aging_lines,
                                    'lines': []}
                    filt = account_move_lines.filtered(lambda x: x.partner_id.id == partner.id)
                    for vals in filt:
                        partner_id = vals.partner_id.name
                        date = vals.date
                        doc_type = vals.journal_id.type
                        doc_no = vals.ref
                        due_date = vals.date_maturity
                        description = vals.move_name
                        if vals.debit:
                            invoice_amount = vals.debit
                        else:
                            invoice_amount = vals.credit
                        balance = vals.balance
                        pdc_amount = vals.move_id.total_pdc_payment
                        account_move_vals = {'type': 'data',
                                             'partner_id': partner_id,
                                             'date': date,
                                             'doc_no': doc_no,
                                             'doc_type': str(doc_type).upper(),
                                             'due_date': due_date,
                                             'description': description,
                                             'invoice_amount': invoice_amount,
                                             'balance': balance,
                                             'pdc_amount': pdc_amount,
                                             }
                        partner_vals['lines'].append(account_move_vals)

                    sales_person_vals['partners'].append(partner_vals)
                if sales_person_vals['partners']:
                    data.append(sales_person_vals)

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'datas': data,
            'currency_id': currency_id,
            'company_id': browsed_company.name,
            'company_city': browsed_company.city,
            'company_phone': browsed_company.phone,
            'company_mobile': browsed_company.mobile,
            'company_zip': browsed_company.zip,
            'company_vat': browsed_company.vat,
            'company_website': browsed_company.website,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
            'from_date': date_from,
            'to_date': date_end
        }
